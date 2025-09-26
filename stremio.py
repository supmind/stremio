from fastapi.responses import JSONResponse
from tmdb import get_meta as tmdb_get_meta, get_season_episodes, get_genres, discover_media, search_media, get_credits
from config import PLUGIN_ID, PLUGIN_NAME, PLUGIN_VERSION, PLUGIN_DESCRIPTION
import asyncio
from datetime import datetime, timezone
from urllib.parse import quote

# 缓存和常量
GENRE_CACHE = {}
SORT_OPTIONS = ["热门", "评分", "发行日期"]
YEARS = [str(year) for year in range(datetime.now().year, 1979, -1)]

def format_to_iso(date_str):
    if not date_str: return None
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        dt_utc = dt.replace(tzinfo=timezone.utc)
        return dt_utc.isoformat().replace('+00:00', 'Z')
    except (ValueError, TypeError):
        return None

async def get_manifest():
    if "movie_genres" not in GENRE_CACHE: GENRE_CACHE["movie_genres"] = get_genres("movie")
    if "series_genres" not in GENRE_CACHE: GENRE_CACHE["series_genres"] = get_genres("tv")

    movie_genres = [genre['name'] for genre in GENRE_CACHE["movie_genres"]]
    series_genres = [genre['name'] for genre in GENRE_CACHE["series_genres"]]

    # 为可发现目录（可过滤）添加 'skip'
    movie_extra_discover = [
        {"name": "排序", "options": ["热门", "评分", "发行日期"], "isRequired": False},
        {"name": "类型", "options": movie_genres, "isRequired": False},
        {"name": "年份", "options": YEARS, "isRequired": False},
        {"name": "skip"} # 添加 skip
    ]
    series_extra_discover = [
        {"name": "排序", "options": ["热门", "评分", "发行日期"], "isRequired": False},
        {"name": "类型", "options": series_genres, "isRequired": False},
        {"name": "年份", "options": YEARS, "isRequired": False},
        {"name": "skip"} # 添加 skip
    ]

    # 定义基础分页行为
    paginated_behavior = {"behaviorHints": {"paginated": True}}

    # 简化后的目录结构
    catalogs = [
        # 电影
        {"type": "movie", "id": "tmdb-popular", "name": "热门电影", **paginated_behavior, "extra": [{"name": "skip"}]},
        {"type": "movie", "id": "tmdb-top-rated", "name": "高分电影", **paginated_behavior, "extra": [{"name": "skip"}]},
        {"type": "movie", "id": "tmdb-discover-all", "name": "全部电影", **paginated_behavior, "extra": movie_extra_discover},
        # 剧集
        {"type": "series", "id": "tmdb-popular", "name": "热门剧集", **paginated_behavior, "extra": [{"name": "skip"}]},
        {"type": "series", "id": "tmdb-top-rated", "name": "高分剧集", **paginated_behavior, "extra": [{"name": "skip"}]},
        {"type": "series", "id": "tmdb-discover-all", "name": "全部剧集", **paginated_behavior, "extra": series_extra_discover}
    ]

    # 为搜索添加专门的目录
    search_catalogs = [
        {"type": "movie", "id": "tmdb-search", "name": "电影搜索", "extra": [{"name": "search", "isRequired": True}]},
        {"type": "series", "id": "tmdb-search", "name": "剧集搜索", "extra": [{"name": "search", "isRequired": True}]}
    ]
    catalogs.extend(search_catalogs)

    return {
        "id": PLUGIN_ID, "version": "1.1.0", "name": PLUGIN_NAME, "description": PLUGIN_DESCRIPTION,
        "resources": ["catalog", "meta", "search"], "types": ["movie", "series"], "idPrefixes": ["tmdb:"],
        "catalogs": catalogs
    }

def _to_stremio_meta_preview(item, media_type):
    # 搜索结果中的 media_type 可能与请求的 media_type 不同，需要从 item 中获取
    actual_media_type = item.get('media_type', media_type)

    release_date_key = 'release_date' if actual_media_type == 'movie' else 'first_air_date'
    release_date = item.get(release_date_key)
    year = release_date.split('-')[0] if release_date else None

    # 有些搜索结果可能没有 'name' 或 'title'，提供备用
    name = item.get('title') if actual_media_type == 'movie' else item.get('name')
    if not name:
        name = item.get('original_title') or item.get('original_name')

    # Map genre_ids to names
    genre_ids = item.get('genre_ids', [])
    genre_cache_key = f"{'series' if actual_media_type == 'tv' else 'movie'}_genres"
    genres = [genre['name'] for genre in GENRE_CACHE.get(genre_cache_key, []) if genre['id'] in genre_ids]

    return {
        "id": f"tmdb:{item.get('id')}",
        "type": media_type,
        "name": name,
        "poster": f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}" if item.get('poster_path') else None,
        "description": item.get('overview'),
        "releaseInfo": year,
        "imdbRating": item.get('vote_average'),
        "genres": genres
    }

