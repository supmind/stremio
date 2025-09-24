# Stremio 115 插件

这是一个为 Stremio 制作的非官方插件, 它结合了 TMDB、Elasticsearch 和 115 网盘, 旨在提供一个完整的观影体验。

## 功能

*   **浏览热门影视**: 从 The Movie Database (TMDB) 获取热门电影和剧集, 并在 Stremio 中展示。
*   **元数据详情**: 显示来自 TMDB 的详细信息, 包括简介、海报、评分等。
*   **自动搜索资源**: 当你选择一个影片时, 插件会自动使用影片标题在你的 Elasticsearch 索引中搜索对应的 BT 种子元数据 (infohash)。
*   **115 离线下载与播放**: 获取到 infohash 后, 插件会调用 115 API (占位符实现) 将资源添加到离线下载任务, 并获取播放链接, 以便你在 Stremio 中直接播放。

## 安装与运行

### 1. 克隆或下载项目

将本项目下载到你的本地机器。

### 2. 配置环境

本项目需要配置两部分信息:

**a) `.env` 文件**

在项目根目录创建一个 `.env` 文件, 并填入以下内容:

*   `TMDB_API_KEY`: 你在 [TMDB 网站](https://www.themoviedb.org/settings/api) 申请的 API 密钥。
*   `ES_HOST`: Elasticsearch 服务器的地址 (例如, `localhost`)。
*   `ES_PORT`: Elasticsearch 服务器的端口 (例如, `9200`)。
*   `ES_INDEX`: 存储 BT 种子元数据的索引名称。

**b) `115-cookies.txt` 文件**

在项目根目录创建一个名为 `115-cookies.txt` 的文件。这个文件用于 115 网盘的登录认证。

你需要从浏览器中导出你的 115 登录 cookies, 并保存为 Netscape cookie 文件格式。一个简单的方法是使用浏览器插件, 例如:
*   Chrome: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
*   Firefox: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

导出后, 将内容粘贴到 `115-cookies.txt` 文件中。

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

## 重要提示

*   **`es_search.py`**: 这个模块中的 Elasticsearch 查询 (`search_infohash` 函数) 是一个示例。你**必须**根据你自己的 Elasticsearch 索引结构来修改查询语句, 以确保能正确地根据标题搜索到 `infohash`。
*   **`pan115.py`**: 这个模块现在使用了 `p115client` 库来与真实的 115 API 进行交互。请确保你已经按照上面的说明正确创建了 `115-cookies.txt` 文件。代码中的等待时间 (`time.sleep`) 是一个预估值, 在处理大型文件时可能需要调整。

祝你使用愉快!
