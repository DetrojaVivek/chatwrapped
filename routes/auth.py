import secrets
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from database.models import User, PasswordReset
from extensions import db, bcrypt, mail

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'GET':
        return render_template('auth/signup.html')
    
    name     = request.form.get('name','').strip()
    email    = request.form.get('email','').strip().lower()
    password = request.form.get('password','')
    confirm  = request.form.get('confirm_password','')
    
    if not name or not email or not password:
        flash('Sare fields bharo!', 'error')
        return render_template('auth/signup.html')
    
    if len(password) < 8:
        flash('Password kam se kam 8 characters ka hona chahiye!', 'error')
        return render_template('auth/signup.html')
    
    if password != confirm:
        flash('Passwords match nahi kar rahe!', 'error')
        return render_template('auth/signup.html')
    
    if User.query.filter_by(email=email).first():
        flash('Ye email already registered hai!', 'error')
        return render_template('auth/signup.html')
    
    hashed_pwd = bcrypt.generate_password_hash(password).decode('utf-8')
    user = User(name=name, email=email, password_hash=hashed_pwd)
    db.session.add(user)
    db.session.commit()
    
    # Send verification email (optional - skip if MAIL not configured)
    try:
        token = secrets.token_urlsafe(32)
        # Store token (simple approach: use password_resets table)
        pr = PasswordReset(user_id=user.id, token='verify_'+token, 
                          expires_at=datetime.utcnow()+timedelta(days=7))
        db.session.add(pr)
        db.session.commit()
        verify_url = url_for('auth.verify_email', token=token, _external=True)
        msg = Message('ChatWrapped - Email Verify Karo',
                     sender='noreply@chatwrapped.in',
                     recipients=[email])
        msg.body = f'Email verify karne ke liye ye link open karo: {verify_url}'
        mail.send(msg)
    except:
        pass  # Mail fail hone pe bhi signup kaam karega
    
    flash('Account ban gaya! Ab login karo.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    email    = request.form.get('email','').strip().lower()
    password = request.form.get('password','')
    remember = 'remember_me' in request.form
    
    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password_hash, password):
        login_user(user, remember=remember)
        next_page = request.args.get('next')
        flash(f'Welcome back, {user.name}!', 'success')
        return redirect(next_page or url_for('dashboard.index'))
    
    flash('Email ya password galat hai!', 'error')
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout ho gaye!', 'success')
    return redirect(url_for('upload.handle_upload'))

@auth_bp.route('/forgot-password', methods=['GET','POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('auth/forgot-password.html')
    
    email = request.form.get('email','').strip().lower()
    user  = User.query.filter_by(email=email).first()
    
    if user:
        token = secrets.token_urlsafe(32)
        pr = PasswordReset(user_id=user.id, token=token,
                          expires_at=datetime.utcnow()+timedelta(hours=1))
        db.session.add(pr)
        db.session.commit()
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        try:
            msg = Message('ChatWrapped - Password Reset',
                         sender='noreply@chatwrapped.in',
                         recipients=[email])
            msg.body = f'Password reset link: {reset_url} (1 ghante mein expire hoga)'
            mail.send(msg)
        except: pass
    
    flash('Agar ye email registered hai, reset link bhej diya gaya hai!', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset-password', methods=['GET','POST'])
def reset_password():
    token = request.args.get('token','')
    pr    = PasswordReset.query.filter_by(token=token, used=False).first()
    if not pr or pr.expires_at < datetime.utcnow():
        flash('Reset link expire ho gaya ya invalid hai!', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'GET':
        return render_template('auth/reset-password.html', token=token)
    
    new_pwd = request.form.get('password','')
    if len(new_pwd) < 8:
        flash('Password kam se kam 8 characters ka hona chahiye!', 'error')
        return render_template('auth/reset-password.html', token=token)
    
    user = User.query.get(pr.user_id)
    user.password_hash = bcrypt.generate_password_hash(new_pwd).decode('utf-8')
    pr.used = True
    db.session.commit()
    flash('Password update ho gaya! Ab login karo.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/verify-email')
def verify_email():
    token = request.args.get('token','')
    pr    = PasswordReset.query.filter_by(token='verify_'+token, used=False).first()
    if pr:
        user = User.query.get(pr.user_id)
        user.is_verified = True
        pr.used = True
        db.session.commit()
        flash('Email verify ho gaya!', 'success')
    return redirect(url_for('auth.login'))