def get_catalog(media_type, catalog_id, extra_args=None):
    tmdb_type = 'tv' if media_type == 'series' else 'movie'
    extra_args = extra_args or {}
    page = int(extra_args.get("skip", 0)) // 20 + 1

    # 处理搜索请求
    search_query = extra_args.get("search")
    if search_query:
        search_results = search_media(search_query, page)
        # Stremio 会为每种类型发送单独的搜索请求, 我们需要过滤结果
        items = [item for item in search_results if item.get('media_type') == tmdb_type]
        metas = [_to_stremio_meta_preview(item, media_type) for item in items]
        return JSONResponse(content={"metas": metas})

    # 处理普通的目录浏览请求
    # 确定排序方式
    sort_by = "popular" # 默认
    if "top-rated" in catalog_id:
        sort_by = "top_rated"
    elif "popular" in catalog_id:
        sort_by = "popular"

    # 对于 "全部" 目录，从 extra_args 获取排序
    if "all" in catalog_id:
        sort_by_map = {"热门": "popular", "评分": "top_rated", "发行日期": "release_date"}
        sort_by = sort_by_map.get(extra_args.get("排序"), "popular")

    genre_name = extra_args.get("类型")
    year = extra_args.get("年份")
    genre_id = None
    if genre_name:
        genre_list = GENRE_CACHE.get(f"{media_type}_genres", [])
        for genre in genre_list:
            if genre['name'] == genre_name:
                genre_id = genre['id']
                break

    items = discover_media(tmdb_type, genre_id, sort_by, year, page)
    metas = [_to_stremio_meta_preview(item, media_type) for item in items]
    return JSONResponse(content={"metas": metas})

def _to_stremio_videos(episodes, series_id):
    videos = []
    for episode in episodes:
        video_id = f"tmdb:{series_id}:{episode.get('season_number')}:{episode.get('episode_number')}"
        videos.append({
            "id": video_id, "title": episode.get('name'), "season": episode.get('season_number'),
            "episode": episode.get('episode_number'), "released": format_to_iso(episode.get('air_date')),
            "overview": episode.get('overview'),
            "thumbnail": f"https://image.tmdb.org/t/p/w500{episode.get('still_path')}" if episode.get('still_path') else None,
        })
    return videos

def _to_stremio_meta(request, item, credits, media_type):
    base_url = f"https://{request.url.netloc}"
    transport_url = f"{base_url}/manifest.json"

    genres = item.get('genres', [])
    genre_links = [
        {
            "name": genre['name'],
            "category": "Genres",
            "url": f"stremio:///discover/{quote(transport_url, safe='')}/{media_type}/tmdb-discover-all?类型={quote(genre['name'])}"
        } for genre in genres
    ]

    # Extract director and cast
    directors = []
    cast = []
    if credits:
        directors = [member['name'] for member in credits.get('crew', []) if member.get('job') == 'Director']
        # For TV shows, 'created_by' are often considered directors/creators
        if not directors and media_type == 'series':
            directors = [creator['name'] for creator in item.get('created_by', [])]
        cast = [member['name'] for member in credits.get('cast', [])[:10]] # Limit to top 10 actors

    # Correctly format releaseInfo and released
    release_info = ""
    released_date = None
    if media_type == 'movie':
        release_date_str = item.get('release_date')
        if release_date_str:
            release_info = release_date_str.split('-')[0]
        released_date = format_to_iso(release_date_str)
    elif media_type == 'series':
        start_date_str = item.get('first_air_date')
        start_year = start_date_str.split('-')[0] if start_date_str else ''
        released_date = format_to_iso(start_date_str)

        status = item.get('status')
        if status in ['Ended', 'Canceled']:
            end_date_str = item.get('last_air_date')
            end_year = end_date_str.split('-')[0] if end_date_str else ''
            if start_year and end_year and start_year != end_year:
                release_info = f"{start_year}-{end_year}"
            else:
                release_info = start_year
        else: # 'Returning Series', 'In Production', etc.
            release_info = f"{start_year}-" if start_year else ""

    meta = {
        "id": f"tmdb:{item.get('id')}",
        "type": media_type,
        "name": item.get('title') if media_type == 'movie' else item.get('name'),
        "poster": f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}" if item.get('poster_path') else None,
        "background": f"https://image.tmdb.org/t/p/original{item.get('backdrop_path')}" if item.get('backdrop_path') else None,
        "description": item.get('overview'),
        "releaseInfo": release_info,
        "released": released_date,
        "imdbRating": item.get('vote_average'),
        "director": directors,
        "cast": cast,
        "genres": [genre['name'] for genre in genres],
        "links": genre_links,
        "videos": [],  # Crucial: Add 'videos' array for all types
        "behaviorHints": {
            "defaultVideoId": None,
            "hasScheduledVideos": media_type == 'series'
        }
    }
    return meta

def get_meta(request, media_type, tmdb_id_str):
    tmdb_id = tmdb_id_str.replace("tmdb:", "")
    tmdb_type = 'tv' if media_type == 'series' else 'movie'

    # 并行获取元数据和演职员信息
    meta_info, credits_info = asyncio.run(asyncio.gather(
        asyncio.to_thread(tmdb_get_meta, tmdb_type, tmdb_id),
        asyncio.to_thread(get_credits, tmdb_type, tmdb_id)
    ))

    if not meta_info:
        return JSONResponse(content={"meta": {}})

    stremio_meta = _to_stremio_meta(request, meta_info, credits_info, media_type)

    if media_type == 'series':
        all_episodes = []
        seasons = [s for s in meta_info.get('seasons', []) if s.get('season_number') != 0]
        for season in seasons:
            episodes = get_season_episodes(tmdb_id, season.get('season_number'))
            all_episodes.extend(episodes)
        stremio_meta['videos'] = _to_stremio_videos(all_episodes, tmdb_id)

    return JSONResponse(content={"meta": stremio_meta})