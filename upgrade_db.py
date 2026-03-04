"""
数据库升级脚本
用于添加新字段到已有表
"""
from app import create_app
from app.models.models import db

def upgrade_db():
    """升级数据库表结构"""
    app = create_app()
    
    with app.app_context():
        # 方法1: 使用 migrate（推荐）
        # flask db migrate -m "add cover_images field"
        # flask db upgrade
        
        # 方法2: 手动添加字段（如果 migrate 不可用）
        from sqlalchemy import inspect
        
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"当前数据库表: {tables}")
        
        # 检查 books 表
        if 'books' in tables:
            columns = [c['name'] for c in inspector.get_columns('books')]
            print(f"books 表字段: {columns}")
            
            # 添加 cover_images 字段
            if 'cover_images' not in columns:
                print("\n尝试添加 cover_images 字段...")
                try:
                    # SQLite 语法
                    db.session.execute(db.text(
                        "ALTER TABLE books ADD COLUMN cover_images TEXT"
                    ))
                    db.session.commit()
                    print("✓ cover_images 字段添加成功！")
                except Exception as e:
                    print(f"添加失败（可能是 MySQL）: {e}")
                    print("\n请使用以下命令迁移数据库:")
                    print("  pip install flask-migrate")
                    print("  flask db init")
                    print("  flask db migrate -m 'add cover_images'")
                    print("  flask db upgrade")
        else:
            print("books 表不存在，请先运行 init_db.py")

if __name__ == '__main__':
    upgrade_db()
