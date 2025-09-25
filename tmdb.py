import requests
from config import TMDB_API_KEY

# TMDB API 的基础 URL
BASE_URL = "https://api.themoviedb.org/3"

def get_popular(media_type="movie", page=1):
    """
    从 TMDB API 获取热门电影或剧集, 支持分页。

    :param media_type: 媒体类型, 'movie' 或 'tv' (对应剧集)
    :param page: 页码
    :return: 包含热门内容的列表, 如果出错则返回空列表
    """
    if media_type not in ["movie", "tv"]:
        return []

    # 构建 API 请求 URL
    url = f"{BASE_URL}/{media_type}/popular?api_key={TMDB_API_KEY}&language=zh-CN&page={page}"

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

def get_genres(media_type="movie"):
    """
    获取 TMDB 的类型列表。
    :param media_type: 'movie' 或 'tv'
    :return: 包含类型ID和名称的字典列表, 如 [{'id': 28, 'name': '动作'}]
    """
    url = f"{BASE_URL}/genre/{media_type}/list?api_key={TMDB_API_KEY}&language=zh-CN"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("genres", [])
    except requests.exceptions.RequestException as e:
        print(f"请求 TMDB 类型列表时发生错误: {e}")
        return []

def discover_media(media_type="movie", genre_id=None, sort_by=None, year=None, page=1):
    """
    根据多种条件发现影视内容, 支持分页。
    :param media_type: 'movie' 或 'tv'
    :param genre_id: 类型的 ID
    :param sort_by: 排序方式
    :param year: 年份
    :param page: 页码
    :return: 包含内容的列表
    """
    sort_map = {
        "热门程度": "popularity.desc",
        "发行日期": "primary_release_date.desc",
        "评分": "vote_average.desc",
    }
    sort_param = sort_map.get(sort_by, "popularity.desc")

    url = f"{BASE_URL}/discover/{media_type}?api_key={TMDB_API_KEY}&language=zh-CN&sort_by={sort_param}&page={page}"
    if genre_id:
        url += f"&with_genres={genre_id}"

    if year:
        if media_type == 'movie':
            url += f"&primary_release_year={year}"
        else: # tv
            url += f"&first_air_date_year={year}"

    # TMDB API 要求, 按评分排序时, 投票数必须达到一个阈值才有意义
    if sort_param == "vote_average.desc":
        url += "&vote_count.gte=100"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except requests.exceptions.RequestException as e:
        print(f"请求 TMDB discover API 时发生错误: {e}")
        return []
