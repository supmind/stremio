from fastapi.responses import JSONResponse
from tmdb import get_popular, get_meta, get_season_episodes, get_genres, discover_media
from config import PLUGIN_ID, PLUGIN_NAME, PLUGIN_VERSION, PLUGIN_DESCRIPTION
import asyncio

# 缓存类型列表以避免重复请求
GENRE_CACHE = {}
SORT_OPTIONS = ["热门程度", "发行日期", "评分"]

async def get_manifest():
    """
    提供插件的 manifest.json。
    该函数现在是异步的,因为它需要从 TMDB 获取类型列表。
    """
    if "movie_genres" not in GENRE_CACHE:
        GENRE_CACHE["movie_genres"] = get_genres("movie")
    if "series_genres" not in GENRE_CACHE:
        GENRE_CACHE["series_genres"] = get_genres("tv")

    movie_genres = [genre['name'] for genre in GENRE_CACHE["movie_genres"]]
    series_genres = [genre['name'] for genre in GENRE_CACHE["series_genres"]]

    return {
        "id": PLUGIN_ID,
        "version": PLUGIN_VERSION,
        "name": PLUGIN_NAME,
        "description": PLUGIN_DESCRIPTION,
        "resources": ["catalog", "meta"],
        "types": ["movie", "series"],
        "idPrefixes": ["tmdb:"],
        "catalogs": [
            {
                "type": "movie",
                "id": "tmdb-discover-movies",
                "name": "发现电影",
                "extra": [
                    {"name": "genre", "options": movie_genres, "isRequired": False},
                    {"name": "sort", "options": SORT_OPTIONS, "isRequired": False}
                ]
            },
            {
                "type": "series",
                "id": "tmdb-discover-series",
                "name": "发现剧集",
                "extra": [
                    {"name": "genre", "options": series_genres, "isRequired": False},
                    {"name": "sort", "options": SORT_OPTIONS, "isRequired": False}
                ]
            }
        ]
    }

def _to_stremio_meta_preview(item, media_type):
    """
    将 TMDB API 返回的条目转换为 Stremio 的 meta 预览格式。
    """
    return {
        "id": f"tmdb:{item.get('id')}",
        "type": media_type,
        "name": item.get('title') if media_type == 'movie' else item.get('name'),
        "poster": f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}" if item.get('poster_path') else None,
    }

def get_catalog(media_type, catalog_id, extra_args=None):
    """
    处理 Stremio 的 catalog 请求, 支持按类型和排序筛选。
    """
    tmdb_type = 'tv' if media_type == 'series' else 'movie'
    genre_name = extra_args.get("genre") if extra_args else None
    sort_by = extra_args.get("sort") if extra_args else "热门程度"

    genre_id = None
    if genre_name:
        genre_list = GENRE_CACHE.get(f"{'series' if tmdb_type == 'tv' else 'movie'}_genres", [])
        for genre in genre_list:
            if genre['name'] == genre_name:
                genre_id = genre['id']
                break

    items = discover_media(tmdb_type, genre_id, sort_by)

    metas = [_to_stremio_meta_preview(item, media_type) for item in items]
    return JSONResponse(content={"metas": metas})

def _to_stremio_videos(episodes, series_id):
    """
    将 TMDB 的分集信息转换为 Stremio 的 video 对象格式。
    """
    videos = []
    for episode in episodes:
        video_id = f"tmdb:{series_id}:{episode.get('season_number')}:{episode.get('episode_number')}"
        videos.append({
            "id": video_id,
            "title": episode.get('name'),
            "season": episode.get('season_number'),
            "episode": episode.get('episode_number'),
            "released": episode.get('air_date'),
            "overview": episode.get('overview'),
            "thumbnail": f"https://image.tmdb.org/t/p/w500{episode.get('still_path')}" if episode.get('still_path') else None,
        })
    return videos

def _to_stremio_meta(item, media_type):
    """
    将 TMDB API 返回的详细信息转换为 Stremio 的 meta 对象格式。
    """
    meta = {
        "id": f"tmdb:{item.get('id')}",
        "type": media_type,
        "name": item.get('title') if media_type == 'movie' else item.get('name'),
        "poster": f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}" if item.get('poster_path') else None,
        "background": f"https://image.tmdb.org/t/p/original{item.get('backdrop_path')}" if item.get('backdrop_path') else None,
        "description": item.get('overview'),
        "releaseInfo": item.get('release_date') if media_type == 'movie' else item.get('first_air_date'),
        "imdbRating": item.get('vote_average'),
        "genres": [genre['name'] for genre in item.get('genres', [])],
    }
    return meta

def get_meta(media_type, tmdb_id_str):
    """
    处理 Stremio 的 meta 请求, 返回单个电影或剧集的详细信息。
    如果请求的是剧集, 则额外获取并返回分集信息。
    """
    tmdb_id = tmdb_id_str.replace("tmdb:", "")
    tmdb_type = 'tv' if media_type == 'series' else 'movie'

    meta_info = get_meta(tmdb_type, tmdb_id)
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