# AI指令解析和功能处理模块
import re
import json
import random
from datetime import datetime

# 定义支持的功能指令
SUPPORTED_COMMANDS = {
    'play_music': ['播放', '音乐', '歌曲'],
    'play_movie': ['播放', '电影', '影片'],
    'show_weather': ['天气', '温度', '预报'],
    'show_report': ['报表', '数据', '图表', '饼图', '柱状图']
}

# 解析用户消息，判断是否包含AI指令
def parse_ai_command(message):
    """
    解析用户消息，判断是否包含@AI指令
    :param message: 用户发送的消息
    :return: tuple (is_ai_command, command_type, command_params)
    """
    # 检查是否包含@AI或@ai
    if not re.search(r'@(AI|ai)', message):
        return False, None, None
    
    # 提取指令内容（@AI后面的部分）
    command_content = re.sub(r'@(AI|ai)\s*', '', message).strip()
    if not command_content:
        return True, None, None
    
    # 判断指令类型
    command_type = None
    for cmd, keywords in SUPPORTED_COMMANDS.items():
        for keyword in keywords:
            if keyword in command_content:
                command_type = cmd
                break
        if command_type:
            break
    
    return True, command_type, command_content

# 处理AI指令
def handle_ai_command(command_type, command_params, user_id):
    """
    根据指令类型处理AI指令
    :param command_type: 指令类型
    :param command_params: 指令参数
    :param user_id: 用户ID
    :return: dict 包含响应内容和功能类型
    """
    if not command_type:
        return {
            'type': 'text',
            'content': '你好！我是智能助手，我可以为你提供以下服务：\n1. 播放音乐 - @AI 播放一首音乐\n2. 播放电影 - @AI 播放一部电影\n3. 展示天气 - @AI 查询天气\n4. 数据报表 - @AI 展示数据报表'
        }
    
    handlers = {
        'play_music': handle_play_music,
        'play_movie': handle_play_movie,
        'show_weather': handle_show_weather,
        'show_report': handle_show_report
    }
    
    handler = handlers.get(command_type)
    if handler:
        return handler(command_params, user_id)
    
    return {
        'type': 'text',
        'content': '抱歉，我还不支持这个功能。请尝试其他指令。'
    }

# 处理播放音乐指令
def handle_play_music(params, user_id):
    """
    处理播放音乐指令
    :param params: 指令参数
    :param user_id: 用户ID
    :return: dict 音乐播放响应
    """
    # 模拟音乐列表
    music_list = [
        {"id": 1, "title": "小幸运", "artist": "田馥甄"},
        {"id": 2, "title": "晴天", "artist": "周杰伦"},
        {"id": 3, "title": "起风了", "artist": "买辣椒也用券"},
        {"id": 4, "title": "成都", "artist": "赵雷"},
        {"id": 5, "title": "海阔天空", "artist": "Beyond"}
    ]
    
    # 随机选择一首音乐
    selected_music = random.choice(music_list)
    
    return {
        'type': 'music',
        'content': f'正在为你播放：{selected_music["title"]} - {selected_music["artist"]}',
        'music_info': selected_music
    }

# 处理播放电影指令
def handle_play_movie(params, user_id):
    """
    处理播放电影指令
    :param params: 指令参数
    :param user_id: 用户ID
    :return: dict 电影播放响应
    """
    # 模拟电影列表
    movie_list = [
        {"id": 1, "title": "流浪地球", "director": "郭帆"},
        {"id": 2, "title": "哪吒之魔童降世", "director": "饺子"},
        {"id": 3, "title": "我不是药神", "director": "文牧野"},
        {"id": 4, "title": "唐人街探案3", "director": "陈思诚"},
        {"id": 5, "title": "你好，李焕英", "director": "贾玲"}
    ]
    
    # 随机选择一部电影
    selected_movie = random.choice(movie_list)
    
    return {
        'type': 'movie',
        'content': f'正在为你播放：{selected_movie["title"]}（导演：{selected_movie["director"]}）',
        'movie_info': selected_movie
    }

# 处理天气查询指令
def handle_show_weather(params, user_id):
    """
    处理天气查询指令
    :param params: 指令参数
    :param user_id: 用户ID
    :return: dict 天气信息响应
    """
    # 模拟天气数据
    weather_data = {
        "city": "北京",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "temperature": f"{random.randint(10, 35)}°C",
        "weather": random.choice(["晴", "多云", "阴", "小雨", "中雨"]),
        "wind": f"{random.randint(1, 5)}级",
        "humidity": f"{random.randint(30, 80)}%"
    }
    
    return {
        'type': 'weather',
        'content': f'{weather_data["city"]} {weather_data["date"]} 天气：{weather_data["weather"]}，温度：{weather_data["temperature"]}，风力：{weather_data["wind"]}，湿度：{weather_data["humidity"]}',
        'weather_info': weather_data
    }

# 处理数据报表指令
def handle_show_report(params, user_id):
    """
    处理数据报表指令
    :param params: 指令参数
    :param user_id: 用户ID
    :return: dict 数据报表响应
    """
    # 模拟报表数据
    chart_type = "pie"  # 默认饼图
    if "柱状图" in params:
        chart_type = "bar"
    
    # 生成随机数据
    if chart_type == "pie":
        report_data = {
            "type": "pie",
            "title": "销售数据统计",
            "labels": ["产品A", "产品B", "产品C", "产品D"],
            "data": [random.randint(100, 500) for _ in range(4)],
            "colors": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0"]
        }
    else:
        report_data = {
            "type": "bar",
            "title": "月度销售额",
            "labels": ["1月", "2月", "3月", "4月", "5月"],
            "data": [random.randint(1000, 5000) for _ in range(5)],
            "colors": ["#FF6384"]
        }
    
    return {
        'type': 'report',
        'content': f'为你展示{report_data["title"]}',
        'report_info': report_data
    }
