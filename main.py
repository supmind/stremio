from fastapi import FastAPI
from stremio import get_manifest, get_catalog, get_meta

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Stremio TMDB Addon is running!"}

@app.get("/manifest.json")
async def read_manifest():
    return await get_manifest()

@app.get("/catalog/{media_type}/{catalog_id}.json")
async def read_catalog_root(media_type: str, catalog_id: str):
    """
    处理不带额外参数的 catalog 请求。
    """
    return get_catalog(media_type, catalog_id)

@app.get("/catalog/{media_type}/{catalog_id}/{extra_props}.json")
async def read_catalog_with_extras(media_type: str, catalog_id: str, extra_props: str):
    """
    处理带有额外参数 (类型筛选、排序) 的 catalog 请求。
    extra_props 的格式为 "key1=value1&key2=value2.json"
    """
    extra_args = dict(prop.split("=") for prop in extra_props.split("&"))
    return get_catalog(media_type, catalog_id, extra_args)

@app.get("/meta/{media_type}/{tmdb_id}.json")
async def read_meta(media_type: str, tmdb_id: str):
    """
    提供特定内容的元数据。
    """
    return get_meta(media_type, tmdb_id)