from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    student_id = db.Column(db.String(20))  # 学号
    credit_score = db.Column(db.Integer, default=100)  # 信用分
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # 关系
    books = db.relationship('Book', backref='seller', lazy='dynamic', foreign_keys='Book.seller_id')
    orders_as_buyer = db.relationship('Order', backref='buyer', lazy='dynamic', foreign_keys='Order.buyer_id')
    orders_as_seller = db.relationship('Order', backref='seller_order', lazy='dynamic', foreign_keys='Order.seller_id')
    reviews_given = db.relationship('Review', backref='reviewer', lazy='dynamic', foreign_keys='Review.reviewer_id')
    reviews_received = db.relationship('Review', backref='reviewed_user', lazy='dynamic', foreign_keys='Review.user_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Book(db.Model):
    """书籍模型"""
    __tablename__ = 'books'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    isbn = db.Column(db.String(20))
    edition = db.Column(db.String(50))  # 版本
    publisher = db.Column(db.String(100))
    publish_year = db.Column(db.Integer)
    
    # 书籍状况
    condition = db.Column(db.String(20), nullable=False)  # new, like_new, good, fair, poor
    description = db.Column(db.Text)
    cover_image = db.Column(db.String(255))  # 封面图片路径
    
    # AI识别结果（百炼大模型）
    ai_condition = db.Column(db.String(20))  # AI评估的新旧程度
    ai_condition_reason = db.Column(db.Text)  # AI评估依据
    ai_analyzed = db.Column(db.Boolean, default=False)  # 是否已通过AI分析
    
    # 价格相关
    original_price = db.Column(db.Float)  # 原价
    listing_price = db.Column(db.Float, nullable=False)  # 挂牌价
    smart_price = db.Column(db.Float)  # 智能定价
    final_price = db.Column(db.Float)  # 最终成交价
    
    # 分类
    category = db.Column(db.String(50))  # 教材/小说/杂志等
    tags = db.Column(db.String(200))  # 标签，逗号分隔
    
    # 状态
    status = db.Column(db.String(20), default='available')  # available, reserved, sold, withdrawn
    view_count = db.Column(db.Integer, default=0)
    want_count = db.Column(db.Integer, default=0)  # 想要的人数
    
    # 外键
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sold_at = db.Column(db.DateTime)
    
    # 关系
    orders = db.relationship('Order', backref='book', lazy='dynamic')
    reviews = db.relationship('Review', backref='book', lazy='dynamic')
    
    def __repr__(self):
        return f'<Book {self.title}>'

    def get_condition_display(self):
        """获取新旧程度显示文本"""
        condition_map = {
            'new': '全新',
            'like_new': '几乎全新',
            'good': '较好',
            'fair': '一般',
            'poor': '较差'
        }
        return condition_map.get(self.condition, self.condition or '未知')
    
    def get_edition_display(self):
        """获取版本显示文本"""
        if not self.edition:
            return '-'
        edition_map = {
            'latest': '最新版',
            'recent': '近几年版本',
            'old': '旧版'
        }
        return edition_map.get(self.edition, self.edition)

class Order(db.Model):
    """订单模型"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(30), unique=True, nullable=False)  # 订单号
    
    # 关联
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 价格
    price = db.Column(db.Float, nullable=False)
    
    # 交易状态
    status = db.Column(db.String(20), default='pending')  
    # pending: 待确认, confirmed: 已确认, paid: 已付款, shipped: 已发货, completed: 已完成, cancelled: 已取消
    
    # 联系方式（交易时可见）
    contact_info = db.Column(db.String(100))
    
    # 时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Order {self.order_no}>'


class Review(db.Model):
    """评价模型"""
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 被评价的用户
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 评价者
    
    rating = db.Column(db.Integer, nullable=False)  # 1-5 评分
    content = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Review {self.id}>'


class PriceHistory(db.Model):
    """价格历史模型 - 用于智能定价"""
    __tablename__ = 'price_history'
    
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
    isbn = db.Column(db.String(20))  # 相同ISBN的书籍价格历史
    
    price = db.Column(db.Float, nullable=False)
    price_type = db.Column(db.String(20))  # listing: 挂牌价, smart: 智能定价, deal: 成交价
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PriceHistory {self.id}>'
