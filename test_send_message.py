#!/usr/bin/env python3
# 测试send_message函数的脚本
import requests
import json

# 登录信息
login_data = {
    'username': 'testuser',
    'password': 'testpassword'
}

# 发送登录请求
session = requests.Session()
login_response = session.post('http://localhost:5000/login', data=login_data)

if login_response.status_code == 200:
    print('登录成功')
    
    # 获取测试聊天室ID
    chatrooms_response = session.get('http://localhost:5000/chatrooms')
    print('聊天室列表状态:', chatrooms_response.status_code)
    
    # 发送消息测试
    message_data = {
        'content': '测试消息'
    }
    
    # 假设聊天室ID为1，根据实际情况修改
    room_id = 5  # 根据之前创建的测试聊天室ID
    
    send_response = session.post(f'http://localhost:5000/send_message/{room_id}', data=message_data)
    print('发送消息状态:', send_response.status_code)
    print('发送消息响应:', send_response.text)
    
    try:
        response_json = send_response.json()
        print('JSON响应:', json.dumps(response_json, indent=2))
    except json.JSONDecodeError:
        print('响应不是有效的JSON')
        print('响应内容:', send_response.content)
else:
    print('登录失败:', login_response.status_code)
    print('登录响应:', login_response.text)