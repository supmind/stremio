from fastapi import FastAPI
from stremio import get_manifest, get_catalog, get_meta

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Stremio TMDB Addon is running!"}

@app.get("/manifest.json")
async def read_manifest():
    """
    Stremio 插件的 manifest.json
    """
    return get_manifest()

@app.get("/catalog/{media_type}/{catalog_id}.json")
async def read_catalog(media_type: str, catalog_id: str):
    """
    提供内容目录 (例如, 热门电影).
    路径参数:
    - media_type: 'movie' 或 'series'
    - catalog_id: 在 manifest 中定义的 catalog id
    """
    return get_catalog(media_type, catalog_id)

@app.get("/meta/{media_type}/{tmdb_id}.json")
async def read_meta(media_type: str, tmdb_id: str):
    """
    提供特定内容的元数据.
    路径参数:
    - media_type: 'movie' 或 'series'
    - tmdb_id: Stremio 传递的 ID (例如 'tmdb:123')
    """
    return get_meta(media_type, tmdb_id)
