from elasticsearch import Elasticsearch
from config import ES_HOST, ES_PORT, ES_INDEX

# 全局 Elasticsearch 客户端实例
es_client = None

def get_es_client():
    """
    获取 Elasticsearch 客户端的单例。
    如果客户端未初始化, 则尝试初始化。
    """
    global es_client
    if es_client is None:
        try:
            # 从配置初始化客户端
            client = Elasticsearch(
                [{'host': ES_HOST, 'port': ES_PORT, 'scheme': 'http'}]
            )
            # 检查连接是否成功
            if not client.ping():
                print("警告: 无法连接到 Elasticsearch。搜索功能将不可用。")
                return None
            es_client = client
        except Exception as e:
            print(f"初始化 Elasticsearch 客户端时发生错误: {e}")
            return None
    return es_client

def search_infohash(title):
    """
    在 Elasticsearch 中根据标题搜索 infohash。

    :param title: 电影或剧集的标题
    :return: 找到的第一个 infohash, 如果找不到或出错则返回 None
    """
    client = get_es_client()
    if not client:
        return None

    # 构建搜索查询。
    # 假设 infohash 存储在 'infohash' 字段, 标题在 'name' 字段。
    # 这个查询会寻找 'name' 字段与 `title` 精确匹配的文档。
    # 你可能需要根据你的实际情况调整查询, 例如使用 'match' 来进行全文搜索。
    query = {
        "query": {
            "term": {
                "name.keyword": title  # 假设你有一个 'name.keyword' 字段用于精确匹配
            }
        },
        "size": 1 # 我们只需要一个结果
    }

    try:
        # 在指定的索引中执行搜索
        response = client.search(index=ES_INDEX, body=query)
        hits = response.get('hits', {}).get('hits', [])

        if hits:
            # 返回第一个匹配结果的 infohash
            # 假设 infohash 存储在 _source 的 'infohash' 字段中
            infohash = hits[0].get('_source', {}).get('infohash')
            if infohash:
                print(f"为 '{title}' 找到 Infohash: {infohash}")
                return infohash
            else:
                print(f"为 '{title}' 找到的文档中不包含 'infohash' 字段。")
                return None
        else:
            print(f"在 Elasticsearch 中未找到标题为 '{title}' 的资源。")
            return None
    except Exception as e:
        print(f"在 Elasticsearch 中搜索时发生错误: {e}")
        return None
