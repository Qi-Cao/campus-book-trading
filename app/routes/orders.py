"""
订单路由 - 交易撮合、订单管理
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.models import db, Book, Order, Review
from datetime import datetime
import random
import string

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')


def generate_order_no():
    """生成订单号"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = ''.join(random.choices(string.digits, k=4))
    return f'ORD{timestamp}{random_str}'


@orders_bp.route('/create/<int:book_id>', methods=['GET', 'POST'])
@login_required
def create(book_id):
    """创建订单"""
    book = Book.query.get_or_404(book_id)
    
    # 验证
    if book.status != 'available':
        flash('该书籍已下架或已售出', 'warning')
        return redirect(url_for('books.detail', book_id=book_id))
    
    if book.seller_id == current_user.id:
        flash('不能购买自己的书籍', 'danger')
        return redirect(url_for('books.detail', book_id=book_id))
    
    # GET 请求显示确认页面
    if request.method == 'GET':
        return render_template('orders/create.html', book=book)
    
    # POST 请求创建订单
    order = Order(
        order_no=generate_order_no(),
        book_id=book_id,
        buyer_id=current_user.id,
        seller_id=book.seller_id,
        price=request.form.get('price', type=float) or book.listing_price,
        status='pending',
        contact_info=request.form.get('contact_info', '')
    )
    
    # 更新书籍状态
    book.status = 'reserved'
    
    db.session.add(order)
    db.session.commit()
    
    flash('订单已创建，等待卖家确认', 'success')
    return redirect(url_for('orders.detail', order_id=order.id))


