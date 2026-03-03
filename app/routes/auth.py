"""
认证路由 - 用户注册、登录
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.models import db, User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone')
        student_id = request.form.get('student_id')
        
        # 验证
        if not username or not email or not password:
            flash('请填写所有必填项', 'danger')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('两次密码输入不一致', 'danger')
            return render_template('auth/register.html')
        
        # 检查用户是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已被使用', 'danger')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'danger')
            return render_template('auth/register.html')
        
        # 创建用户
        user = User(
            username=username,
            email=email,
            phone=phone,
            student_id=student_id
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功！请登录', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f'欢迎回来，{user.username}！', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        else:
            flash('用户名或密码错误', 'danger')
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """退出登录"""
    logout_user()
    flash('已退出登录', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile')
@login_required
def profile():
    """用户资料"""
    return render_template('auth/profile.html')


@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """编辑资料"""
    if request.method == 'POST':
        current_user.phone = request.form.get('phone')
        current_user.student_id = request.form.get('student_id')
        
        new_password = request.form.get('new_password')
        if new_password:
            current_user.set_password(new_password)
        
        db.session.commit()
        flash('资料已更新', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/edit_profile.html')
