"""
初始化数据库
"""
from app import create_app
from app.models.models import db, User, Book, Order, Review, PriceHistory

def init_db():
    """初始化数据库"""
    app = create_app()
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("✓ 数据库表创建成功")
        
        # 创建测试用户
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@campus.edu',
                phone='13800138000',
                student_id='2024001'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("✓ 测试管理员用户创建成功")
        
        # 创建示例用户
        if not User.query.filter_by(username='testuser').first():
            testuser = User(
                username='testuser',
                email='test@campus.edu',
                phone='13900139000',
                student_id='2024002'
            )
            testuser.set_password('test123')
            db.session.add(testuser)
            print("✓ 测试用户创建成功")
        
        db.session.commit()
        print("\n初始化完成！")
        print("\n测试账号:")
        print("  - 管理员: admin / admin123")
        print("  - 普通用户: testuser / test123")

if __name__ == '__main__':
    init_db()
