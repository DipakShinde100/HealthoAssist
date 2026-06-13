from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models.database import db, User, Consultation
from functools import wraps

doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor')

def doctor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role not in ['doctor', 'admin']:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@doctor_bp.route('/dashboard')
@login_required
@doctor_required
def dashboard():
    search_query = request.args.get('search', '')
    
    if search_query:
        search_term = f"%{search_query}%"
        patients = User.query.filter(
            User.role == 'patient',
            (User.name.like(search_term) | User.email.like(search_term))
        ).order_by(User.name).all()
    else:
        patients = User.query.filter_by(role='patient').order_by(User.name).all()
    
    pending = Consultation.query.filter_by(
        doctor_reviewed=False
    ).order_by(Consultation.consulted_at.desc()).limit(20).all()
    
    # Analytics
    total_patients = User.query.filter_by(role='patient').count()
    total_consultations = Consultation.query.count()
    
    disease_counts_query = db.session.query(
        Consultation.predicted_disease, 
        db.func.count(Consultation.predicted_disease)
    ).filter(Consultation.predicted_disease.isnot(None)).group_by(Consultation.predicted_disease).order_by(db.func.count(Consultation.predicted_disease).desc()).limit(5).all()

    # Convert the list of Row objects to a simple list of lists
    disease_counts = [[disease, count] for disease, count in disease_counts_query]
    
    return render_template('doctor_dashboard.html',
                         patients=patients,
                         pending_reviews=pending,
                         total_patients=total_patients,
                         total_consultations=total_consultations,
                         disease_counts=disease_counts,
                         search_query=search_query)
@doctor_bp.route('/patient/<int:patient_id>')
@login_required
@doctor_required
def view_patient(patient_id):
    patient = User.query.get_or_404(patient_id)
    consultations = Consultation.query.filter_by(
        patient_id=patient_id
    ).order_by(Consultation.consulted_at.desc()).all()
    
    return render_template('doctor_patient_view.html',
                         patient=patient,
                         consultations=consultations)


@doctor_bp.route('/consultation/<int:consultation_id>/review', methods=['POST'])
@login_required
@doctor_required
def review_consultation(consultation_id):
    c = Consultation.query.get_or_404(consultation_id)
    c.doctor_reviewed = True
    c.doctor_id = current_user.id
    c.doctor_note = request.form.get('doctor_note', '')
    c.prescription = request.form.get('prescription', '')
    
    try:
        db.session.commit()
        flash('Review submitted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('doctor.view_patient', patient_id=c.patient_id))