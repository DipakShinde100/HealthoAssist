"""
HealthoAssist - SVM Disease Prediction Service
Loads the trained model and provides prediction functionality
"""

import joblib
import numpy as np
import os
import json

class DiseasePredictor:
    def __init__(self, model_path=None, data_dir=None):
        if model_path is None:
            model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'svc.pkl')
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        
        self.model_data = None
        self.model = None
        self.label_encoder = None
        self.symptom_columns = []
        self.symptom_index_map = {}
        self.diseases = []
        self.loaded = False
        
        self._load_model(model_path, data_dir)
    
    def _load_model(self, model_path, data_dir):
        """Load the trained SVM model and metadata"""
        try:
            if os.path.exists(model_path):
                self.model_data = joblib.load(model_path)
                self.model = self.model_data['model']
                self.label_encoder = self.model_data['label_encoder']
                self.symptom_columns = self.model_data['symptom_columns']
                self.diseases = self.model_data['diseases']
                
                # Build symptom-to-index mapping
                for i, col in enumerate(self.symptom_columns):
                    clean_name = col.replace('_', ' ').strip().lower()
                    self.symptom_index_map[clean_name] = i
                    # Also map with underscores
                    self.symptom_index_map[col.strip().lower()] = i
                
                self.loaded = True
                print(f"Model loaded successfully. {len(self.diseases)} diseases, {len(self.symptom_columns)} symptoms")
            else:
                print(f"WARNING: Model file not found at {model_path}")
                print("Please run train_model.py first")
                self._load_fallback(data_dir)
        except Exception as e:
            print(f"Error loading model: {e}")
            self._load_fallback(data_dir)
    
    def _load_fallback(self, data_dir):
        """Load symptom list from JSON if model isn't available"""
        symptom_list_path = os.path.join(data_dir, 'symptom_list.json')
        if os.path.exists(symptom_list_path):
            with open(symptom_list_path, 'r') as f:
                data = json.load(f)
                self.symptom_columns = data.get('raw_columns', [])
                self.symptom_index_map = {k.lower(): v for k, v in data.get('symptom_to_index', {}).items()}
    
    def get_all_symptoms(self):
        """Return list of all symptom names (cleaned)"""
        return [col.replace('_', ' ').strip() for col in self.symptom_columns]
    
    def normalize_symptom(self, symptom_text):
        """Normalize a symptom text to match the feature vector index"""
        normalized = symptom_text.strip().lower().replace('_', ' ')
        
        # Direct match
        if normalized in self.symptom_index_map:
            return self.symptom_index_map[normalized]
        
        # Try with underscores
        underscore_version = normalized.replace(' ', '_')
        if underscore_version in self.symptom_index_map:
            return self.symptom_index_map[underscore_version]
        
        # Fuzzy match - find closest
        for key, idx in self.symptom_index_map.items():
            if normalized in key or key in normalized:
                return idx
        
        return None
    
    def build_feature_vector(self, symptoms_list):
        """
        Build a 132-dimensional binary feature vector from symptom list.
        Returns numpy array of shape (1, num_features)
        """
        num_features = len(self.symptom_columns)
        vector = np.zeros(num_features)
        
        matched_symptoms = []
        unmatched_symptoms = []
        
        for symptom in symptoms_list:
            idx = self.normalize_symptom(symptom)
            if idx is not None and idx < num_features:
                vector[idx] = 1
                matched_symptoms.append(symptom)
            else:
                unmatched_symptoms.append(symptom)
        
        return vector.reshape(1, -1), matched_symptoms, unmatched_symptoms
    
    def predict(self, symptoms_list, confidence_threshold=0.40):
        """
        Predict disease from symptoms.
        
        Returns:
            dict with keys:
                - predicted_disease: str
                - confidence: float
                - top3: list of dicts
                - referral_flag: bool
                - matched_symptoms: list
                - unmatched_symptoms: list
        """
        if not self.loaded:
            return {
                'error': 'Model not loaded. Please run train_model.py first.',
                'predicted_disease': None,
                'confidence': 0,
                'top3': [],
                'referral_flag': True,
                'matched_symptoms': [],
                'unmatched_symptoms': symptoms_list
            }
        
        # Build feature vector
        feature_vector, matched, unmatched = self.build_feature_vector(symptoms_list)
        
        # Check minimum symptoms
        if len(matched) < 3:
            return {
                'error': f'Need at least 3 valid symptoms. Only {len(matched)} matched.',
                'predicted_disease': None,
                'confidence': 0,
                'top3': [],
                'referral_flag': True,
                'matched_symptoms': matched,
                'unmatched_symptoms': unmatched
            }
        
        # Get probability predictions
        probabilities = self.model.predict_proba(feature_vector)[0]
        
        # Get top-3 predictions
        top_indices = np.argsort(probabilities)[::-1][:3]
        top3 = []
        for idx in top_indices:
            disease_name = self.label_encoder.inverse_transform([idx])[0]
            confidence = float(probabilities[idx])
            top3.append({
                'disease': disease_name,
                'confidence': round(confidence, 4),
                'confidence_pct': round(confidence * 100, 2)
            })
        
        # Top prediction
        predicted_disease = top3[0]['disease']
        confidence = top3[0]['confidence']
        
        # Referral flag
        referral_flag = confidence < confidence_threshold
        
        return {
            'predicted_disease': predicted_disease,
            'confidence': confidence,
            'confidence_pct': round(confidence * 100, 2),
            'top3': top3,
            'referral_flag': referral_flag,
            'matched_symptoms': matched,
            'unmatched_symptoms': unmatched,
            'error': None
        }