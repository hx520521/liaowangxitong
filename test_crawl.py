from app import app, db
from models import SearchResult, CrawlRule, CrawledContent, ContentDetails
from baidu_spider import BaiduSpider

def test_crawl():
    with app.app_context():
        # 创建一个测试搜索结果
        test_result = SearchResult(
            title='测试标题',
            url='https://example.com',
            source='test',
            user_id=1
        )
        db.session.add(test_result)
        db.session.commit()
        
        # 创建一个测试采集规则
        test_rule = CrawlRule(
            domain='example.com',
            rule_name='测试规则',
            title_xpath='//title',
            content_xpath='//body',
            headers='{}'
        )
        db.session.add(test_rule)
        db.session.commit()
        
        try:
            # 初始化爬虫
            spider = BaiduSpider()
            
            # 执行采集
            print("开始测试采集...")
            crawl_result = spider.crawl_with_rule(test_result.url, test_rule)
            print(f"采集结果: {crawl_result}")
            
            # 创建CrawledContent记录
            crawled_content = CrawledContent(
                result_id=test_result.id,
                rule_id=test_rule.id,
                status='success'
            )
            db.session.add(crawled_content)
            db.session.flush()  # 获取crawled_content.id
            
            # 保存到ContentDetails
            if crawl_result.get('title'):
                title_detail = ContentDetails(
                    content_id=crawled_content.id,
                    field_name='title',
                    field_value=crawl_result['title'],
                    field_type='text'
                )
                db.session.add(title_detail)
            
            if crawl_result.get('content'):
                content_detail = ContentDetails(
                    content_id=crawled_content.id,
                    field_name='content',
                    field_value=crawl_result['content'],
                    field_type='text'
                )
                db.session.add(content_detail)
            
            db.session.commit()
            print("测试采集完成，数据已保存到数据库！")
            
        except Exception as e:
            print(f"测试采集失败: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    test_crawl()