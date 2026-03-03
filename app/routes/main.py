"""
主路由 - 首页和公共页面
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.models import db, Book, User, Order
from flask_login import current_user
from sqlalchemy import or_, func

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """首页 - 书籍列表"""
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # 搜索功能
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    query = Book.query.filter(Book.status == 'available')
    
    if search:
        query = query.filter(
            or_(
                Book.title.ilike(f'%{search}%'),
                Book.author.ilike(f'%{search}%'),
                Book.isbn.ilike(f'%{search}%')
            )
        )
    
    if category:
        query = query.filter(Book.category == category)
    
    books = query.order_by(Book.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 热门分类
    categories = db.session.query(
        Book.category, func.count(Book.id)
    ).filter(
        Book.status == 'available',
        Book.category.isnot(None)
    ).group_by(Book.category).all()
    
    # 统计数据
    stats = {
        'total_books': Book.query.filter(Book.status == 'available').count(),
        'total_users': User.query.count(),
        'total_orders': Order.query.filter(Order.status == 'completed').count()
    }
    
    return render_template('index.html', 
                         books=books, 
                         categories=categories,
                         stats=stats,
                         search=search,
                         selected_category=category)


@main_bp.route('/about')
def about():
    """关于页面"""
    return render_template('about.html')


@main_bp.route('/help')
def help():
    """帮助页面"""
    return render_template('help.html')


@main_bp.route('/search')
def search():
    """高级搜索"""
    return redirect(url_for('main.index', search=request.args.get('q', '')))


@main_bp.route('/category/<category>')
def category_books(category):
    """分类页面"""
    return redirect(url_for('main.index', category=category))
