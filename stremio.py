from fastapi.responses import JSONResponse
from tmdb import get_popular as tmdb_get_popular, get_meta as tmdb_get_meta
from config import PLUGIN_ID, PLUGIN_NAME, PLUGIN_VERSION, PLUGIN_DESCRIPTION
from es_search import search_infohash
from pan115 import get_115_stream_url

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
            "stream"
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
    这个格式用于在 catalog 中显示。
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
    根据 catalog_id 从 TMDB 获取热门电影或剧集, 并转换为 Stremio 格式。
    """
    if catalog_id not in ["tmdb-popular-movies", "tmdb-popular-series"]:
        return JSONResponse(content={"metas": []})

    # Stremio 使用 'series' 类型, TMDB 使用 'tv'
    tmdb_type = 'tv' if media_type == 'series' else 'movie'

    popular_items = tmdb_get_popular(tmdb_type)

    # 将 TMDB 的数据转换为 Stremio 的 meta 预览列表
    metas = [_to_stremio_meta_preview(item, media_type) for item in popular_items]

    return JSONResponse(content={"metas": metas})

def _to_stremio_meta(item, media_type):
    """
    将 TMDB API 返回的详细信息转换为 Stremio 的 meta 对象格式。
    这个格式用于显示电影或剧集的详情页面。
    """
    meta = {
        "id": f"tmdb:{item.get('id')}",
        "type": media_type,
        "name": item.get('title') if media_type == 'movie' else item.get('name'),
        "poster": f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}" if item.get('poster_path') else None,
        "background": f"https://image.tmdb.org/t/p/original{item.get('backdrop_path')}" if item.get('backdrop_path') else None,
        "description": item.get('overview'),
        "releaseInfo": item.get('release_date') if media_type == 'movie' else item.get('first_air_date'),
        # 可以根据需要添加更多字段, 例如评分、类型等
        "imdbRating": item.get('vote_average'),
        "genres": [genre['name'] for genre in item.get('genres', [])],
    }
    return meta

def get_meta(media_type, tmdb_id_str):
    """
    处理 Stremio 的 meta 请求。
    根据 tmdb_id 从 TMDB 获取单个电影或剧集的详细信息。
    """
    # Stremio 的 ID 格式为 "tmdb:12345", 我们需要提取出数字 ID
    tmdb_id = tmdb_id_str.replace("tmdb:", "")
    tmdb_type = 'tv' if media_type == 'series' else 'movie'

    meta_info = tmdb_get_meta(tmdb_type, tmdb_id)

    if not meta_info:
        return JSONResponse(content={"meta": {}})

    stremio_meta = _to_stremio_meta(meta_info, media_type)

    return JSONResponse(content={"meta": stremio_meta})

def get_stream(media_type, tmdb_id_str):
    """
    处理 stream 请求, 返回播放链接。
    这是整个插件的核心逻辑。
    """
    tmdb_id = tmdb_id_str.replace("tmdb:", "")
    tmdb_type = 'tv' if media_type == 'series' else 'movie'

    # 1. 获取元数据以得到标题
    meta_info = tmdb_get_meta(tmdb_type, tmdb_id)
    if not meta_info:
        return JSONResponse(content={"streams": []})

    title = meta_info.get('title') if tmdb_type == 'movie' else meta_info.get('name')
    if not title:
        return JSONResponse(content={"streams": []})

    print(f"正在为 '{title}' 寻找播放源...")

    # 2. 在 Elasticsearch 中搜索 infohash
    infohash = search_infohash(title)
    if not infohash:
        print(f"未能为 '{title}' 找到 infohash。")
        return JSONResponse(content={"streams": []})

    # 3. 使用 115 API 获取播放链接
    stream_url = get_115_stream_url(infohash)
    if not stream_url:
        print(f"未能从 115 获取 '{title}' 的播放链接。")
        return JSONResponse(content={"streams": []})

    # 4. 构建 Stremio 的 stream 响应
    stream_response = {
        "streams": [
            {
                "name": "115 Player",
                "title": f"{title}\n- 115 云盘",
                "url": stream_url,
            }
        ]
    }

    return JSONResponse(content=stream_response)
