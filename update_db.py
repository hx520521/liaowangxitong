from app import app, db
from sqlalchemy import text

# 创建应用上下文
with app.app_context():
    print("开始更新数据库表结构...")
    
    # 检查并添加search_result表的缺失列
    print("\n检查search_result表...")
    try:
        # 检查data_source_id列是否存在
        with db.engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(search_result)"))
            columns = [row[1] for row in result]
            
            print(f"当前列: {columns}")
            
            # 添加缺失的列
            if 'data_source_id' not in columns:
                print("添加data_source_id列...")
                conn.execute(text("ALTER TABLE search_result ADD COLUMN data_source_id INTEGER"))
                conn.execute(text("CREATE INDEX ix_search_result_data_source_id ON search_result(data_source_id)"))
            
            if 'spider_id' not in columns:
                print("添加spider_id列...")
                conn.execute(text("ALTER TABLE search_result ADD COLUMN spider_id INTEGER"))
                conn.execute(text("CREATE INDEX ix_search_result_spider_id ON search_result(spider_id)"))
            
            if 'cover_url' not in columns:
                print("添加cover_url列...")
                conn.execute(text("ALTER TABLE search_result ADD COLUMN cover_url VARCHAR(500)"))
            
            conn.commit()
            print("search_result表更新完成")
    except Exception as e:
        print(f"更新search_result表出错: {e}")
        import traceback
        traceback.print_exc()
    
    # 检查其他表是否存在
    print("\n检查其他表...")
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    
    # 需要存在的表
    required_tables = ['user', 'search_result', 'crawl_rule', 'crawled_content', 'content_details', 
                     'data_source', 'industry_tag', 'data_source_tag', 'spider', 'spider_test']
    
    for table in required_tables:
        if table not in tables:
            print(f"警告: {table}表不存在")
        else:
            print(f"✓ {table}表存在")
    
    # 尝试重新运行查询测试
    print("\n测试查询:")
    try:
        from models import SearchResult
        results = SearchResult.query.limit(10).all()
        print(f"✓ 查询成功，找到 {len(results)} 条SearchResult数据")
    except Exception as e:
        print(f"✗ 查询失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n数据库更新完成！")