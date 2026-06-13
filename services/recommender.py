"""
HealthoAssist - Recommendation Engine
Fetches medications, diet, precautions, and workouts for predicted diseases
"""

import pandas as pd
import os
import ast

class RecommendationEngine:
    def __init__(self, data_dir=None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        
        self.data_dir = data_dir
        self.descriptions = {}
        self.medications = {}
        self.diets = {}
        self.precautions = {}
        self.workouts = {}
        
        self._load_data()
    
    def _safe_eval(self, val):
        """Safely evaluate string representations of lists"""
        if pd.isna(val) or val == '' or val is None:
            return []
        try:
            result = ast.literal_eval(str(val))
            if isinstance(result, list):
                return result
            return [str(result)]
        except:
            return [str(val)]
    
    def _load_data(self):
        """Load all recommendation data from CSV files"""
        
        # Load descriptions
        desc_path = os.path.join(self.data_dir, 'description.csv')
        if os.path.exists(desc_path):
            df = pd.read_csv(desc_path)
            for _, row in df.iterrows():
                disease = str(row.iloc[0]).strip()
                desc = str(row.iloc[1]).strip() if len(row) > 1 else ''
                self.descriptions[disease.lower()] = desc
            print(f"Loaded {len(self.descriptions)} disease descriptions")
        
        # Load medications
        med_path = os.path.join(self.data_dir, 'medications.csv')
        if os.path.exists(med_path):
            df = pd.read_csv(med_path)
            for _, row in df.iterrows():
                disease = str(row.iloc[0]).strip()
                meds = self._safe_eval(row.iloc[1]) if len(row) > 1 else []
                self.medications[disease.lower()] = meds
            print(f"Loaded medications for {len(self.medications)} diseases")
        
        # Load diets
        diet_path = os.path.join(self.data_dir, 'diets.csv')
        if os.path.exists(diet_path):
            df = pd.read_csv(diet_path)
            for _, row in df.iterrows():
                disease = str(row.iloc[0]).strip()
                diet = self._safe_eval(row.iloc[1]) if len(row) > 1 else []
                self.diets[disease.lower()] = diet
            print(f"Loaded diets for {len(self.diets)} diseases")
        
        # Load precautions
        prec_path = os.path.join(self.data_dir, 'precautions_df.csv')
        if os.path.exists(prec_path):
            df = pd.read_csv(prec_path)
            for _, row in df.iterrows():
                disease = str(row.iloc[0]).strip()
                precs = []
                for i in range(1, min(5, len(row))):
                    if pd.notna(row.iloc[i]) and str(row.iloc[i]).strip():
                        precs.append(str(row.iloc[i]).strip())
                self.precautions[disease.lower()] = precs
            print(f"Loaded precautions for {len(self.precautions)} diseases")
        
        # Load workouts
        workout_path = os.path.join(self.data_dir, 'workout_df.csv')
        if os.path.exists(workout_path):
            df = pd.read_csv(workout_path)
            for _, row in df.iterrows():
                disease = str(row.iloc[0]).strip().lower()
                workout = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ''
                if disease in self.workouts:
                    self.workouts[disease].append(workout)
                else:
                    self.workouts[disease] = [workout]
            print(f"Loaded workouts for {len(self.workouts)} diseases")
    
    def _find_disease_key(self, disease_name):
        """Find the matching key in our data dictionaries"""
        disease_lower = disease_name.strip().lower()
        
        # Direct match
        if disease_lower in self.descriptions:
            return disease_lower
        
        # Partial match
        for key in self.descriptions.keys():
            if disease_lower in key or key in disease_lower:
                return key
        
        # Try without parentheses
        clean = disease_lower.split('(')[0].strip()
        for key in self.descriptions.keys():
            if clean in key or key in clean:
                return key
        
        return disease_lower
    
    def get_recommendations(self, disease_name):
        """
        Get all recommendations for a predicted disease.
        
        Returns dict with: description, medications, diet, precautions, workout
        """
        key = self._find_disease_key(disease_name)
        
        result = {
            'disease': disease_name,
            'description': self.descriptions.get(key, 'No description available.'),
            'medications': self.medications.get(key, []),
            'diet': self.diets.get(key, []),
            'precautions': self.precautions.get(key, []),
            'workout': self.workouts.get(key, []),
        }
        
        return result