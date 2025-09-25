from fastapi.responses import JSONResponse
from tmdb import get_meta as tmdb_get_meta, get_season_episodes, get_genres, discover_media
from config import PLUGIN_ID, PLUGIN_NAME, PLUGIN_VERSION, PLUGIN_DESCRIPTION
import asyncio
from datetime import datetime, timezone

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

    # 新的主页目录 (支持分页)
    home_catalogs = [
        {"type": "movie", "id": "tmdb-popular", "name": "热门电影", **paginated_behavior, "extra": [{"name": "skip"}]},
        {"type": "movie", "id": "tmdb-top-rated", "name": "高分电影", **paginated_behavior, "extra": [{"name": "skip"}]},
        {"type": "series", "id": "tmdb-popular", "name": "热门剧集", **paginated_behavior, "extra": [{"name": "skip"}]},
        {"type": "series", "id": "tmdb-top-rated", "name": "高分剧集", **paginated_behavior, "extra": [{"name": "skip"}]}
    ]

    # 新的发现页面目录 (支持分页)
    discover_catalogs = [
        {"type": "movie", "id": "tmdb-discover-popular", "name": "电影 - 热门", **paginated_behavior, "extra": [{"name": "skip"}]},
        {"type": "movie", "id": "tmdb-discover-top-rated", "name": "电影 - 评分", **paginated_behavior, "extra": [{"name": "skip"}]},
        {"type": "movie", "id": "tmdb-discover-all", "name": "电影 - 全部", **paginated_behavior, "extra": movie_extra_discover},
        {"type": "series", "id": "tmdb-discover-popular", "name": "剧集 - 热门", **paginated_behavior, "extra": [{"name": "skip"}]},
        {"type": "series", "id": "tmdb-discover-top-rated", "name": "剧集 - 评分", **paginated_behavior, "extra": [{"name": "skip"}]},
        {"type": "series", "id": "tmdb-discover-all", "name": "剧集 - 全部", **paginated_behavior, "extra": series_extra_discover}
    ]

    return {
        "id": PLUGIN_ID, "version": "1.0.9", "name": PLUGIN_NAME, "description": PLUGIN_DESCRIPTION,
        "resources": ["catalog", "meta"], "types": ["movie", "series"], "idPrefixes": ["tmdb:"],
        "catalogs": home_catalogs + discover_catalogs
    }

def _to_stremio_meta_preview(item, media_type):
    return {
        "id": f"tmdb:{item.get('id')}", "type": media_type,
        "name": item.get('title') if media_type == 'movie' else item.get('name'),
        "poster": f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}" if item.get('poster_path') else None,
    }

def get_catalog(media_type, catalog_id, extra_args=None):
    tmdb_type = 'tv' if media_type == 'series' else 'movie'
    extra_args = extra_args or {}
    page = int(extra_args.get("skip", 0)) // 20 + 1

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

def _to_stremio_meta(item, media_type):
    meta = {
        "id": f"tmdb:{item.get('id')}", "type": media_type,
        "name": item.get('title') if media_type == 'movie' else item.get('name'),
        "poster": f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}" if item.get('poster_path') else None,
        "background": f"https://image.tmdb.org/t/p/original{item.get('backdrop_path')}" if item.get('backdrop_path') else None,
        "description": item.get('overview'),
        "releaseInfo": format_to_iso(item.get('release_date') if media_type == 'movie' else item.get('first_air_date')),
        "imdbRating": item.get('vote_average'), "genres": [genre['name'] for genre in item.get('genres', [])],
    }
    return meta

def get_meta(media_type, tmdb_id_str):
    tmdb_id = tmdb_id_str.replace("tmdb:", "")
    tmdb_type = 'tv' if media_type == 'series' else 'movie'
    meta_info = tmdb_get_meta(tmdb_type, tmdb_id)
    if not meta_info:
        return JSONResponse(content={"meta": {}})
    stremio_meta = _to_stremio_meta(meta_info, media_type)
    if media_type == 'series':
        all_episodes = []
        seasons = [s for s in meta_info.get('seasons', []) if s.get('season_number') != 0]
        for season in seasons:
            episodes = get_season_episodes(tmdb_id, season.get('season_number'))
            all_episodes.extend(episodes)
        stremio_meta['videos'] = _to_stremio_videos(all_episodes, tmdb_id)
    return JSONResponse(content={"meta": stremio_meta})