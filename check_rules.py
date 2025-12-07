from app import app, db
from models import CrawlRule

with app.app_context():
    rules = CrawlRule.query.all()
    print('现有规则数量:', len(rules))
    for rule in rules:
        print(f'规则ID: {rule.id}, 域名: {rule.domain}, 规则名称: {rule.rule_name}')
        print(f'  标题XPath: {rule.title_xpath}')
        print(f'  内容XPath: {rule.content_xpath}')
        print(f'  Headers: {rule.headers}')
        print()