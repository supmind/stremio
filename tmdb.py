import requests
from config import TMDB_ACCESS_TOKEN

# TMDB API 的基础 URL 和通用请求头
BASE_URL = "https://api.themoviedb.org/3"
HEADERS = {
    "accept": "application/json",
    "Authorization": f"Bearer {TMDB_ACCESS_TOKEN}"
}

def get_meta(media_type, tmdb_id):
    """
    从 TMDB API 获取单个电影或剧集的详细元数据。
    """
    if media_type not in ["movie", "tv"]:
        return None
    url = f"{BASE_URL}/{media_type}/{tmdb_id}?language=zh-CN"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求 TMDB 元数据时发生错误: {e}")
        return None

def get_season_episodes(tv_id, season_number):
    """
    获取单个季度的所有分集信息。
    """
    url = f"{BASE_URL}/tv/{tv_id}/season/{season_number}?language=zh-CN"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        return data.get("episodes", [])
    except requests.exceptions.RequestException as e:
        print(f"请求 TMDB 季度 {season_number} 信息时发生错误: {e}")
        return []

def get_genres(media_type="movie"):
    """
    获取 TMDB 的类型列表, 并排除“成人”类型。
    """
    url = f"{BASE_URL}/genre/{media_type}/list?language=zh-CN"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        return [genre for genre in data.get("genres", []) if genre['name'] != "成人"]
    except requests.exceptions.RequestException as e:
        print(f"请求 TMDB 类型列表时发生错误: {e}")
        return []

def discover_media(media_type="movie", genre_id=None, sort_by=None, year=None, page=1):
    """
    根据多种条件发现影视内容, 支持分页, 排除成人内容。
    """
    sort_map = {
        "热门": "popularity.desc",
        "发行日期": "primary_release_date.desc",
        "评分": "vote_average.desc",
    }
    sort_param = sort_map.get(sort_by, "popularity.desc")

    params = {
        'language': 'zh-CN',
        'sort_by': sort_param,
        'page': page,
        'include_adult': 'false'
    }
    if genre_id:
        params['with_genres'] = genre_id
    if year:
        if media_type == 'movie':
            params['primary_release_year'] = year
        else:
            params['first_air_date_year'] = year
    if sort_param == "vote_average.desc":
        params['vote_count.gte'] = 300 if media_type == 'movie' else 200

    url = f"{BASE_URL}/discover/{media_type}"
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except requests.exceptions.RequestException as e:
        print(f"请求 TMDB discover API 时发生错误: {e}")
        return []