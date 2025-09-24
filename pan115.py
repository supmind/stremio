import time
import os
from p115client import P115Client

# --- 使用 p115client 库的真实实现 ---

# 假设用户在项目根目录提供了 `115-cookies.txt` 文件
COOKIE_FILE = "115-cookies.txt"

def get_115_client():
    """
    初始化并返回一个 P115Client 实例。
    """
    if not os.path.exists(COOKIE_FILE):
        print(f"错误: 未找到 115 cookie 文件 '{COOKIE_FILE}'。请根据 README 创建该文件。")
        return None
    try:
        # P115Client 会自动处理登录和 token
        client = P115Client(COOKIE_FILE)
        return client
    except Exception as e:
        print(f"初始化 115 客户端时发生错误: {e}")
        return None

def get_115_stream_url(infohash):
    """
    主函数, 使用 p115client 库整合添加任务和获取链接的过程。

    :param infohash: 种子的 infohash
    :return: 视频文件的播放链接, 或 None
    """
    client = get_115_client()
    if not client:
        return None

    magnet_uri = f"magnet:?xt=urn:btih:{infohash}"
    print(f"正在向 115 添加磁力链接任务: {magnet_uri}")

    # 1. 添加离线任务
    try:
        result = client.lixian_add_urls([magnet_uri])
        if not result.get("state"):
            print(f"添加 115 任务失败: {result.get('error_msg')}")
            return None
    except Exception as e:
        print(f"调用 lixian_add_urls 时出错: {e}")
        return None

    print("任务已添加, 等待云端下载完成...")
    # 2. 轮询任务状态
    # 为了简化, 我们这里只等待一个固定的时间, 然后查找最新的任务。
    # 一个更健壮的实现会使用 result 中的 task_id 来轮询特定任务的状态。
    time.sleep(10) # 等待 10 秒, 假设对于小文件足够了

    try:
        # 获取最近的离线任务列表
        tasks = client.lixian_task_list(page=1, page_size=5)
        if not tasks:
            print("未能获取到任务列表。")
            return None

        # 3. 查找与 infohash 匹配的任务
        target_task = None
        for task in tasks:
            if task.get("info_hash", "").lower() == infohash.lower():
                target_task = task
                break

        if not target_task:
            print(f"在最近的任务列表中未找到 infohash 为 {infohash} 的任务。")
            return None

        # 4. 检查任务是否完成
        if target_task.get("status") != 2:
            print(f"任务尚未完成 (状态: {target_task.get('status_text')})。")
            # 在真实应用中, 你可能想在这里等待更长时间或重试
            return None

        print("任务已完成, 正在查找视频文件...")

        # 5. 获取任务中的文件列表
        # 任务的文件列表通常在任务对象中, `file_id` 或 `file_list` 字段
        file_id = target_task.get("file_id")
        if not file_id:
            print("任务中未找到 file_id。")
            return None

        # 使用 file_id 获取文件信息, 这通常是一个目录
        files = client.fs_files(file_id=file_id).get("data", [])

        # 6. 查找视频文件并获取下载链接
        for f in files:
            # 查找最大的视频文件
            file_name = f.get("n", "") # 'n' 是文件名字段
            file_ext = os.path.splitext(file_name)[1].lower()
            if file_ext in ['.mp4', '.mkv', '.avi', '.rmvb', '.mov', '.wmv']:
                pick_code = f.get("pc") # 'pc' 是 pick_code 字段
                if pick_code:
                    print(f"找到视频文件: {file_name}, 正在获取播放链接...")
                    # 使用 pick_code 获取视频播放信息
                    video_info = client.video_data(pick_code)
                    play_url = video_info.get("data", {}).get("video_url")
                    if play_url:
                        print("成功获取播放链接！")
                        return play_url
                    else:
                        print(f"未能为文件 {file_name} 获取到 video_url。")

        print("在任务中未找到可播放的视频文件链接。")
        return None

    except Exception as e:
        print(f"在处理 115 任务时发生错误: {e}")
        return None
