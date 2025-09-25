from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from stremio import get_manifest, get_catalog, get_meta
from typing import Optional

app = FastAPI()

# 配置 CORS 中间件
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

# 新增: 处理不带 extra_props 的 catalog 请求
@app.get("/catalog/{media_type}/{catalog_id}.json")
async def read_catalog_simple(media_type: str, catalog_id: str):
    """
    处理不带 extra_props 的 catalog 请求, 例如主页上的热门和高分榜。
    """
    return get_catalog(media_type, catalog_id)

# 修改: 处理带 extra_props 的 catalog 请求
@app.get("/catalog/{media_type}/{catalog_id}/{extra_props:path}.json")
async def read_catalog_with_extras(media_type: str, catalog_id: str, extra_props: Optional[str] = None):
    """
    处理所有带 extra_props 的 catalog 请求。
    extra_props 是一个可选路径参数, 格式为 "key=value&key2=value2"
    """
    extra_args = {}
    if extra_props:
        try:
            extra_args = dict(prop.split("=") for prop in extra_props.replace(".json", "").split("&"))
        except ValueError:
            pass
    return get_catalog(media_type, catalog_id, extra_args)

@app.get("/meta/{media_type}/{tmdb_id}.json")
async def read_meta(request: Request, media_type: str, tmdb_id: str):
    """
    提供特定内容的元数据。
    """
    return get_meta(request, media_type, tmdb_id)