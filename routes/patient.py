"""
HealthoAssist - Patient Routes
Dashboard, symptom prediction, history, profile management
"""
from models.database import db, User, Consultation, Feedback
from services.chatbot import HealthoChatbot
import os
from flask import send_file
from services.report_generator import PDFReportGenerator
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from models.database import db, User, Consultation
from services.predictor import DiseasePredictor
from services.recommender import RecommendationEngine
from services.safety import SafetyChecker
import json
from datetime import datetime
from functools import wraps

patient_bp = Blueprint('patient', __name__)

def patient_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@patient_bp.route('/dashboard')
@login_required
def dashboard():
    # Get recent consultations
    recent_consultations = Consultation.query.filter_by(
        patient_id=current_user.id
    ).order_by(Consultation.consulted_at.desc()).limit(5).all()
    
    total_consultations = Consultation.query.filter_by(patient_id=current_user.id).count()
    
    return render_template('dashboard.html',
                         recent_consultations=recent_consultations,
                         total_consultations=total_consultations)


@patient_bp.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    predictor = current_app.config.get('PREDICTOR')
    recommender = current_app.config.get('RECOMMENDER')
    
    if not predictor:
        flash('Prediction service is not available. Please contact admin.', 'danger')
        return redirect(url_for('patient.dashboard'))
    
    # Get all symptoms for the dropdown
    all_symptoms = predictor.get_all_symptoms()
    
    if request.method == 'POST':
        # Get selected symptoms
        selected_symptoms = request.form.getlist('symptoms')
        
        if not selected_symptoms:
            flash('Please select at least 3 symptoms.', 'warning')
            return render_template('predict.html', symptoms=all_symptoms)
        
        if len(selected_symptoms) < 3:
            flash('Please select at least 3 symptoms for accurate prediction.', 'warning')
            return render_template('predict.html', symptoms=all_symptoms,
                                 selected=selected_symptoms)
        
        # Get prediction
        result = predictor.predict(
            selected_symptoms,
            confidence_threshold=current_app.config.get('CONFIDENCE_THRESHOLD', 0.40)
        )
        
        if result.get('error') and not result.get('predicted_disease'):
            flash(result['error'], 'danger')
            return render_template('predict.html', symptoms=all_symptoms,
                                 selected=selected_symptoms)
        
        # Get recommendations if not referral
        recommendations = {}
        safety_result = {'warnings': [], 'has_warnings': False}
        
        if not result['referral_flag'] and recommender:
            recommendations = recommender.get_recommendations(result['predicted_disease'])
            
            # Safety check
            if recommendations.get('medications'):
                safety_result = SafetyChecker.perform_safety_check(
                    recommendations['medications'],
                    current_user.get_allergies_list(),
                    current_user.get_current_medications_list()
                )
        
        # Save consultation to database
        consultation = Consultation(
            patient_id=current_user.id,
            symptoms_input=json.dumps(selected_symptoms),
            predicted_disease=result['predicted_disease'],
            confidence_score=result['confidence'],
            top3_predictions=json.dumps(result['top3']),
            medications_recommended=json.dumps(recommendations.get('medications', [])),
            diet_recommended=json.dumps(recommendations.get('diet', [])),
            precautions_recommended=json.dumps(recommendations.get('precautions', [])),
            workout_recommended=json.dumps(recommendations.get('workout', [])),
            description=recommendations.get('description', ''),
            referral_flag=result['referral_flag'],
            safety_warnings=json.dumps(safety_result.get('warnings', []))
        )
        
        try:
            db.session.add(consultation)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error saving consultation: {e}")
        
        return render_template('results.html',
                             prediction=result,
                             recommendations=recommendations,
                             safety=safety_result,
                             consultation=consultation,
                             selected_symptoms=selected_symptoms)
    
    return render_template('predict.html', symptoms=all_symptoms)


