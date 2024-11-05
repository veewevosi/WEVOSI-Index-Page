from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User
from app import db
from utils.mail import send_verification_email
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            if not user.email_verified:
                flash('Please verify your email address first.')
                return redirect(url_for('auth.login'))
            login_user(user)
            return redirect(url_for('main.account'))
        flash('Invalid email or password')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return redirect(url_for('auth.register'))
        
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        # Generate verification token
        verification_token = new_user.generate_verification_token()
        
        db.session.add(new_user)
        db.session.commit()
        
        # Generate verification URL
        verification_url = url_for('auth.verify_email', 
                                 token=verification_token,
                                 _external=True)
        
        # Send verification email
        if send_verification_email(new_user, verification_url):
            flash('Registration successful! Please check your email to verify your account.')
        else:
            flash('Registration successful but failed to send verification email. Please contact support.')
            
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    
    if not user:
        flash('Invalid or expired verification link')
        return redirect(url_for('auth.login'))
    
    user.email_verified = True
    user.is_active = True
    user.verification_token = None
    db.session.commit()
    
    flash('Email verified successfully! You can now login.')
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
