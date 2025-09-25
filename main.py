from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from stremio import get_manifest, get_catalog, get_meta
from typing import Optional

app = FastAPI()

# 配置 CORS 中间件
# 允许所有来源、所有方法、所有请求头, 这是 Stremio 插件的推荐配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    """
    extra_args = {}
    if extra_props:
        try:
            extra_args = dict(prop.split("=") for prop in extra_props.split("&"))
        except ValueError:
            pass

    return get_catalog(media_type, catalog_id, extra_args)

@app.get("/meta/{media_type}/{tmdb_id}.json")
async def read_meta(media_type: str, tmdb_id: str):
    """
    提供特定内容的元数据。
    """
    return get_meta(media_type, tmdb_id)