@orders_bp.route('/<int:order_id>')
def detail(order_id):
    """订单详情"""
    order = Order.query.get_or_404(order_id)
    
    # 权限检查
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    if current_user.id not in [order.buyer_id, order.seller_id]:
        flash('您没有权限查看此订单', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('orders/detail.html', order=order)


@orders_bp.route('/<int:order_id>/confirm', methods=['POST'])
@login_required
def confirm(order_id):
    """确认订单（卖家）"""
    order = Order.query.get_or_404(order_id)
    
    if order.seller_id != current_user.id:
        flash('您没有权限操作此订单', 'danger')
        return redirect(url_for('orders.detail', order_id=order_id))
    
    if order.status != 'pending':
        flash('订单状态无法确认', 'warning')
        return redirect(url_for('orders.detail', order_id=order_id))
    
    order.status = 'confirmed'
    db.session.commit()
    
    flash('订单已确认，等待买家付款', 'success')
    return redirect(url_for('orders.detail', order_id=order_id))


@orders_bp.route('/<int:order_id>/pay', methods=['POST'])
@login_required
def pay(order_id):
    """付款（买家）"""
    order = Order.query.get_or_404(order_id)
    
    if order.buyer_id != current_user.id:
        flash('您没有权限操作此订单', 'danger')
        return redirect(url_for('orders.detail', order_id=order_id))
    
    if order.status != 'confirmed':
        flash('订单状态无法付款', 'warning')
        return redirect(url_for('orders.detail', order_id=order_id))
    
    order.status = 'paid'
    db.session.commit()
    
    flash('付款成功，等待卖家发货', 'success')
    return redirect(url_for('orders.detail', order_id=order_id))


@orders_bp.route('/<int:order_id>/ship', methods=['POST'])
@login_required
def ship(order_id):
    """发货（卖家）"""
    order = Order.query.get_or_404(order_id)
    
    if order.seller_id != current_user.id:
        flash('您没有权限操作此订单', 'danger')
        return redirect(url_for('orders.detail', order_id=order_id))
    
    if order.status != 'paid':
        flash('订单状态无法发货', 'warning')
        return redirect(url_for('orders.detail', order_id=order_id))
    
    order.status = 'shipped'
    db.session.commit()
    
    flash('已发货，等待买家确认收货', 'success')
    return redirect(url_for('orders.detail', order_id=order_id))


@orders_bp.route('/<int:order_id>/confirm_receive', methods=['POST'])
@login_required
def confirm_receive(order_id):
    """确认收货（买家）"""
    order = Order.query.get_or_404(order_id)
    
    if order.buyer_id != current_user.id:
        flash('您没有权限操作此订单', 'danger')
        return redirect(url_for('orders.detail', order_id=order_id))
    
    if order.status != 'shipped':
        flash('订单状态无法确认收货', 'warning')
        return redirect(url_for('orders.detail', order_id=order_id))
    
    order.status = 'completed'
    order.completed_at = datetime.utcnow()
    
    # 更新书籍状态
    book = order.book
    book.status = 'sold'
    book.sold_at = datetime.utcnow()
    book.final_price = order.price
    
    # 记录成交价
    from app.utils.smart_pricing import SmartPricing
    from config import Config
    pricing = SmartPricing(Config.PRICING)
    pricing.record_price(book.isbn, book.id, order.price, 'deal')
    
    db.session.commit()
    
    flash('交易完成！请对商品进行评价', 'success')
    return redirect(url_for('orders.review', order_id=order_id))


@orders_bp.route('/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel(order_id):
    """取消订单"""
    order = Order.query.get_or_404(order_id)
    
    # 买家或卖家都可以取消（待确认状态）
    if current_user.id not in [order.buyer_id, order.seller_id]:
        flash('您没有权限操作此订单', 'danger')
        return redirect(url_for('orders.detail', order_id=order_id))
    
    if order.status not in ['pending', 'confirmed']:
        flash('订单状态无法取消', 'warning')
        return redirect(url_for('orders.detail', order_id=order_id))
    
    order.status = 'cancelled'
    
    # 恢复书籍状态
    book = order.book
    book.status = 'available'
    
    db.session.commit()
    
    flash('订单已取消', 'info')
    return redirect(url_for('main.index'))


@orders_bp.route('/<int:order_id>/review', methods=['GET', 'POST'])
@login_required
def review(order_id):
    """评价订单"""
    order = Order.query.get_or_404(order_id)
    
    if order.buyer_id != current_user.id:
        flash('您没有权限评价此订单', 'danger')
        return redirect(url_for('orders.detail', order_id=order_id))
    
    if order.status != 'completed':
        flash('订单未完成，无法评价', 'warning')
        return redirect(url_for('orders.detail', order_id=order_id))
    
    # 检查是否已评价
    existing_review = Review.query.filter_by(order_id=order_id).first()
    if existing_review:
        flash('您已经评价过此订单', 'warning')
        return redirect(url_for('orders.detail', order_id=order_id))
    
    if request.method == 'POST':
        rating = request.form.get('rating', type=int)
        content = request.form.get('content')
        
        if not rating or rating < 1 or rating > 5:
            flash('请选择评分（1-5分）', 'danger')
            return render_template('orders/review.html', order=order)
        
        # 创建评价
        review = Review(
            order_id=order_id,
            book_id=order.book_id,
            user_id=order.seller_id,  # 评价卖家
            reviewer_id=current_user.id,
            rating=rating,
            content=content
        )
        
        # 更新卖家信用分
        seller = order.seller_order
        if rating >= 4:
            seller.credit_score = min(100, seller.credit_score + 2)
        elif rating <= 2:
            seller.credit_score = max(0, seller.credit_score - 2)
        
        db.session.add(review)
        db.session.commit()
        
        flash('评价成功！感谢您的反馈', 'success')
        return redirect(url_for('orders.detail', order_id=order_id))
    
    return render_template('orders/review.html', order=order)


@orders_bp.route('/my-orders')
@login_required
def my_orders():
    """我的订单"""
    role = request.args.get('role', 'buyer')  # buyer, seller, or all
    status = request.args.get('status', 'all')
    
    if role == 'buyer':
        query = Order.query.filter(Order.buyer_id == current_user.id)
    elif role == 'seller':
        query = Order.query.filter(Order.seller_id == current_user.id)
    else:  # all - 显示买家和卖家的所有订单
        query = Order.query.filter(
            (Order.buyer_id == current_user.id) | 
            (Order.seller_id == current_user.id)
        )
    
    if status != 'all':
        query = query.filter(Order.status == status)
    
    orders = query.order_by(Order.created_at.desc()).all()
    
    return render_template('orders/my_orders.html', 
                         orders=orders, 
                         role=role,
                         status=status)
