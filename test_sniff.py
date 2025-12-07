import requests

# 测试嗅探功能
def test_sniff():
    # 登录获取会话
    login_url = 'http://127.0.0.1:5000/login'
    login_data = {
        'username': 'admin',
        'password': 'admin888'
    }
    
    with requests.Session() as session:
        # 首先访问首页获取初始cookie
        session.get('http://127.0.0.1:5000/')
        
        # 登录
        login_response = session.post(login_url, data=login_data, allow_redirects=True)
        
        # 检查是否登录成功（通常会重定向到dashboard）
        if 'dashboard' not in login_response.url:
            print("登录失败")
            print(f"登录响应URL: {login_response.url}")
            return
        
        print("登录成功")
        
        # 测试嗅探API
        sniff_url = 'http://127.0.0.1:5000/sniff_url'
        test_url = 'https://www.baidu.com'
        
        sniff_data = {
            'url': test_url
        }
        
        sniff_response = session.post(sniff_url, data=sniff_data)
        
        if sniff_response.status_code == 200:
            result = sniff_response.json()
            if result['success']:
                print("嗅探成功！")
                print(f"域名: {result['data']['domain']}")
                print(f"标题XPath: {result['data']['title_xpath']}")
                print(f"内容XPath: {result['data']['content_xpath']}")
                print(f"请求头: {result['data']['headers']}")
            else:
                print(f"嗅探失败: {result['message']}")
        else:
            print(f"请求失败，状态码: {sniff_response.status_code}")
            print(f"响应内容: {sniff_response.text}")

if __name__ == "__main__":
    test_sniff()