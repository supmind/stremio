# Stremio TMDB 插件

这是一个为 Stremio 制作的非官方插件, 它只使用 The Movie Database (TMDB) 来提供电影和剧集信息。

## 功能

*   **浏览热门影视**: 从 The Movie Database (TMDB) 获取热门电影和剧集, 并在 Stremio 中展示。
*   **元数据详情**: 显示来自 TMDB 的详细信息, 包括简介、海报、评分等。

## 安装与运行

### 1. 克隆或下载项目

将本项目下载到你的本地机器。

### 2. 配置环境变量

在项目根目录创建一个 `.env` 文件, 并填入你的 TMDB API 读访问令牌。

```
# .env
TMDB_ACCESS_TOKEN="your_tmdb_bearer_token_here"
```

你可以从 [TMDB 网站](https://www.themoviedb.org/settings/api) 的“API 读访问令牌”部分获取。

### 3. 安装依赖

本项目使用 Python。建议在一个虚拟环境中安装依赖。

```bash
pip install -r requirements.txt
```

### 4. 运行插件服务器

安装完依赖后, 你可以运行 FastAPI 服务器。

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

服务器启动后, 你就可以在 Stremio 中通过 `http://127.0.0.1:8000/manifest.json` 地址来安装这个插件了。

祝你使用愉快!