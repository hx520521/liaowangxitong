import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlparse
from datetime import datetime
import json

class BaseSpider:
    """基础爬虫类，定义通用接口"""
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/14',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Connection': 'keep-alive'
        }
    
    def search(self, keyword):
        """搜索关键词并返回结果列表"""
        raise NotImplementedError("子类必须实现search方法")
    
    def sniff(self, url):
        """嗅探网页内容，提取标题、内容的XPath和request headers，并保存到数据库"""
        try:
            # 发送请求获取网页内容
            response = requests.get(url, headers=self.headers)
            response.encoding = 'utf-8'
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取域名
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # 提取标题的XPath（这里使用简单的XPath，实际应用中可能需要更复杂的逻辑）
            title_tag = soup.find('title')
            title_xpath = '//title' if title_tag else None
            
            # 提取主要内容的XPath（这里使用简单的选择，实际应用中可能需要更复杂的逻辑）
            content_xpath = None
            # 尝试找到可能包含主要内容的标签
            content_tags = soup.find_all(['article', 'div', 'main'], 
                                      class_=['content', 'main-content', 'article-content', 'post-content', 'text'])
            if content_tags:
                # 简单使用第一个找到的内容标签
                content_xpath = f'//{content_tags[0].name}[@class="{content_tags[0]["class"][0]}"]' if content_tags[0].has_attr('class') else f'//{content_tags[0].name}'
            else:
                # 如果没有找到特定类的内容标签，尝试使用body标签
                content_xpath = '//body'
            
            # 提取request headers
            headers = dict(response.request.headers)
            
            # 生成默认规则名称
            rule_name = f"{domain}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # 不再直接保存到数据库，而是返回结果让前端处理
            return {
                'domain': domain,
                'rule_name': rule_name,
                'title_xpath': title_xpath,
                'content_xpath': content_xpath,
                'headers': headers
            }
            
        except Exception as e:
            print(f"嗅探错误: {e}")
            return None
    
    def crawl_with_rule(self, url, crawl_rule):
        """使用规则采集网页内容"""
        try:
            # 使用规则中的headers或默认headers
            # 确保headers是字典类型
            headers = self.headers.copy()  # 先复制默认headers
            if crawl_rule.headers:
                try:
                    if isinstance(crawl_rule.headers, dict):
                        headers.update(crawl_rule.headers)
                    elif isinstance(crawl_rule.headers, str):
                        # 如果是字符串，尝试解析为JSON
                        import json
                        rule_headers = json.loads(crawl_rule.headers)
                        headers.update(rule_headers)
                except Exception as e:
                    print(f"解析headers失败: {e}")
                    # 解析失败仍使用默认headers
            
            # 发送请求获取网页内容
            print(f"正在采集: {url}")
            print(f"使用headers: {headers}")
            response = requests.get(url, headers=headers, timeout=10)  # 添加超时
            response.encoding = 'utf-8'
            print(f"响应状态码: {response.status_code}")
            
            # 解析HTML
            from lxml import etree
            html = etree.HTML(response.text)
            
            # 使用XPath提取标题
            title = ''
            if crawl_rule.title_xpath:
                try:
                    title_elements = html.xpath(crawl_rule.title_xpath)
                    if title_elements:
                        # 使用lxml正确的文本提取方法
                        title = title_elements[0].xpath('string()').strip()
                    print(f"提取标题: {title}")
                except Exception as e:
                    print(f"提取标题失败: {e}")
            
            # 使用XPath提取内容
            content = ''
            if crawl_rule.content_xpath:
                try:
                    content_elements = html.xpath(crawl_rule.content_xpath)
                    if content_elements:
                        # 使用lxml正确的文本提取方法
                        content = content_elements[0].xpath('string()').strip()
                        # 只保留前1000个字符用于调试
                        print(f"提取内容长度: {len(content)} 字符")
                        print(f"内容前100字符: {content[:100]}...")
                except Exception as e:
                    print(f"提取内容失败: {e}")
            
            return {
                'title': title,
                'content': content
            }
            
        except requests.exceptions.RequestException as e:
            print(f"网络请求错误: {e}")
            raise Exception(f"网络请求错误: {str(e)}")
        except Exception as e:
            print(f"采集错误: {e}")
            raise Exception(f"采集处理错误: {str(e)}")

class BaiduSpider(BaseSpider):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://www.baidu.com/s?wd='
    
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
                    'cover_url': cover_url,
                    'source': 'baidu'
                })
            
            return results
            
        except Exception as e:
            print(f"百度爬虫错误: {e}")
            return []

class BingSpider(BaseSpider):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://cn.bing.com/search?q='
        # 使用Bing特定的headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36 Edg/142.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br, zsdch, zstd',
            'sec-ch-ua': '"Chromium";v="142", "Microsoft Edge";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'dnt': '1',
            'priority': 'u=0, i'
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
                    'cover_url': cover_url,
                    'source': 'baidu'
                })
            
            return results
            
        except Exception as e:
            print(f"爬虫错误: {e}")
            return []

class BingSpider(BaseSpider):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://cn.bing.com/search?q='
        # 使用Bing特定的headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36 Edg/142.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br, zsdch, zstd',
            'sec-ch-ua': '"Chromium";v="142", "Microsoft Edge";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'dnt': '1',
            'priority': 'u=0, i'
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
            
            # 尝试多种Bing搜索结果的标签结构
            search_result_tags = []
            
            # 尝试1: li.b_algo 标签
            algo_tags = soup.find_all('li', class_='b_algo')
            search_result_tags.extend(algo_tags)
            
            # 尝试2: 所有可能的结果容器
            if not search_result_tags:
                # 尝试查找所有包含h2和a标签的div
                div_tags = soup.find_all('div')
                for div in div_tags:
                    h2 = div.find('h2')
                    if h2 and h2.find('a'):
                        search_result_tags.append(div)
            
            for tag in search_result_tags:
                try:
                    # 提取标题和URL - h2标签在div.b_algoheader内的a标签中
                    algoheader = tag.find('div', class_='b_algoheader')
                    if not algoheader:
                        continue
                        
                    # 找到a标签
                    url_tag = algoheader.find('a')
                    if not url_tag:
                        continue
                    
                    # 提取URL
                    url = url_tag.get('href', '')
                    
                    # 提取标题 - h2标签在a标签内部
                    title_tag = url_tag.find('h2') or url_tag.find('h3')
                    if not title_tag:
                        continue
                    title = title_tag.get_text().strip()
                    
                    # 提取摘要
                    summary = ''
                    # 尝试多种摘要标签结构
                    summary_tag = tag.find('div', class_='b_caption') or tag.find('div', class_='c-abstract')
                    if summary_tag:
                        # 移除摘要中的多余标签
                        for br in summary_tag.find_all('br'):
                            br.replace_with(' ')
                        summary = summary_tag.get_text().strip()
                    else:
                        # 尝试获取所有文本内容作为摘要
                        all_text = tag.get_text().strip()
                        if len(all_text) > len(title) + 10:
                            summary = all_text[len(title):].strip()[:200]
                    
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
                        'cover_url': cover_url,
                        'source': 'bing'
                    })
                except Exception as e:
                    continue
            return results
            
        except Exception as e:
            print(f"Bing爬虫错误: {e}")
            return []