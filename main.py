from fastapi import FastAPI
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

# 最终修复: 使用单个端点和可选路径参数来处理所有 catalog 请求
@app.get("/catalog/{media_type}/{catalog_id}/{extra_props:path}.json")
async def read_catalog(media_type: str, catalog_id: str, extra_props: Optional[str] = None):
    """
    处理所有 catalog 请求。
    extra_props 是一个可选路径参数, 格式为 "key=value&key2=value2"
    """
    extra_args = {}
    if extra_props:
        try:
            # Stremio 的 extra_props 格式是 "key=value&key2=value2"
            # FastAPI 会自动 URL 解码, 我们只需解析参数
            extra_args = dict(prop.split("=") for prop in extra_props.replace(".json", "").split("&"))
        except ValueError:
            pass # 如果解析失败, extra_args 保持为空

    return get_catalog(media_type, catalog_id, extra_args)

@app.get("/meta/{media_type}/{tmdb_id}.json")
async def read_meta(media_type: str, tmdb_id: str):
    """
    提供特定内容的元数据。
    """
    return get_meta(media_type, tmdb_id)