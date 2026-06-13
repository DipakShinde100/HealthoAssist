"""
HealthoAssist - Authentication Module
Handles registration, login, logout, and session management
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models.database import db, User
from datetime import datetime

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('patient.dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        gender = request.form.get('gender', '')
        dob = request.form.get('date_of_birth', '')
        blood_group = request.form.get('blood_group', '')
        phone = request.form.get('phone', '')
        allergies = request.form.get('allergies', '')
        
        # Validation
        errors = []
        if not name:
            errors.append('Name is required.')
        if not email:
            errors.append('Email is required.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        # Check if email exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            errors.append('Email already registered. Please login.')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html')
        
        # Create user
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        new_user = User(
            name=name,
            email=email,
            password_hash=password_hash,
            role='patient',
            gender=gender,
            date_of_birth=datetime.strptime(dob, '%Y-%m-%d').date() if dob else None,
            blood_group=blood_group,
            phone=phone,
            allergies=allergies
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')
    
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        elif current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('patient.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            flash(f'Welcome back, {user.name}!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            if user.role == 'doctor':
                return redirect(url_for('doctor.dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('patient.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))