import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

class BaiduSpider:
    def __init__(self):
        self.base_url = 'https://www.baidu.com/s?wd='
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/14',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Connection': 'keep-alive'
        }
    
    def search(self, keyword):
        """搜索关键词并返回结果列表"""
        # 对关键词进行URL编码
        encoded_keyword = quote(keyword)
        url = self.base_url + encoded_keyword
        
        try:
            # 发送请求
            response = requests.get(url, headers=self.headers)
            response.encoding = 'utf-8'
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找搜索结果
            results = []
            search_result_tags = soup.find_all('div', class_='result')
            
            for tag in search_result_tags:
                # 提取标题
                title_tag = tag.find('h3')
                if not title_tag:
                    continue
                title = title_tag.get_text().strip()
                
                # 提取URL
                url_tag = title_tag.find('a')
                if not url_tag:
                    continue
                url = url_tag.get('href', '')
                
                # 提取摘要
                summary_tag = tag.find('div', class_='c-abstract')
                summary = summary_tag.get_text().strip() if summary_tag else ''
                
                # 提取封面URL（如果有）
                cover_url = ''
                img_tag = tag.find('img')
                if img_tag:
                    cover_url = img_tag.get('src', '')
                
                # 添加到结果列表
                results.append({
                    'title': title,
                    'summary': summary,
                    'url': url,
                    'cover_url': cover_url
                })
            
            return results
            
        except Exception as e:
            print(f"爬虫错误: {e}")
            return []