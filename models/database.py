from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='patient')  # patient, doctor, admin
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    gender = db.Column(db.String(10))
    date_of_birth = db.Column(db.Date)
    blood_group = db.Column(db.String(5))
    phone = db.Column(db.String(15))
    allergies = db.Column(db.Text)  # Comma-separated allergy list
    current_medications = db.Column(db.Text)  # Comma-separated current meds
    chronic_conditions = db.Column(db.Text)  # Comma-separated conditions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    consultations = db.relationship('Consultation', backref='patient', lazy=True,
                                     foreign_keys='Consultation.patient_id')
    
    def get_allergies_list(self):
        if self.allergies:
            return [a.strip().lower() for a in self.allergies.split(',') if a.strip()]
        return []
    
    def get_current_medications_list(self):
        if self.current_medications:
            return [m.strip().lower() for m in self.current_medications.split(',') if m.strip()]
        return []
    
    def get_chronic_conditions_list(self):
        if self.chronic_conditions:
            return [c.strip().lower() for c in self.chronic_conditions.split(',') if c.strip()]
        return []


class Consultation(db.Model):
    __tablename__ = 'consultations'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symptoms_input = db.Column(db.Text, nullable=False)  # JSON list of symptoms
    predicted_disease = db.Column(db.String(100))
    confidence_score = db.Column(db.Float)
    top3_predictions = db.Column(db.Text)  # JSON: [{"disease": "...", "confidence": 0.9}, ...]
    medications_recommended = db.Column(db.Text)  # JSON list
    diet_recommended = db.Column(db.Text)
    precautions_recommended = db.Column(db.Text)
    workout_recommended = db.Column(db.Text)
    description = db.Column(db.Text)
    referral_flag = db.Column(db.Boolean, default=False)
    safety_warnings = db.Column(db.Text)  # JSON list of warnings
    doctor_reviewed = db.Column(db.Boolean, default=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    doctor_note = db.Column(db.Text)
    prescription = db.Column(db.Text)
    consulted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship for doctor
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='reviewed_consultations')
        # This line connects Consultation to its ONE Feedback
    feedback = db.relationship('Feedback', backref='consultation', uselist=False, lazy='joined')
    
    def get_symptoms_list(self):
        try:
            return json.loads(self.symptoms_input)
        except:
            return []
    
    def get_top3_list(self):
        try:
            return json.loads(self.top3_predictions)
        except:
            return []
    
    def get_medications_list(self):
        try:
            return json.loads(self.medications_recommended)
        except:
            return []
    
    def get_safety_warnings_list(self):
        try:
            return json.loads(self.safety_warnings) if self.safety_warnings else []
        except:
            return []


class Disease(db.Model):
    __tablename__ = 'diseases'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # infectious, metabolic, etc.
    
    medications = db.relationship('Medication', backref='disease', lazy=True)
    diets = db.relationship('Diet', backref='disease', lazy=True)
    precautions = db.relationship('Precaution', backref='disease', lazy=True)
    workouts = db.relationship('Workout', backref='disease', lazy=True)


class Symptom(db.Model):
    __tablename__ = 'symptoms'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    feature_index = db.Column(db.Integer)  # Index in the 132-dim feature vector


class Medication(db.Model):
    __tablename__ = 'medications'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    disease_id = db.Column(db.Integer, db.ForeignKey('diseases.id'), nullable=False)
    drug_name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(100))
    contraindications = db.Column(db.Text)  # Comma-separated
    side_effects = db.Column(db.Text)


class Diet(db.Model):
    __tablename__ = 'diets'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    disease_id = db.Column(db.Integer, db.ForeignKey('diseases.id'), nullable=False)
    recommended_foods = db.Column(db.Text)
    foods_to_avoid = db.Column(db.Text)


class Precaution(db.Model):
    __tablename__ = 'precautions'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    disease_id = db.Column(db.Integer, db.ForeignKey('diseases.id'), nullable=False)
    precaution_1 = db.Column(db.String(200))
    precaution_2 = db.Column(db.String(200))
    precaution_3 = db.Column(db.String(200))
    precaution_4 = db.Column(db.String(200))


class Workout(db.Model):
    __tablename__ = 'workouts'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    disease_id = db.Column(db.Integer, db.ForeignKey('diseases.id'), nullable=False)
    workout_recommendation = db.Column(db.Text)
class Feedback(db.Model):
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    consultation_id = db.Column(db.Integer, db.ForeignKey('consultations.id'), nullable=False)
    
    accuracy_rating = db.Column(db.Integer)  # 1-5
    medication_rating = db.Column(db.Integer) # 1-5
    experience_rating = db.Column(db.Integer) # 1-5
    
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('User', backref='feedbacks')
    