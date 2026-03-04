"""
书籍路由 - 书籍发布、详情、搜索
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, current_app
from flask_login import login_required, current_user
from app.models.models import db, Book, User
from app.utils.smart_pricing import calculate_smart_price, SmartPricing
from app.utils.dashscope_helper import analyze_book_image, analyze_multiple_images
from config import Config
from werkzeug.utils import secure_filename
import os
import uuid

books_bp = Blueprint('books', __name__, url_prefix='/books')


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def save_uploaded_file(file):
    """保存上传的文件"""
    if file and allowed_file(file.filename):
        # 生成唯一文件名
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        
        # 确保上传目录存在
        upload_folder = os.path.join(current_app.root_path, '..', Config.UPLOAD_FOLDER)
        os.makedirs(upload_folder, exist_ok=True)
        
        # 保存文件
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        return filename
    return None


@books_bp.route('/upload', methods=['POST'])
@login_required
def upload_image():
    """处理图片上传（AJAX）"""
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'})
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    filename = save_uploaded_file(file)
    if not filename:
        return jsonify({'success': False, 'error': 'Invalid file type'})
    
    # 返回文件路径
    return jsonify({
        'success': True,
        'filename': filename,
        'url': url_for('books.uploaded_file', filename=filename)
    })


@books_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    """提供上传的文件"""
    upload_folder = os.path.join(current_app.root_path, '..', Config.UPLOAD_FOLDER)
    return send_from_directory(upload_folder, filename)


@books_bp.route('/analyze-image', methods=['POST'])
@login_required
def analyze_image():
    """AI分析书籍图片（OCR + 新旧程度评估）"""
    # 获取图片数据
    image_data = request.json.get('image_data')  # base64
    filename = request.json.get('filename')
    
    if not image_data and not filename:
        return jsonify({'success': False, 'error': 'No image provided'})
    
    # 调用AI分析
    try:
        if filename:
            # 从文件分析
            upload_folder = os.path.join(current_app.root_path, '..', Config.UPLOAD_FOLDER)
            filepath = os.path.join(upload_folder, filename)
            result = analyze_book_image(image_path=filepath)
        elif image_data:
            # 从base64分析
            result = analyze_book_image(image_base64=image_data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@books_bp.route('/analyze-images', methods=['POST'])
@login_required
def analyze_images():
    """AI批量分析多张书籍图片（OCR + 新旧程度评估）"""
    # 获取图片文件名列表
    filenames = request.json.get('filenames', [])
    
    if not filenames:
        return jsonify({'success': False, 'error': 'No images provided'})
    
    try:
        # 准备图片路径
        upload_folder = os.path.join(current_app.root_path, '..', Config.UPLOAD_FOLDER)
        image_paths = []
        for filename in filenames:
            filepath = os.path.join(upload_folder, filename)
            if os.path.exists(filepath):
                image_paths.append(filepath)
        
        if not image_paths:
            return jsonify({'success': False, 'error': 'No valid images found'})
        
        # 批量分析
        result = analyze_multiple_images(image_paths=image_paths)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


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
        condition = request.form.get('condition')  # 用户选择的新旧程度
        ai_condition = request.form.get('ai_condition')  # AI识别的新旧程度
        category = request.form.get('category')
        description = request.form.get('description')
        listing_price = request.form.get('listing_price', type=float)
        
        # 处理图片上传
        cover_image = None
        cover_images_list = []
        
        # 处理多图片上传
        if 'cover_images' in request.files:
            files = request.files.getlist('cover_images')
            for file in files:
                if file.filename:
                    filename = save_uploaded_file(file)
                    if filename:
                        cover_images_list.append(filename)
                        if not cover_image:
                            cover_image = filename  # 第一张作为封面
        
        # 处理多图片JSON
        import json
        cover_images_json = json.dumps(cover_images_list) if cover_images_list else None
        
        if not title or not listing_price:
            flash('请填写书籍名称和价格', 'danger')
            return render_template('books/create.html')
        
        # 确定最终新旧程度（优先使用用户选择的，如果没有就用AI识别的）
        final_condition = condition if condition else ai_condition
        if not final_condition:
            final_condition = 'good'  # 默认值
        
        # 计算智能定价
        book_data = {
            'original_price': original_price,
            'condition': final_condition,
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
            condition=final_condition,
            category=category,
            description=description,
            listing_price=listing_price,
            smart_price=pricing_result['smart_price'],
            cover_image=cover_image,
            cover_images=cover_images_json,
            ai_condition=ai_condition,
            ai_analyzed=True if ai_condition else False,
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
