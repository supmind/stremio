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
async def read_catalog_simple(request: Request, media_type: str, catalog_id: str):
    """
    处理不带 extra_props 的 catalog 请求, 例如主页上的热门和高分榜。
    """
    return await get_catalog(request, media_type, catalog_id)

# 修改: 处理带 extra_props 的 catalog 请求
@app.get("/catalog/{media_type}/{catalog_id}/{extra_props:path}.json")
async def read_catalog_with_extras(request: Request, media_type: str, catalog_id: str, extra_props: Optional[str] = None):
    """
    处理所有带 extra_props 的 catalog 请求。
    extra_props 可以是 "key=value&key2=value2" 格式,
    对于搜索, 也可能是纯文本查询, 如 "The Queen's Gambit"。
    """
    extra_args = {}
    if extra_props:
        clean_props = extra_props.replace(".json", "")
        # 检查是否为纯文本搜索查询 (不含 '=')
        is_raw_search = catalog_id == 'tmdb-search' and '=' not in clean_props

        if is_raw_search:
            # 如果是纯文本, 直接作为搜索词
            extra_args['search'] = clean_props
        else:
            # 否则, 按 key=value 对解析
            try:
                extra_args = dict(prop.split("=") for prop in clean_props.split("&"))
            except ValueError:
                # 忽略格式错误的参数
                pass

    return await get_catalog(request, media_type, catalog_id, extra_args)

@app.get("/meta/{media_type}/{tmdb_id}.json")
async def read_meta(request: Request, media_type: str, tmdb_id: str):
    """
    提供特定内容的元数据。
    """
    return await get_meta(request, media_type, tmdb_id)