from fastapi.responses import JSONResponse
from tmdb import (
    get_meta as tmdb_get_meta, get_season_episodes, get_genres, discover_media,
    search_media, get_credits, search_person,
    get_person_combined_credits
)
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

    movie_extra_discover = [
        {"name": "排序", "options": ["热门", "评分", "发行日期"], "isRequired": False},
        {"name": "类型", "options": movie_genres, "isRequired": False},
        {"name": "年份", "options": YEARS, "isRequired": False},
        {"name": "skip"}
    ]
    series_extra_discover = [
        {"name": "排序", "options": ["热门", "评分", "发行日期"], "isRequired": False},
        {"name": "类型", "options": series_genres, "isRequired": False},
        {"name": "年份", "options": YEARS, "isRequired": False},
        {"name": "skip"}
    ]

    paginated_behavior = {"behaviorHints": {"paginated": True}}

    catalogs = [
        {"type": "movie", "id": "tmdb-popular", "name": "热门电影", **paginated_behavior, "extra": [{"name": "skip"}]},
        {"type": "movie", "id": "tmdb-top-rated", "name": "高分电影", **paginated_behavior, "extra": [{"name": "skip"}]},
        {"type": "movie", "id": "tmdb-discover-all", "name": "全部电影", **paginated_behavior, "extra": movie_extra_discover},
        {"type": "series", "id": "tmdb-popular", "name": "热门剧集", **paginated_behavior, "extra": [{"name": "skip"}]},
        {"type": "series", "id": "tmdb-top-rated", "name": "高分剧集", **paginated_behavior, "extra": [{"name": "skip"}]},
        {"type": "series", "id": "tmdb-discover-all", "name": "全部剧集", **paginated_behavior, "extra": series_extra_discover}
    ]

    search_catalogs = [
        {"type": "movie", "id": "tmdb-search", "name": "电影搜索", "extra": [{"name": "search", "isRequired": True}]},
        {"type": "series", "id": "tmdb-search", "name": "剧集搜索", "extra": [{"name": "search", "isRequired": True}]}
    ]
    catalogs.extend(search_catalogs)

    return {
        "id": PLUGIN_ID, "version": "1.1.0", "name": PLUGIN_NAME, "description": PLUGIN_DESCRIPTION,
        "resources": ["catalog", "meta", "search"], "types": ["movie", "series"], "idPrefixes": ["tmdb:", "tt"],
        "catalogs": catalogs
    }

def _to_stremio_meta_preview(request, item, media_type):
    tmdb_item_type = item.get('media_type', 'tv' if media_type == 'series' else 'movie')
    release_date_key = 'release_date' if tmdb_item_type == 'movie' else 'first_air_date'
    release_date = item.get(release_date_key)
    year = release_date.split('-')[0] if release_date else None
    name = item.get('title') if tmdb_item_type == 'movie' else item.get('name')
    rating = item.get('vote_average')
    overview = item.get('overview')

    description_parts = []
    # if rating:
    #     description_parts.append(f"⭐ {rating:.1f}/10")
    if overview:
        description_parts.append(overview)
    formatted_description = "\n\n".join(description_parts)

    return {
        "id": f"tmdb:{item.get('id')}",
        "type": media_type,
        "name": name,
        "poster": f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}" if item.get('poster_path') else None,
        "description": formatted_description,
        "releaseInfo": year,
        "imdbRating": f"{rating:.1f}" if rating else None,
    }

