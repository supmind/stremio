from fastapi.responses import JSONResponse
from tmdb import get_popular as tmdb_get_popular, get_meta as tmdb_get_meta, get_season_episodes
from config import PLUGIN_ID, PLUGIN_NAME, PLUGIN_VERSION, PLUGIN_DESCRIPTION

def get_manifest():
    """
    提供插件的 manifest.json。
    这是 Stremio 识别插件的入口点。
    """
    return {
        "id": PLUGIN_ID,
        "version": PLUGIN_VERSION,
        "name": PLUGIN_NAME,
        "description": PLUGIN_DESCRIPTION,
        "resources": [
            "catalog",
            "meta",
        ],
        "types": ["movie", "series"],
        "idPrefixes": ["tmdb:"],
        "catalogs": [
            {
                "type": "movie",
                "id": "tmdb-popular-movies",
                "name": "热门电影"
            },
            {
                "type": "series",
                "id": "tmdb-popular-series",
                "name": "热门剧集"
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

def get_catalog(media_type, catalog_id):
    """
    处理 Stremio 的 catalog 请求。
    """
    if catalog_id not in ["tmdb-popular-movies", "tmdb-popular-series"]:
        return JSONResponse(content={"metas": []})

    tmdb_type = 'tv' if media_type == 'series' else 'movie'
    popular_items = tmdb_get_popular(tmdb_type)
    metas = [_to_stremio_meta_preview(item, media_type) for item in popular_items]
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

    meta_info = tmdb_get_meta(tmdb_type, tmdb_id)
    if not meta_info:
        return JSONResponse(content={"meta": {}})

    stremio_meta = _to_stremio_meta(meta_info, media_type)

    # 如果是剧集, 则获取所有分集信息
    if media_type == 'series':
        all_episodes = []
        # TMDB API 可能会有 "special" 季节, 季号为 0, 通常我们不显示
        seasons = [s for s in meta_info.get('seasons', []) if s.get('season_number') != 0]
        for season in seasons:
            episodes = get_season_episodes(tmdb_id, season.get('season_number'))
            all_episodes.extend(episodes)

        stremio_meta['videos'] = _to_stremio_videos(all_episodes, tmdb_id)

    return JSONResponse(content={"meta": stremio_meta})
