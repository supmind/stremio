import requests
from config import TMDB_API_KEY

# TMDB API 的基础 URL
BASE_URL = "https://api.themoviedb.org/3"

def get_popular(media_type="movie"):
    """
    从 TMDB API 获取热门电影或剧集。

    :param media_type: 媒体类型, 'movie' 或 'tv' (对应剧集)
    :return: 包含热门内容的列表, 如果出错则返回空列表
    """
    if media_type not in ["movie", "tv"]:
        return []

    # 构建 API 请求 URL
    url = f"{BASE_URL}/{media_type}/popular?api_key={TMDB_API_KEY}&language=zh-CN"

    try:
        response = requests.get(url)
        response.raise_for_status()  # 如果请求失败 (状态码不是 2xx), 则抛出异常
        data = response.json()
        return data.get("results", [])
    except requests.exceptions.RequestException as e:
        print(f"请求 TMDB API 时发生错误: {e}")
        return []

def get_meta(media_type, tmdb_id):
    """
    从 TMDB API 获取单个电影或剧集的详细元数据。

    :param media_type: 媒体类型, 'movie' 或 'tv'
    :param tmdb_id: TMDB ID
    :return: 包含元数据信息的字典, 如果出错则返回 None
    """
    if media_type not in ["movie", "tv"]:
        return None

    # 构建 API 请求 URL
    url = f"{BASE_URL}/{media_type}/{tmdb_id}?api_key={TMDB_API_KEY}&language=zh-CN"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求 TMDB 元数据时发生错误: {e}")
        return None

def get_season_episodes(tv_id, season_number):
    """
    获取单个季度的所有分集信息。

    :param tv_id: 剧集的 TMDB ID
    :param season_number: 季号
    :return: 包含分集信息的列表, 如果出错则返回空列表
    """
    url = f"{BASE_URL}/tv/{tv_id}/season/{season_number}?api_key={TMDB_API_KEY}&language=zh-CN"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("episodes", [])
    except requests.exceptions.RequestException as e:
        print(f"请求 TMDB 季度 {season_number} 信息时发生错误: {e}")
        return []