async def get_catalog(request, media_type, catalog_id, extra_args=None):
    tmdb_type = 'tv' if media_type == 'series' else 'movie'
    extra_args = extra_args or {}
    page = int(extra_args.get("skip", 0)) // 20 + 1
    search_query = extra_args.get("search")

    if catalog_id == 'tmdb-search' and search_query:
        items = []
        person_id = await asyncio.to_thread(search_person, search_query)

        if person_id:
            all_works = await asyncio.to_thread(get_person_combined_credits, person_id)
            if all_works:
                person_works = [work for work in all_works if work.get('media_type') == tmdb_type]
                if person_works:
                    items.extend(person_works)

        if not items:
            title_results = await asyncio.to_thread(search_media, search_query, page)
            items.extend([item for item in title_results if item.get('media_type') == tmdb_type])

        items.sort(key=lambda x: x.get('vote_average') or 0, reverse=True)
        metas = [_to_stremio_meta_preview(request, item, media_type) for item in items]
        return JSONResponse(content={"metas": metas})

    sort_by = "popular"
    if "top-rated" in catalog_id:
        sort_by = "top_rated"
    elif "popular" in catalog_id:
        sort_by = "popular"

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

    items = await asyncio.to_thread(discover_media, tmdb_type, genre_id, sort_by, year, page)
    metas = [_to_stremio_meta_preview(request, item, media_type) for item in items]
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
    imdb_id = item.get('external_ids', {}).get('imdb_id')
    stremio_id = imdb_id if imdb_id else f"tmdb:{item.get('id')}"
    rating = item.get('vote_average')

    links = []
    if rating:
        links.append({"name": f"{rating:.1f}", "category": "imdb", "url": f"https://imdb.com/title/{imdb_id}"})

    genre_names = [genre['name'] for genre in item.get('genres', [])]
    links.extend([{"name": name, "category": "Genres", "url": f"stremio:///discover/{quote(transport_url, safe='')}/{media_type}/tmdb-discover-all?类型={quote(name)}"} for name in genre_names])

    if credits:
        directors = [member['name'] for member in credits.get('crew', []) if member.get('job') == 'Director']
        if not directors and media_type == 'series':
            directors = [creator['name'] for creator in item.get('created_by', [])]
        links.extend([{"name": name, "category": "Directors", "url": f"stremio:///search?search={quote(name)}"} for name in directors])

        cast = [member['name'] for member in credits.get('cast', [])[:10]]
        links.extend([{"name": name, "category": "Cast", "url": f"stremio:///search?search={quote(name)}"} for name in cast])

    release_info = ""
    if media_type == 'movie':
        release_date_str = item.get('release_date')
        if release_date_str:
            release_info = release_date_str.split('-')[0]
    elif media_type == 'series':
        start_year = item.get('first_air_date', '').split('-')[0]
        end_year = item.get('last_air_date', '').split('-')[0] if item.get('status') in ['Ended', 'Canceled'] else ''
        if start_year and end_year and start_year != end_year:
            release_info = f"{start_year}–{end_year}"
        elif start_year and item.get('status') not in ['Ended', 'Canceled']:
            release_info = f"{start_year}–"
        else:
            release_info = start_year

    meta = {
        "id": stremio_id,
        "type": media_type,
        "name": item.get('title') if media_type == 'movie' else item.get('name'),
        "poster": f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}" if item.get('poster_path') else None,
        "background": f"https://image.tmdb.org/t/p/original{item.get('backdrop_path')}" if item.get('backdrop_path') else None,
        "description": item.get('overview'),
        "releaseInfo": release_info,
        "imdbRating": f"{rating:.1f}" if rating else None,
        "links": links,
        "videos": [],
        "behaviorHints": {"defaultVideoId": None, "hasScheduledVideos": media_type == 'series'}
    }
    return meta

async def get_meta(request, media_type, tmdb_id_str):
    tmdb_id = tmdb_id_str.replace("tmdb:", "").replace("tt", "")
    tmdb_type = 'tv' if media_type == 'series' else 'movie'

    meta_info, credits_info = await asyncio.gather(
        asyncio.to_thread(tmdb_get_meta, tmdb_type, tmdb_id),
        asyncio.to_thread(get_credits, tmdb_type, tmdb_id)
    )

    if not meta_info:
        return JSONResponse(content={"meta": {}})

    stremio_meta = _to_stremio_meta(request, meta_info, credits_info, media_type)

    if media_type == 'series':
        all_episodes = []
        seasons = [s for s in meta_info.get('seasons', []) if s.get('season_number') != 0]
        tasks = [asyncio.to_thread(get_season_episodes, tmdb_id, season.get('season_number')) for season in seasons]
        season_results = await asyncio.gather(*tasks)
        for episodes in season_results:
            all_episodes.extend(episodes)
        stremio_meta['videos'] = _to_stremio_videos(all_episodes, tmdb_id)

    return JSONResponse(content={"meta": stremio_meta})
