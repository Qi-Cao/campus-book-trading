"""
API 路由 - 提供JSON API接口
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models.models import db, Book, User, Order, Review
from sqlalchemy import func

api_bp = Blueprint('api', __name__)


@api_bp.route('/books', methods=['GET'])
def get_books():
    """获取书籍列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    category = request.args.get('category')
    search = request.args.get('search')
    
    query = Book.query.filter(Book.status == 'available')
    
    if search:
        query = query.filter(
            db.or_(
                Book.title.ilike(f'%{search}%'),
                Book.author.ilike(f'%{search}%'),
                Book.isbn.ilike(f'%{search}%')
            )
        )
    
    if category:
        query = query.filter(Book.category == category)
    
    pagination = query.order_by(Book.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'success': True,
        'data': [{
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'condition': book.condition,
            'listing_price': book.listing_price,
            'smart_price': book.smart_price,
            'category': book.category,
            'cover_image': book.cover_image,
            'seller': {
                'id': book.seller.id,
                'username': book.seller.username,
                'credit_score': book.seller.credit_score
            }
        } for book in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@api_bp.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    """获取书籍详情"""
    book = Book.query.get_or_404(book_id)
    
    return jsonify({
        'success': True,
        'data': {
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'isbn': book.isbn,
            'edition': book.edition,
            'publisher': book.publisher,
            'publish_year': book.publish_year,
            'original_price': book.original_price,
            'condition': book.condition,
            'description': book.description,
            'listing_price': book.listing_price,
            'smart_price': book.smart_price,
            'category': book.category,
            'view_count': book.view_count,
            'want_count': book.want_count,
            'created_at': book.created_at.isoformat(),
            'seller': {
                'id': book.seller.id,
                'username': book.seller.username,
                'credit_score': book.seller.credit_score,
                'books_sold': Book.query.filter(
                    Book.seller_id == book.seller.id,
                    Book.status == 'sold'
                ).count()
            }
        }
    })


@api_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """获取用户信息"""
    user = User.query.get_or_404(user_id)
    
    # 统计数据
    books_selling = Book.query.filter(
        Book.seller_id == user.id,
        Book.status == 'available'
    ).count()
    
    books_sold = Book.query.filter(
        Book.seller_id == user.id,
        Book.status == 'sold'
    ).count()
    
    orders_completed = Order.query.filter(
        db.or_(
            Order.buyer_id == user.id,
            Order.seller_id == user.id
        ),
        Order.status == 'completed'
    ).count()
    
    # 评分统计
    avg_rating = db.session.query(func.avg(Review.rating)).filter(
        Review.user_id == user.id
    ).scalar()
    
    return jsonify({
        'success': True,
        'data': {
            'id': user.id,
            'username': user.username,
            'credit_score': user.credit_score,
            'created_at': user.created_at.isoformat(),
            'stats': {
                'books_selling': books_selling,
                'books_sold': books_sold,
                'orders_completed': orders_completed,
                'avg_rating': round(avg_rating, 1) if avg_rating else None
            }
        }
    })


@api_bp.route('/categories', methods=['GET'])
def get_categories():
    """获取分类列表"""
    categories = db.session.query(
        Book.category,
        func.count(Book.id).label('count')
    ).filter(
        Book.status == 'available',
        Book.category.isnot(None)
    ).group_by(Book.category).all()
    
    return jsonify({
        'success': True,
        'data': [{
            'name': cat.category,
            'count': cat.count
        } for cat in categories]
    })


@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """获取全局统计数据"""
    total_books = Book.query.filter(Book.status == 'available').count()
    total_users = User.query.count()
    total_orders = Order.query.filter(Order.status == 'completed').count()
    
    # 今日新增
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    today_books = Book.query.filter(
        Book.created_at >= today
    ).count()
    
    return jsonify({
        'success': True,
        'data': {
            'total_books': total_books,
            'total_users': total_users,
            'total_orders': total_orders,
            'today_books': today_books
        }
    })


@api_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'success': True,
        'message': 'API is running',
        'version': '1.0.0'
    })
