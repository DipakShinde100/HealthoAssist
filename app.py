import os
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect

from config import DevelopmentConfig
from models.database import db, User
from routes.auth import auth_bp
from routes.patient import patient_bp
from routes.doctor import doctor_bp
from routes.admin import admin_bp
from services.predictor import DiseasePredictor
from services.recommender import RecommendationEngine


def create_app():
    app = Flask(__name__)
    app.config.from_object(DevelopmentConfig)

    db.init_app(app)
    bcrypt = Bcrypt(app)
    csrf = CSRFProtect(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()

        app.config['PREDICTOR'] = DiseasePredictor(
            model_path=app.config.get('MODEL_PATH'),
            data_dir=app.config.get('DATA_DIR')
        )
        app.config['RECOMMENDER'] = RecommendationEngine(
            data_dir=app.config.get('DATA_DIR')
        )

        if not User.query.filter_by(role='admin').first():
            try:
                admin = User(
                    name='Admin',
                    email='admin@healthoassist.com',
                    password_hash=bcrypt.generate_password_hash('admin123').decode('utf-8'),
                    role='admin'
                )
                doctor = User(
                    name='Dr. Demo',
                    email='doctor@healthoassist.com',
                    password_hash=bcrypt.generate_password_hash('doctor123').decode('utf-8'),
                    role='doctor'
                )
                db.session.add(admin)
                db.session.add(doctor)
                db.session.commit()
                print("Default accounts created:")
                print("  Admin: admin@healthoassist.com / admin123")
                print("  Doctor: doctor@healthoassist.com / doctor123")
            except Exception as e:
                db.session.rollback()
                print(f"Could not create default users: {e}")

    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(admin_bp)

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'doctor':
                return redirect(url_for('doctor.dashboard'))
            elif current_user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('patient.dashboard'))
        return render_template('home.html')

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('error.html', error_code=403, error_message='Access Forbidden'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('error.html', error_code=404, error_message='Page Not Found'), 404

    return app


print("Starting HealthoAssist...")
app = create_app()

if __name__ == '__main__':
    print("Server starting on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)