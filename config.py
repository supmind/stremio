import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 从环境变量中获取 TMDB API 读访问令牌
TMDB_ACCESS_TOKEN = os.getenv("TMDB_ACCESS_TOKEN")

# Stremio 插件配置
PLUGIN_ID = "com.example.stremio-tmdb-plugin"
PLUGIN_VERSION = "1.0.0"
PLUGIN_NAME = "TMDB Catalog"
PLUGIN_DESCRIPTION = "一个只提供 TMDB 信息的 Stremio 插件。"