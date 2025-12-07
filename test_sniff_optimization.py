import requests
import json
import time

# 测试优化后的嗅探功能
def test_sniff_optimization():
    print("=== 测试优化后的嗅探功能 ===")
    
    # 1. 登录
    login_url = "http://127.0.0.1:5000/login"
    dashboard_url = "http://127.0.0.1:5000/dashboard"
    
    # 创建会话
    session = requests.Session()
    
    # 获取首页cookie
    index_response = session.get(dashboard_url)
    print("首页响应状态码:", index_response.status_code)
    
    # 登录
    login_data = {
        'username': 'admin',
        'password': 'admin888'
    }
    login_response = session.post(login_url, data=login_data, allow_redirects=True)
    
    # 检查登录是否成功
    if "dashboard" in login_response.url:
        print("登录成功")
    else:
        print("登录失败")
        print("登录响应URL:", login_response.url)
        return False
    
    # 2. 测试嗅探功能
    sniff_url = "http://127.0.0.1:5000/sniff_url"
    test_url = "https://www.baidu.com"
    
    sniff_data = {
        'url': test_url
    }
    
    sniff_response = session.post(sniff_url, data=sniff_data)
    sniff_result = sniff_response.json()
    
    print("\n=== 嗅探结果 ===")
    print(f"成功状态: {sniff_result['success']}")
    if sniff_result['success']:
        data = sniff_result['data']
        print(f"规则名称: {data['rule_name']}")
        print(f"域名: {data['domain']}")
        print(f"标题XPath: {data['title_xpath']}")
        print(f"内容XPath: {data['content_xpath']}")
        print(f"请求头: {json.dumps(data['headers'], indent=2)}")
    else:
        print(f"错误信息: {sniff_result['message']}")
        return False
    
    # 3. 测试保存规则功能
    save_url = "http://127.0.0.1:5000/save_crawl_rule"
    
    # 编辑规则
    edited_rule = {
        'rule_name': sniff_result['data']['rule_name'],
        'domain': sniff_result['data']['domain'],
        'title_xpath': sniff_result['data']['title_xpath'],
        'content_xpath': sniff_result['data']['content_xpath'],
        'headers': json.dumps(sniff_result['data']['headers'])
    }
    
    # 修改规则名称进行测试
    edited_rule['rule_name'] = f"测试规则_{int(time.time())}"
    
    save_response = session.post(save_url, data=edited_rule)
    save_result = save_response.json()
    
    print("\n=== 保存规则结果 ===")
    print(f"成功状态: {save_result['success']}")
    if save_result['success']:
        print("规则保存成功")
        return True
    else:
        print(f"错误信息: {save_result['message']}")
        return False

if __name__ == "__main__":
    success = test_sniff_optimization()
    if success:
        print("\n✅ 优化后的嗅探功能测试成功！")
    else:
        print("\n❌ 优化后的嗅探功能测试失败！")