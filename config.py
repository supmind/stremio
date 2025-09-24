import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 从环境变量中获取 TMDB API 密钥
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "your_tmdb_api_key_here")

# 从环境变量中获取 Elasticsearch 配置
ES_HOST = os.getenv("ES_HOST", "localhost")
ES_PORT = int(os.getenv("ES_PORT", "9200"))
ES_INDEX = os.getenv("ES_INDEX", "stremio_torrents") # 假设的索引名

# Stremio 插件配置
PLUGIN_ID = "com.example.stremio-115-plugin"
PLUGIN_VERSION = "0.0.1"
PLUGIN_NAME = "115 Player"
PLUGIN_DESCRIPTION = "一个Stremio插件，用于从115网盘播放视频。"
