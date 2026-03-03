import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """应用配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'campus-book-trading-secret-key-2026'
    
    # ==================== 数据库配置 ====================
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = os.environ.get('MYSQL_PORT') or '3306'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'password'
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'campus_books'
    
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # ==================== 百炼AI配置 ====================
    # 申请地址: https://dashscope.console.aliyun.com/
    DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY') or ''
    
    # 分页配置
    BOOKS_PER_PAGE = 12
    ORDERS_PER_PAGE = 10
    
    # 智能定价配置
    PRICING = {
        # 新旧程度系数 (1-10分)
        'condition_weights': {
            'new': 1.0,      # 全新
            'like_new': 0.9, # 几乎全新
            'good': 0.7,     # 较好
            'fair': 0.5,     # 一般
            'poor': 0.3      # 较差
        },
        # 版本系数
        'edition_weights': {
            'latest': 1.0,   # 最新版
            'recent': 0.85,  # 近几年
            'old': 0.6       # 旧版
        },
        # 市场供需系数
        'demand_multiplier': 1.2,  # 需求高时加成
        'supply_multiplier': 0.8,  # 供给多时折扣
        # 基础价格参考
        'base_price_range': (5, 100),  # 最低最高定价
    }
    
    # 文件上传配置
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
