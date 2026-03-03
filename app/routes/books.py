"""
书籍路由 - 书籍发布、详情、搜索
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.models import db, Book, User
from app.utils.smart_pricing import calculate_smart_price, SmartPricing
from config import Config
import os

books_bp = Blueprint('books', __name__, url_prefix='/books')


@books_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """发布书籍"""
    if request.method == 'POST':
        # 获取表单数据
        title = request.form.get('title')
        author = request.form.get('author')
        isbn = request.form.get('isbn')
        edition = request.form.get('edition')
        publisher = request.form.get('publisher')
        publish_year = request.form.get('publish_year', type=int)
        original_price = request.form.get('original_price', type=float)
        condition = request.form.get('condition')
        category = request.form.get('category')
        description = request.form.get('description')
        listing_price = request.form.get('listing_price', type=float)
        
        if not title or not listing_price:
            flash('请填写书籍名称和价格', 'danger')
            return render_template('books/create.html')
        
        # 计算智能定价
        book_data = {
            'original_price': original_price,
            'condition': condition,
            'edition': edition,
            'category': category,
            'isbn': isbn
        }
        
        pricing_result = calculate_smart_price(book_data, Config.PRICING)
        
        # 创建书籍
        book = Book(
            title=title,
            author=author,
            isbn=isbn,
            edition=edition,
            publisher=publisher,
            publish_year=publish_year,
            original_price=original_price,
            condition=condition,
            category=category,
            description=description,
            listing_price=listing_price,
            smart_price=pricing_result['smart_price'],
            seller_id=current_user.id,
            status='available'
        )
        
        db.session.add(book)
        db.session.commit()
        
        # 记录智能定价历史
        pricing = SmartPricing(Config.PRICING)
        pricing.record_price(isbn, book.id, listing_price, 'listing')
        pricing.record_price(isbn, book.id, pricing_result['smart_price'], 'smart')
        
        flash('书籍发布成功！', 'success')
        return redirect(url_for('books.detail', book_id=book.id))
    
    return render_template('books/create.html')


@books_bp.route('/<int:book_id>')
def detail(book_id):
    """书籍详情"""
    book = Book.query.get_or_404(book_id)
    
    # 增加浏览量
    book.view_count += 1
    db.session.commit()
    
    # 相似书籍推荐
    similar_books = Book.query.filter(
        Book.category == book.category,
        Book.id != book.id,
        Book.status == 'available'
    ).limit(4).all()
    
    # 获取智能定价详情
    pricing_info = None
    if book.isbn:
        pricing = SmartPricing(Config.PRICING)
        pricing_info = {
            'history': pricing.get_historical_prices(book.isbn),
            'avg_deal_price': pricing.get_average_deal_price(book.isbn)
        }
    
    return render_template('books/detail.html', 
                         book=book, 
                         similar_books=similar_books,
                         pricing_info=pricing_info)


@books_bp.route('/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(book_id):
    """编辑书籍"""
    book = Book.query.get_or_404(book_id)
    
    if book.seller_id != current_user.id:
        flash('您没有权限编辑此书籍', 'danger')
        return redirect(url_for('books.detail', book_id=book_id))
    
    if book.status != 'available':
        flash('该书籍当前无法编辑', 'warning')
        return redirect(url_for('books.detail', book_id=book_id))
    
    if request.method == 'POST':
        book.title = request.form.get('title')
        book.author = request.form.get('author')
        book.isbn = request.form.get('isbn')
        book.edition = request.form.get('edition')
        book.publisher = request.form.get('publisher')
        book.publish_year = request.form.get('publish_year', type=int)
        book.original_price = request.form.get('original_price', type=float)
        book.condition = request.form.get('condition')
        book.category = request.form.get('category')
        book.description = request.form.get('description')
        book.listing_price = request.form.get('listing_price', type=float)
        
        # 重新计算智能定价
        book_data = {
            'original_price': book.original_price,
            'condition': book.condition,
            'edition': book.edition,
            'category': book.category,
            'isbn': book.isbn
        }
        pricing_result = calculate_smart_price(book_data, Config.PRICING)
        book.smart_price = pricing_result['smart_price']
        
        db.session.commit()
        flash('书籍信息已更新', 'success')
        return redirect(url_for('books.detail', book_id=book.id))
    
    return render_template('books/edit.html', book=book)


@books_bp.route('/<int:book_id>/delete', methods=['POST'])
@login_required
def delete(book_id):
    """删除书籍"""
    book = Book.query.get_or_404(book_id)
    
    if book.seller_id != current_user.id:
        flash('您没有权限删除此书籍', 'danger')
        return redirect(url_for('books.detail', book_id=book_id))
    
    book.status = 'withdrawn'
    db.session.commit()
    
    flash('书籍已下架', 'success')
    return redirect(url_for('main.index'))


@books_bp.route('/<int:book_id>/want')
@login_required
def want(book_id):
    """想要这本书"""
    book = Book.query.get_or_404(book_id)
    book.want_count += 1
    db.session.commit()
    
    flash('已添加到想要列表', 'success')
    return redirect(url_for('books.detail', book_id=book_id))


@books_bp.route('/my-books')
@login_required
def my_books():
    """我的书籍"""
    status = request.args.get('status', 'all')
    
    query = Book.query.filter(Book.seller_id == current_user.id)
    
    if status != 'all':
        query = query.filter(Book.status == status)
    
    books = query.order_by(Book.created_at.desc()).all()
    
    return render_template('books/my_books.html', books=books, status=status)


@books_bp.route('/pricing-calculator')
def pricing_calculator():
    """智能定价计算器页面"""
    return render_template('books/pricing_calculator.html')


@books_bp.route('/api/calculate-price', methods=['POST'])
def api_calculate_price():
    """API: 计算智能定价"""
    data = request.get_json()
    
    result = calculate_smart_price(data, Config.PRICING)
    
    return jsonify({
        'success': True,
        'data': result
    })
