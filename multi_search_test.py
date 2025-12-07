#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多元搜索测试脚本
展示如何使用BaiduSpider和BingSpider进行多元搜索
"""

from baidu_spider import BaiduSpider, BingSpider
from collections import Counter
import json

def multi_search(keyword, sources=['baidu', 'bing']):
    """
    执行多元搜索
    
    Args:
        keyword (str): 搜索关键词
        sources (list): 搜索来源列表，可选值为'baidu'和'bing'
        
    Returns:
        list: 搜索结果列表，包含来自各个搜索引擎的结果
    """
    results = []
    
    # 执行百度搜索
    if 'baidu' in sources:
        print(f"正在从百度搜索: {keyword}")
        baidu_spider = BaiduSpider()
        baidu_results = baidu_spider.search(keyword)
        results.extend(baidu_results)
        print(f"百度搜索完成，获取到 {len(baidu_results)} 条结果")
    
    # 执行Bing搜索
    if 'bing' in sources:
        print(f"正在从Bing搜索: {keyword}")
        bing_spider = BingSpider()
        bing_results = bing_spider.search(keyword)
        results.extend(bing_results)
        print(f"Bing搜索完成，获取到 {len(bing_results)} 条结果")
    
    return results

def display_results(results):
    """
    展示搜索结果
    
    Args:
        results (list): 搜索结果列表
    """
    if not results:
        print("❌ 未获取到搜索结果")
        return
    
    # 统计结果来源
    sources = Counter([r['source'] for r in results])
    print(f"✅ 搜索完成，共获取到 {len(results)} 条结果")
    print(f"   结果来源分布: {dict(sources)}")
    
    # 展示每条结果
    print("\n" + "="*80)
    for i, result in enumerate(results, 1):
        print(f"结果 #{i} ({result['source']})")
        print(f"标题: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"摘要: {result['summary'][:150]}..." if len(result['summary']) > 150 else f"摘要: {result['summary']}")
        if result['cover_url']:
            print(f"封面: {result['cover_url']}")
        print("-"*80)

def main():
    """
    主函数
    """
    print("欢迎使用多元搜索工具")
    print("="*80)
    
    # 测试1: 单一关键词搜索
    keyword = "雅安"
    print(f"\n测试1: 搜索关键词 '{keyword}'")
    results = multi_search(keyword)
    display_results(results)
    
    # 测试2: 只使用百度搜索
    print(f"\n\n测试2: 只使用百度搜索关键词 '{keyword}'")
    baidu_only_results = multi_search(keyword, sources=['baidu'])
    display_results(baidu_only_results)
    
    # 测试3: 只使用Bing搜索
    print(f"\n\n测试3: 只使用Bing搜索关键词 '{keyword}'")
    bing_only_results = multi_search(keyword, sources=['bing'])
    display_results(bing_only_results)
    
    # 测试4: 将结果保存为JSON文件
    print(f"\n\n测试4: 将搜索结果保存为JSON文件")
    with open(f"search_results_{keyword}.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"结果已保存到 search_results_{keyword}.json")

if __name__ == "__main__":
    main()
