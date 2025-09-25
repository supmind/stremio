from fastapi.responses import JSONResponse
from tmdb import get_meta as tmdb_get_meta, get_season_episodes, get_genres, discover_media
from config import PLUGIN_ID, PLUGIN_NAME, PLUGIN_VERSION, PLUGIN_DESCRIPTION
import asyncio
from datetime import datetime, timezone

# 缓存和常量
GENRE_CACHE = {}
SORT_OPTIONS = ["热门", "发行日期", "评分"]
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
    """
    提供插件的 manifest.json。
    - 首页包含6个目录, 每个目录都支持筛选、排序和分页。
    """
    if "movie_genres" not in GENRE_CACHE: GENRE_CACHE["movie_genres"] = get_genres("movie")
    if "series_genres" not in GENRE_CACHE: GENRE_CACHE["series_genres"] = get_genres("tv")

    movie_genres = [genre['name'] for genre in GENRE_CACHE["movie_genres"]]
    series_genres = [genre['name'] for genre in GENRE_CACHE["series_genres"]]

    movie_extra = [{"name": "genre", "options": movie_genres}, {"name": "sort", "options": SORT_OPTIONS}, {"name": "year", "options": YEARS}]
    series_extra = [{"name": "genre", "options": series_genres}, {"name": "sort", "options": SORT_OPTIONS}, {"name": "year", "options": YEARS}]

    home_catalogs = []
    base_home_sorts = [
        {"id": "popular", "name": "热门"},
        {"id": "rating", "name": "高分"},
        {"id": "latest", "name": "最新"},
    ]
    for cat in base_home_sorts:
        home_catalogs.append({"type": "movie", "id": f"tmdb-movies-{cat['id']}", "name": f"{cat['name']}电影", "extra": movie_extra, "behaviorHints": {"paginated": True}})
    for cat in base_home_sorts:
        home_catalogs.append({"type": "series", "id": f"tmdb-series-{cat['id']}", "name": f"{cat['name']}剧集", "extra": series_extra, "behaviorHints": {"paginated": True}})

    return {
        "id": PLUGIN_ID, "version": PLUGIN_VERSION, "name": PLUGIN_NAME, "description": PLUGIN_DESCRIPTION,
        "resources": ["catalog", "meta"], "types": ["movie", "series"], "idPrefixes": ["tmdb:"],
        "catalogs": home_catalogs,
        # 移除 filterCatalogs
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
    skip = int(extra_args.get("skip", 0))
    page = (skip // 20) + 1

    # 从 catalog_id 中解析出默认排序方式
    sort_key = catalog_id.split("-")[-1]
    sort_map = {"popular": "热门", "rating": "评分", "latest": "发行日期"}
    # 用户在"查看全部"页面选择的排序方式, 会覆盖默认值
    sort_by = extra_args.get("sort", sort_map.get(sort_key, "热门"))

    genre_name = extra_args.get("genre")
    year = extra_args.get("year")
    genre_id = None
    if genre_name:
        genre_list = GENRE_CACHE.get(f"{media_type}_genres", [])
        for genre in genre_list:
            if genre['name'] == genre_name: genre_id = genre['id']; break

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