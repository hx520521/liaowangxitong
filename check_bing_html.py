# 查看Bing搜索结果HTML结构的脚本
with open('bing_response.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 使用BeautifulSoup解析
from bs4 import BeautifulSoup

soup = BeautifulSoup(content, 'html.parser')

# 查找所有b_algo标签
b_algo_tags = soup.find_all('li', class_='b_algo')
print(f'找到 {len(b_algo_tags)} 个 b_algo 标签')

if b_algo_tags:
    print('\n第一个b_algo标签的完整结构：')
    first_tag = b_algo_tags[0]
    print(first_tag.prettify())
    
    print('\n\n标签中所有的子标签：')
    for child in first_tag.children:
        if child.name:
            print(f'标签名: {child.name}, class: {child.get("class", [])}')
            # 查看h2标签
            if child.name == 'h2':
                print(f'  h2内容: {child.text.strip()}')
                print(f'  h2下的a标签: {child.find("a")}')
            # 查看摘要部分
            elif child.name == 'div':
                print(f'  div内容前200字符: {child.text.strip()[:200]}...')
