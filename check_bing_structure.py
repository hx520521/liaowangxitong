# 查看Bing搜索结果详细结构的脚本
with open('bing_response.html', 'r', encoding='utf-8') as f:
    content = f.read()

from bs4 import BeautifulSoup

soup = BeautifulSoup(content, 'html.parser')

# 找到第一个b_algo标签
b_algo = soup.find('li', class_='b_algo')

if b_algo:
    print("=== b_algo标签的所有子标签 ===")
    for child in b_algo.children:
        if child.name:
            print(f"标签名: {child.name}")
            print(f"  Class: {child.get('class', [])}")
            print(f"  文本内容: {child.get_text().strip()[:100]}...")
            print()
    
    print("=== b_algo标签内的所有a标签 ===")
    for a in b_algo.find_all('a'):
        print(f"链接文本: {a.get_text().strip()}")
        print(f"URL: {a.get('href', '')}")
        print(f"  父标签: {a.parent.name} - Class: {a.parent.get('class', [])}")
        print()
    
    print("=== b_algo标签内的所有h2/h3标签 ===")
    for h in b_algo.find_all(['h2', 'h3']):
        print(f"标题文本: {h.get_text().strip()}")
        print(f"  父标签: {h.parent.name} - Class: {h.parent.get('class', [])}")
        print(f"  下一个兄弟: {h.next_sibling.name if h.next_sibling and h.next_sibling.name else None}")
        print()
    
    print("=== b_algo标签内的所有div标签 ===")
    for div in b_algo.find_all('div'):
        print(f"Div Class: {div.get('class', [])}")
        print(f"  文本内容: {div.get_text().strip()[:150]}...")
        print(f"  包含a标签: {div.find('a') is not None}")
        print(f"  包含h2标签: {div.find('h2') is not None}")
        print()
