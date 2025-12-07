from app import app, db
import os

# 创建应用上下文
with app.app_context():
    # 检查数据库文件是否存在
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    print(f"数据库文件路径: {db_path}")
    print(f"数据库文件是否存在: {os.path.exists(db_path)}")
    
    if os.path.exists(db_path):
        print(f"数据库文件大小: {os.path.getsize(db_path)} bytes")
    
    # 列出所有表
    print("\n数据库中所有表:")
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    for table in tables:
        print(f"- {table}")
        
        # 显示表结构
        print("  表结构:")
        columns = inspector.get_columns(table)
        for col in columns:
            print(f"  - {col['name']} ({col['type']})")
        
        # 显示表索引
        print("  索引:")
        indexes = inspector.get_indexes(table)
        for idx in indexes:
            print(f"  - {idx['name']}: {idx['column_names']} (唯一: {idx['unique']})")
        
        # 尝试查询前5条数据
        try:
            result = db.engine.execute(f"SELECT * FROM {table} LIMIT 5")
            rows = result.fetchall()
            print(f"  数据行数: {len(rows)}")
        except Exception as e:
            print(f"  查询数据出错: {e}")
    
    # 尝试运行一个简单的查询
    print("\n尝试运行简单查询:")
    try:
        from models import SearchResult
        results = SearchResult.query.limit(10).all()
        print(f"查询到 {len(results)} 条SearchResult数据")
    except Exception as e:
        print(f"查询出错: {e}")
        import traceback
        traceback.print_exc()