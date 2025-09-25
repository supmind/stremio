import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# TMDB API 读访问令牌
TMDB_ACCESS_TOKEN = os.getenv("TMDB_ACCESS_TOKEN")

# [可选] 代理配置
http_proxy = os.getenv("HTTP_PROXY")
https_proxy = os.getenv("HTTPS_PROXY")
PROXIES = {}
if http_proxy:
    PROXIES["http"] = http_proxy
if https_proxy:
    PROXIES["https"] = https_proxy

# Stremio 插件配置
PLUGIN_ID = "com.example.stremio-tmdb-plugin"
PLUGIN_VERSION = "1.0.1"
PLUGIN_NAME = "TMDB Catalog"
PLUGIN_DESCRIPTION = "一个只提供 TMDB 信息的 Stremio 插件。"