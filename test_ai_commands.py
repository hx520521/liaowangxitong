import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

# 测试用户登录
def test_login():
    print("=== 测试用户登录 ===")
    login_url = f"{BASE_URL}/login"
    login_data = {
        "username": "testuser",
        "password": "testpassword"
    }
    
    session = requests.Session()
    response = session.post(login_url, data=login_data, allow_redirects=True)
    
    if response.status_code == 200 and "dashboard" in response.url:
        print("✅ 用户登录成功")
        return session
    else:
        print("❌ 用户登录失败")
        return None

# 获取聊天室列表
def get_chatrooms(session):
    print("\n=== 获取聊天室列表 ===")
    response = session.get(f"{BASE_URL}/chatrooms")
    
    if response.status_code == 200:
        print("✅ 获取聊天室列表成功")
        # 简单解析HTML获取第一个聊天室ID
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        room_links = soup.find_all('a', href=lambda x: x and x.startswith('/chatroom/'))
        if room_links:
            room_id = room_links[0]['href'].split('/')[-1]
            print(f"找到聊天室ID: {room_id}")
            return room_id
    else:
        print("❌ 获取聊天室列表失败")
    return None

# 测试AI指令
def test_ai_commands(session, room_id):
    print("\n=== 测试AI指令功能 ===")
    
    commands = [
        "@AI 你好",
        "@AI 播放一首音乐",
        "@AI 播放一部电影",
        "@AI 查询天气",
        "@AI 展示数据报表",
        "@AI 展示柱状图"
    ]
    
    for cmd in commands:
        print(f"\n发送指令: {cmd}")
        response = session.post(f"{BASE_URL}/send_message/{room_id}", data={"content": cmd})
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ 发送成功")
                
                # 等待AI回复
                time.sleep(1)
                
                # 获取新消息
                last_msg_id = result['message']['id']
                messages_response = session.get(f"{BASE_URL}/get_messages/{room_id}/{last_msg_id}")
                if messages_response.status_code == 200:
                    messages = messages_response.json()
                    if messages['success'] and messages['messages']:
                        ai_msg = messages['messages'][0]
                        print(f"AI回复: {ai_msg['content']}")
            else:
                print(f"❌ 发送失败: {result['message']}")
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")

# 主函数
if __name__ == "__main__":
    # 登录
    session = test_login()
    if not session:
        exit()
    
    # 获取聊天室ID
    room_id = get_chatrooms(session)
    if not room_id:
        exit()
    
    # 测试AI指令
    test_ai_commands(session, room_id)
    
    print("\n=== 测试完成 ===")
