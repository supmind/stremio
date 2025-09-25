from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from stremio import get_manifest, get_catalog, get_meta

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

# 最终修复: 为 catalog 提供两个明确的端点, 这是最稳健的方案

@app.get("/catalog/{media_type}/{catalog_id}.json")
async def read_catalog_root(media_type: str, catalog_id: str):
    """
    处理不带额外参数的 catalog 请求 (例如首页的六个目录)。
    """
    return get_catalog(media_type, catalog_id)

@app.get("/catalog/{media_type}/{catalog_id}/{extra_props}.json")
async def read_catalog_with_extras(media_type: str, catalog_id: str, extra_props: str):
    """
    处理带有额外参数 (类型筛选、排序、分页) 的 catalog 请求 (来自发现页)。
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