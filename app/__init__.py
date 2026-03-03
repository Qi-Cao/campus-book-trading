from flask import Flask
from config import Config
from app.models.models import db
import os

def create_app(config_class=Config):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 初始化数据库
    db.init_app(app)
    
    # 注册蓝图
    from app.routes.auth import auth_bp
    from app.routes.books import books_bp
    from app.routes.orders import orders_bp
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    return app
