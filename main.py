from fastapi import FastAPI, Request
from stremio import get_manifest, get_catalog, get_meta
from typing import Optional

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Stremio TMDB Addon is running!"}

@app.get("/manifest.json")
async def read_manifest():
    return await get_manifest()

@app.get("/catalog/{media_type}/{catalog_id}/{extra_props:path}.json")
async def read_catalog(media_type: str, catalog_id: str, extra_props: Optional[str] = None):
    """
    处理所有 catalog 请求, 包括带或不带额外参数的情况。
    - extra_props: 可选路径参数, 格式为 "key1=value1&key2=value2"
    """
    extra_args = {}
    if extra_props:
        # FastAPI 会自动解码 URL, 但我们需要手动解析参数
        try:
            extra_args = dict(prop.split("=") for prop in extra_props.split("&"))
        except ValueError:
            # 如果解析失败, 忽略 extra_props
            pass

    return get_catalog(media_type, catalog_id, extra_args)

@app.get("/meta/{media_type}/{tmdb_id}.json")
async def read_meta(media_type: str, tmdb_id: str):
    """
    提供特定内容的元数据。
    """
    return get_meta(media_type, tmdb_id)