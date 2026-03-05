#!/usr/bin/env python3
"""
数据库重置脚本
每次运行此脚本将数据库重置为初始状态
"""
from app import create_app
from app.models.models import db, User, Book, Order, Review, PriceHistory
import os

def reset_db():
    """重置数据库"""
    app = create_app()
    
    with app.app_context():
        print("🔄 开始重置数据库...")
        
        # 1. 删除所有表
        print("  ✗ 删除所有表...")
        db.drop_all()
        print("    ✓ 表已删除")
        
        # 2. 重新创建所有表
        print("  ✓ 创建所有表...")
        db.create_all()
        print("    ✓ 表已创建")
        
        # 3. 创建测试管理员用户
        admin = User(
            username='admin',
            email='admin@campus.edu',
            phone='13800138000',
            student_id='2024001'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print("    ✓ 管理员用户: admin / admin123")
        
        # 4. 创建测试普通用户
        testuser = User(
            username='testuser',
            email='test@campus.edu',
            phone='13900139000',
            student_id='2024002'
        )
        testuser.set_password('test123')
        db.session.add(testuser)
        print("    ✓ 测试用户: testuser / test123")
        
        # 5. 提交更改
        db.session.commit()
        
        print("\n" + "="*50)
        print("✅ 数据库重置完成！")
        print("="*50)
        print("\n📋 测试账号:")
        print("   管理员: admin / admin123")
        print("   用户:   testuser / test123")
        print("\n⚠️  所有数据已被清除！")
        print("="*50)

if __name__ == '__main__':
    reset_db()
