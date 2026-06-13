"""
HealthoAssist - Database Seeding Script
Seeds the MySQL database with disease, symptom, medication, diet, and precaution data from CSV files
"""

import os
import sys
import pandas as pd
import ast

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from models.database import db, Disease, Symptom, Medication, Diet, Precaution, Workout

def seed_database():
    app = create_app()
    data_dir = app.config.get('DATA_DIR', os.path.join(os.path.dirname(__file__), 'data'))
    
    with app.app_context():
        print("Seeding database...")
        
        # 1. Seed diseases from description.csv
        desc_path = os.path.join(data_dir, 'description.csv')
        if os.path.exists(desc_path):
            df = pd.read_csv(desc_path)
            for _, row in df.iterrows():
                name = str(row.iloc[0]).strip()
                desc = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ''
                
                existing = Disease.query.filter_by(name=name).first()
                if not existing:
                    disease = Disease(name=name, description=desc)
                    db.session.add(disease)
            db.session.commit()
            print(f"  Diseases seeded: {Disease.query.count()}")
        
        # 2. Seed symptoms from Training.csv columns
        training_path = os.path.join(data_dir, 'Training.csv')
        if os.path.exists(training_path):
            df = pd.read_csv(training_path)
            cols = [c for c in df.columns if c != 'prognosis' and not c.startswith('Unnamed')]
            for i, col in enumerate(cols):
                clean_name = col.replace('_', ' ').strip()
                existing = Symptom.query.filter_by(name=clean_name).first()
                if not existing:
                    symptom = Symptom(name=clean_name, feature_index=i)
                    db.session.add(symptom)
            db.session.commit()
            print(f"  Symptoms seeded: {Symptom.query.count()}")
        
        # 3. Seed medications
        med_path = os.path.join(data_dir, 'medications.csv')
        if os.path.exists(med_path):
            df = pd.read_csv(med_path)
            for _, row in df.iterrows():
                disease_name = str(row.iloc[0]).strip()
                disease = Disease.query.filter_by(name=disease_name).first()
                if disease:
                    try:
                        meds = ast.literal_eval(str(row.iloc[1]))
                        if isinstance(meds, list):
                            for med_name in meds:
                                existing = Medication.query.filter_by(
                                    disease_id=disease.id, drug_name=str(med_name).strip()
                                ).first()
                                if not existing:
                                    medication = Medication(
                                        disease_id=disease.id,
                                        drug_name=str(med_name).strip()
                                    )
                                    db.session.add(medication)
                    except:
                        pass
            db.session.commit()
            print(f"  Medications seeded: {Medication.query.count()}")
        
        # 4. Seed diets
        diet_path = os.path.join(data_dir, 'diets.csv')
        if os.path.exists(diet_path):
            df = pd.read_csv(diet_path)
            for _, row in df.iterrows():
                disease_name = str(row.iloc[0]).strip()
                disease = Disease.query.filter_by(name=disease_name).first()
                if disease:
                    try:
                        diet_items = ast.literal_eval(str(row.iloc[1]))
                        diet_str = ', '.join(diet_items) if isinstance(diet_items, list) else str(diet_items)
                    except:
                        diet_str = str(row.iloc[1])
                    
                    existing = Diet.query.filter_by(disease_id=disease.id).first()
                    if not existing:
                        diet = Diet(disease_id=disease.id, recommended_foods=diet_str)
                        db.session.add(diet)
            db.session.commit()
            print(f"  Diets seeded: {Diet.query.count()}")
        
        # 5. Seed precautions
        prec_path = os.path.join(data_dir, 'precautions_df.csv')
        if os.path.exists(prec_path):
            df = pd.read_csv(prec_path)
            for _, row in df.iterrows():
                disease_name = str(row.iloc[0]).strip()
                disease = Disease.query.filter_by(name=disease_name).first()
                if disease:
                    existing = Precaution.query.filter_by(disease_id=disease.id).first()
                    if not existing:
                        prec = Precaution(
                            disease_id=disease.id,
                            precaution_1=str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else None,
                            precaution_2=str(row.iloc[2]).strip() if len(row) > 2 and pd.notna(row.iloc[2]) else None,
                            precaution_3=str(row.iloc[3]).strip() if len(row) > 3 and pd.notna(row.iloc[3]) else None,
                            precaution_4=str(row.iloc[4]).strip() if len(row) > 4 and pd.notna(row.iloc[4]) else None,
                        )
                        db.session.add(prec)
            db.session.commit()
            print(f"  Precautions seeded: {Precaution.query.count()}")
        
        # 6. Seed workouts
        workout_path = os.path.join(data_dir, 'workout_df.csv')
        if os.path.exists(workout_path):
            df = pd.read_csv(workout_path)
            added_pairs = set()
            for _, row in df.iterrows():
                disease_name = str(row.iloc[0]).strip()
                workout_text = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ''
                disease = Disease.query.filter_by(name=disease_name).first()
                if disease and workout_text:
                    pair_key = (disease.id, workout_text)
                    if pair_key not in added_pairs:
                        workout = Workout(disease_id=disease.id, workout_recommendation=workout_text)
                        db.session.add(workout)
                        added_pairs.add(pair_key)
            db.session.commit()
            print(f"  Workouts seeded: {Workout.query.count()}")
        
        print("\nDatabase seeding complete!")

if __name__ == '__main__':
    seed_database()