@patient_bp.route('/history')
@login_required
def history():
    page = request.args.get('page', 1, type=int)
    consultations = Consultation.query.filter_by(
        patient_id=current_user.id
    ).order_by(
        Consultation.consulted_at.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template('history.html', consultations=consultations)


@patient_bp.route('/consultation/<int:consultation_id>')
@login_required
def view_consultation(consultation_id):
    consultation = Consultation.query.get_or_404(consultation_id)
    
    # Security: only the patient or their doctor can view
    if consultation.patient_id != current_user.id and current_user.role not in ['doctor', 'admin']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('patient.dashboard'))
    
    # Parse stored JSON data
    recommendations = {
        'description': consultation.description,
        'medications': consultation.get_medications_list(),
        'diet': json.loads(consultation.diet_recommended) if consultation.diet_recommended else [],
        'precautions': json.loads(consultation.precautions_recommended) if consultation.precautions_recommended else [],
        'workout': json.loads(consultation.workout_recommended) if consultation.workout_recommended else [],
    }
    
    prediction = {
        'predicted_disease': consultation.predicted_disease,
        'confidence': consultation.confidence_score,
        'confidence_pct': round((consultation.confidence_score or 0) * 100, 2),
        'top3': consultation.get_top3_list(),
        'referral_flag': consultation.referral_flag,
    }
    
    safety = {
        'warnings': consultation.get_safety_warnings_list(),
        'has_warnings': len(consultation.get_safety_warnings_list()) > 0
    }
    
    return render_template('results.html',
                         prediction=prediction,
                         recommendations=recommendations,
                         safety=safety,
                         consultation=consultation,
                         selected_symptoms=consultation.get_symptoms_list(),
                         is_history_view=True)


@patient_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.name = request.form.get('name', current_user.name)
        current_user.phone = request.form.get('phone', current_user.phone)
        current_user.blood_group = request.form.get('blood_group', current_user.blood_group)
        current_user.allergies = request.form.get('allergies', current_user.allergies)
        current_user.current_medications = request.form.get('current_medications', current_user.current_medications)
        current_user.chronic_conditions = request.form.get('chronic_conditions', current_user.chronic_conditions)
        
        dob = request.form.get('date_of_birth', '')
        if dob:
            try:
                current_user.date_of_birth = datetime.strptime(dob, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')
        
        return redirect(url_for('patient.profile'))
    
    return render_template('profile.html')


@patient_bp.route('/api/symptoms')
@login_required
def api_symptoms():
    """API endpoint for Select2 symptom search"""
    predictor = current_app.config.get('PREDICTOR')
    if predictor:
        query = request.args.get('q', '').lower()
        all_symptoms = predictor.get_all_symptoms()
        if query:
            filtered = [s for s in all_symptoms if query in s.lower()]
        else:
            filtered = all_symptoms
        return jsonify({'results': [{'id': s, 'text': s.title()} for s in filtered]})
    return jsonify({'results': []})
@patient_bp.route('/download-report/<int:consultation_id>')
@login_required
def download_report(consultation_id):
    consultation = Consultation.query.get_or_404(consultation_id)

    # Security check
    if consultation.patient_id != current_user.id and current_user.role not in ['doctor', 'admin']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('patient.dashboard'))

    # Build recommendations dict
    recommendations = {
        'description': consultation.description,
        'medications': consultation.get_medications_list(),
        'diet': json.loads(consultation.diet_recommended) if consultation.diet_recommended else [],
        'precautions': json.loads(consultation.precautions_recommended) if consultation.precautions_recommended else [],
        'workout': json.loads(consultation.workout_recommended) if consultation.workout_recommended else [],
    }

    # Build safety dict
    safety = {
        'warnings': consultation.get_safety_warnings_list(),
        'has_warnings': len(consultation.get_safety_warnings_list()) > 0
    }

    # Get patient history summary
    past_consultations = Consultation.query.filter_by(patient_id=current_user.id).order_by(Consultation.consulted_at.desc()).all()
    
    past_diseases = [c.predicted_disease for c in past_consultations if c.predicted_disease]
    
    most_frequent_disease = "N/A"
    if past_diseases:
        most_frequent_disease = max(set(past_diseases), key=past_diseases.count)

    history_summary = {
        'total_consultations': len(past_consultations),
        'past_diseases': list(set(past_diseases)),
        'most_frequent_disease': most_frequent_disease,
        'last_consultation_date': past_consultations[0].consulted_at.strftime('%d-%m-%Y %H:%M:%S') if past_consultations else 'N/A'
    }

    # Generate PDF
    report_generator = PDFReportGenerator()
    filename = f"HealthoAssist_Report_{consultation.id}.pdf"
    output_path = os.path.join("temp_" + filename)

    report_generator.generate_report(
        patient=current_user,
        consultation=consultation,
        recommendations=recommendations,
        safety=safety,
        history_summary=history_summary,
        output_path=output_path
    )

    return send_file(output_path, as_attachment=True, download_name=filename)
