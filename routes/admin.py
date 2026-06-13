from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models.database import db, User, Consultation, Feedback
from flask_bcrypt import Bcrypt
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
bcrypt = Bcrypt()

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Search
    search_query = request.args.get('search', '')
    if search_query:
        search_term = f"%{search_query}%"
        all_users = User.query.filter(
            User.name.like(search_term) | User.email.like(search_term)
        ).order_by(User.created_at.desc()).all()
    else:
        all_users = User.query.order_by(User.created_at.desc()).all()

    # Analytics
    total_patients = User.query.filter_by(role='patient').count()
    total_doctors = User.query.filter_by(role='doctor').count()
    total_consultations = Consultation.query.count()
    
    # Feedback Analytics
    all_feedback = Feedback.query.order_by(Feedback.created_at.desc()).limit(10).all()
    avg_accuracy = db.session.query(db.func.avg(Feedback.accuracy_rating)).scalar() or 0
    avg_medication = db.session.query(db.func.avg(Feedback.medication_rating)).scalar() or 0
    avg_experience = db.session.query(db.func.avg(Feedback.experience_rating)).scalar() or 0
    
    return render_template('admin_dashboard.html',
                         total_patients=total_patients,
                         total_doctors=total_doctors,
                         total_consultations=total_consultations,
                         all_users=all_users,
                         search_query=search_query,
                         all_feedback=all_feedback,
                         avg_accuracy=round(avg_accuracy, 1),
                         avg_medication=round(avg_medication, 1),
                         avg_experience=round(avg_experience, 1))


@admin_bp.route('/create-doctor', methods=['POST'])
@login_required
@admin_required
def create_doctor():
    # (No changes to this route)
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    
    if not all([name, email, password]):
        flash('All fields required.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    if User.query.filter_by(email=email).first():
        flash('Email exists.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    doctor = User(name=name, email=email,
                  password_hash=bcrypt.generate_password_hash(password).decode('utf-8'),
                  role='doctor')
    try:
        db.session.add(doctor)
        db.session.commit()
        flash(f'Doctor {name} created.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/user/<int:user_id>/toggle_status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('Cannot change admin status.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = "activated" if user.is_active else "blocked"
    flash(f"User {user.name} has been {status}.", "success")
    return redirect(url_for('admin.dashboard'))