from app import app

# 测试用户中心页面是否能正常渲染
def test_user_center():
    with app.test_client() as client:
        # 模拟登录用户
        client.post('/login', data={'username': 'admin', 'password': 'admin888'})
        
        # 访问用户中心页面
        response = client.get('/user_center')
        
        # 检查响应状态码
        if response.status_code == 200:
            print('用户中心页面访问成功！')
        else:
            print(f'用户中心页面访问失败，状态码: {response.status_code}')
            print(f'响应内容: {response.data[:1000]}...')

if __name__ == '__main__':
    test_user_center()