@patient_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    user_message = request.form.get('message', '')

    if not user_message.strip():
        return jsonify({'reply': 'Please type something!'})

    recommender = current_app.config.get('RECOMMENDER')
    chatbot = HealthoChatbot(recommender=recommender)

    # Get user history
    history = Consultation.query.filter_by(
        patient_id=current_user.id
    ).order_by(Consultation.consulted_at.desc()).limit(10).all()

    reply = chatbot.get_response(
        user_message=user_message,
        user=current_user,
        consultation_history=history
    )

    return jsonify({'reply': reply})
@patient_bp.route('/bmi-calculator')
@login_required
def bmi_calculator():
    return render_template('bmi_calculator.html')


@patient_bp.route('/emergency')
@login_required
def emergency():
    return render_template('emergency.html')


@patient_bp.route('/api/dashboard-stats')
@login_required
def dashboard_stats():
    consultations = Consultation.query.filter_by(
        patient_id=current_user.id
    ).order_by(Consultation.consulted_at.desc()).all()

    total = len(consultations)
    
    # Disease frequency
    disease_count = {}
    monthly_count = {}
    
    for c in consultations:
        # Count diseases
        if c.predicted_disease:
            disease_count[c.predicted_disease] = disease_count.get(c.predicted_disease, 0) + 1
        
        # Count by month
        month_key = c.consulted_at.strftime('%b %Y')
        monthly_count[month_key] = monthly_count.get(month_key, 0) + 1
    
    # Health score calculation
    health_score = calculate_health_score(consultations, current_user)
    
    # Most common disease
    most_common = max(disease_count, key=disease_count.get) if disease_count else "None"
    
    # Average confidence
    confidences = [c.confidence_score for c in consultations if c.confidence_score]
    avg_confidence = round(sum(confidences) / len(confidences) * 100, 1) if confidences else 0
    
    # Doctor reviewed percentage
    reviewed = sum(1 for c in consultations if c.doctor_reviewed)
    review_pct = round(reviewed / total * 100, 1) if total > 0 else 0
    
    return jsonify({
        'total_consultations': total,
        'disease_frequency': disease_count,
        'monthly_consultations': monthly_count,
        'health_score': health_score,
        'most_common_disease': most_common,
        'avg_confidence': avg_confidence,
        'doctor_review_percentage': review_pct,
        'total_diseases': len(disease_count)
    })


def calculate_health_score(consultations, user):
    score = 100
    
    if not consultations:
        return score
    
    # Deduct for number of consultations (more = lower score)
    if len(consultations) > 10:
        score -= 10
    elif len(consultations) > 5:
        score -= 5
    
    # Deduct for repeated diseases
    diseases = [c.predicted_disease for c in consultations if c.predicted_disease]
    unique_diseases = set(diseases)
    
    for disease in unique_diseases:
        count = diseases.count(disease)
        if count > 2:
            score -= 5  # Repeated disease
    
    # Deduct for referrals
    referrals = sum(1 for c in consultations if c.referral_flag)
    score -= referrals * 3
    
    # Deduct for low confidence predictions
    low_conf = sum(1 for c in consultations if c.confidence_score and c.confidence_score < 0.5)
    score -= low_conf * 2
    
    # Bonus for doctor reviews
    reviewed = sum(1 for c in consultations if c.doctor_reviewed)
    score += reviewed * 2
    
    # Bonus for having profile filled
    if user.allergies:
        score += 3
    if user.blood_group:
        score += 2
    if user.phone:
        score += 2
    
    # Keep score between 0 and 100
    score = max(0, min(100, score))
    
    return score
@patient_bp.route('/consultation/<int:consultation_id>/feedback', methods=['POST'])
@login_required
def submit_feedback(consultation_id):
    consultation = Consultation.query.get_or_404(consultation_id)

    if consultation.patient_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('patient.history'))

    if consultation.feedback:
        flash('Feedback already submitted for this consultation.', 'warning')
        return redirect(url_for('patient.view_consultation', consultation_id=consultation.id))

    try:
        feedback = Feedback(
            patient_id=current_user.id,
            consultation_id=consultation.id,
            accuracy_rating=int(request.form.get('accuracy_rating', 0)),
            medication_rating=int(request.form.get('medication_rating', 0)),
            experience_rating=int(request.form.get('experience_rating', 0)),
            comments=request.form.get('comments', '').strip()
        )
        db.session.add(feedback)
        db.session.commit()
        flash('Thank you for your feedback!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error submitting feedback.', 'danger')

    return redirect(url_for('patient.view_consultation', consultation_id=consultation.id))
@patient_bp.route('/hospital-finder')
@login_required
def hospital_finder():
    return render_template('hospital_finder.html')