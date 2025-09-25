from fastapi.responses import JSONResponse
from tmdb import get_meta as tmdb_get_meta, get_season_episodes, get_genres, discover_media
from config import PLUGIN_ID, PLUGIN_NAME, PLUGIN_VERSION, PLUGIN_DESCRIPTION
import asyncio
from datetime import datetime

# 缓存和常量
GENRE_CACHE = {}
SORT_OPTIONS = ["热门", "发行日期", "评分"]
YEARS = [str(year) for year in range(datetime.now().year, 1979, -1)]

async def get_manifest():
    """
    提供插件的 manifest.json。
    """
    if "movie_genres" not in GENRE_CACHE:
        GENRE_CACHE["movie_genres"] = get_genres("movie")
    if "series_genres" not in GENRE_CACHE:
        GENRE_CACHE["series_genres"] = get_genres("tv")

    movie_genres = [genre['name'] for genre in GENRE_CACHE["movie_genres"]]
    series_genres = [genre['name'] for genre in GENRE_CACHE["series_genres"]]

    movie_extra = [{"name": "genre", "options": movie_genres}, {"name": "sort", "options": SORT_OPTIONS}, {"name": "year", "options": YEARS}]
    series_extra = [{"name": "genre", "options": series_genres}, {"name": "sort", "options": SORT_OPTIONS}, {"name": "year", "options": YEARS}]

    return {
        "id": PLUGIN_ID, "version": PLUGIN_VERSION, "name": PLUGIN_NAME, "description": PLUGIN_DESCRIPTION,
        "resources": ["catalog", "meta"], "types": ["movie", "series"], "idPrefixes": ["tmdb:"],
        "catalogs": [
            {"type": "movie", "id": "tmdb-movies-latest", "name": "最新电影", "behaviorHints": {"paginated": True}},
            {"type": "series", "id": "tmdb-series-latest", "name": "最新剧集", "behaviorHints": {"paginated": True}}
        ],
        "filterCatalogs": [
            {"type": "movie", "id": "tmdb-movies-discover", "name": "发现电影", "extra": movie_extra, "behaviorHints": {"paginated": True}},
            {"type": "series", "id": "tmdb-series-discover", "name": "发现剧集", "extra": series_extra, "behaviorHints": {"paginated": True}}
        ]
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

    sort_by = "热门"
    if "discover" in catalog_id:
        sort_by = extra_args.get("sort", "热门")
    else:
        sort_key = catalog_id.split("-")[-1]
        sort_map = {"popular": "热门", "rating": "评分", "latest": "发行日期"}
        if sort_key in sort_map:
            sort_by = sort_map[sort_key]

    genre_name = extra_args.get("genre")
    year = extra_args.get("year")
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
            "episode": episode.get('episode_number'), "released": episode.get('air_date'),
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
        "releaseInfo": item.get('release_date') if media_type == 'movie' else item.get('first_air_date'),
        "imdbRating": item.get('vote_average'), "genres": [genre['name'] for genre in item.get('genres', [])],
    }
    return meta

def get_meta(media_type, tmdb_id_str):
    tmdb_id = tmdb_id_str.replace("tmdb:", "")
    tmdb_type = 'tv' if media_type == 'series' else 'movie'

    # 修正: 调用重命名后的 tmdb_get_meta
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