import requests
import json

# 测试规则库管理功能
class TestRuleLibrary:
    def __init__(self):
        self.base_url = 'http://127.0.0.1:5000'
        self.session = requests.Session()
        
    def login(self):
        """登录系统"""
        login_data = {
            'username': 'admin',
            'password': 'admin888'
        }
        response = self.session.post(f'{self.base_url}/login', data=login_data)
        if 'dashboard' in response.url:
            print('✅ 登录成功')
            return True
        else:
            print('❌ 登录失败')
            return False
    
    def test_rule_library_page(self):
        """测试规则库管理页面"""
        response = self.session.get(f'{self.base_url}/rule_library')
        if response.status_code == 200:
            print('✅ 规则库管理页面访问成功')
            return True
        else:
            print(f'❌ 规则库管理页面访问失败，状态码: {response.status_code}')
            return False
    
    def test_add_rule(self):
        """测试新增规则"""
        rule_data = {
            'action': 'add',
            'rule_name': 'test_rule_' + str(int(time.time())),
            'domain': 'test.example.com',
            'title_xpath': '//h1',
            'content_xpath': '//div[@class="content"]',
            'headers': json.dumps({'User-Agent': 'Test Agent'})
        }
        response = self.session.post(f'{self.base_url}/save_rule', data=rule_data)
        if '规则新增成功' in response.text:
            print('✅ 新增规则成功')
            return True
        else:
            print('❌ 新增规则失败')
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print('=== 规则库管理功能测试 ===')
        
        if not self.login():
            return False
            
        if not self.test_rule_library_page():
            return False
        
        if not self.test_add_rule():
            return False
            
        print('\n✅ 所有测试通过！规则库管理功能正常工作。')
        return True

if __name__ == '__main__':
    import time
    test = TestRuleLibrary()
    test.run_all_tests()