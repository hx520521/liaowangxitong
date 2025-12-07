#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Bing搜索爬虫功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from baidu_spider import BingSpider

def test_bing_search():
    """测试Bing搜索功能"""
    print("开始测试Bing搜索爬虫...")
    
    # 创建Bing爬虫实例
    bing_spider = BingSpider()
    
    # 测试搜索关键词
    keyword = "雅安"
    print(f"搜索关键词: {keyword}")
    
    # 执行搜索
    try:
        results = bing_spider.search(keyword)
        
        if not results:
            print("❌ 搜索失败，未获取到结果")
            return False
    except Exception as e:
        print(f"❌ 搜索异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"✅ 搜索成功，获取到 {len(results)} 条结果")
    
    # 打印前5条结果
    print("\n前5条搜索结果:")
    for i, result in enumerate(results[:5], 1):
        print(f"\n结果 {i}:")
        print(f"标题: {result.get('title', '无')}")
        print(f"URL: {result.get('url', '无')}")
        print(f"摘要: {result.get('summary', '无')[:100]}...")
        print(f"封面URL: {result.get('cover_url', '无')}")
        print(f"来源: {result.get('source', '无')}")
    
    return True

if __name__ == "__main__":
    test_bing_search()