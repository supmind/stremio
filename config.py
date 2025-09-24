import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 从环境变量中获取 TMDB API 密钥
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "your_tmdb_api_key_here")

# Stremio 插件配置
PLUGIN_ID = "com.example.stremio-tmdb-plugin"
PLUGIN_VERSION = "1.0.0"
PLUGIN_NAME = "TMDB Catalog"
PLUGIN_DESCRIPTION = "一个只提供 TMDB 信息的 Stremio 插件。"
