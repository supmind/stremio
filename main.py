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
    对于搜索请求, 它会进行特殊的、更健壮的解析。
    """
    extra_args = {}
    if extra_props:
        clean_props = extra_props.replace(".json", "")

        if catalog_id == 'tmdb-search':
            # 对于搜索, 采取最直接的解析方式, 避免解析错误。
            # 无论请求是 "search=query" 还是 "query", 都提取 "query"。
            search_query = clean_props
            if search_query.startswith('search='):
                search_query = search_query.split('search=', 1)[1]
            extra_args['search'] = search_query
        else:
            # 对于其他目录 (如 discover), 使用标准的 key=value 解析。
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