"""
HealthoAssist - SVM Model Training Script
Trains the SVC classifier on the disease-symptom dataset and exports svc.pkl
"""

import pandas as pd
import numpy as np
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import os
import json

def train_model():
    print("=" * 60)
    print("HealthoAssist - SVM Model Training")
    print("=" * 60)
    
    # Load dataset
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    training_path = os.path.join(data_dir, 'Training.csv')
    
    if not os.path.exists(training_path):
        print(f"ERROR: Training.csv not found at {training_path}")
        print("Please download the dataset from:")
        print("https://www.kaggle.com/datasets/itachi9604/disease-symptom-description-dataset")
        return
    
    df = pd.read_csv(training_path)
    print(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    
    # Drop the last column if it's unnamed/null (common in this dataset)
    if df.columns[-1].startswith('Unnamed'):
        df = df.drop(columns=[df.columns[-1]])
    
    # Separate features and target
    X = df.drop('prognosis', axis=1)
    y = df['prognosis']
    
    # Get symptom columns (feature names)
    symptom_columns = list(X.columns)
    print(f"Number of symptom features: {len(symptom_columns)}")
    print(f"Number of diseases: {y.nunique()}")
    print(f"Diseases: {sorted(y.unique())}")
    
    # Encode labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    
    # Train-test split (80/20 stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )
    print(f"\nTrain set: {X_train.shape[0]} samples")
    print(f"Test set: {X_test.shape[0]} samples")
    
    # Train SVM with RBF kernel
    print("\nTraining SVM (RBF kernel)...")
    svm_model = SVC(kernel='rbf', C=10, gamma='scale', random_state=42)
    svm_model.fit(X_train, y_train)
    
    # Calibrate for probability estimates
    print("Calibrating probabilities...")
    calibrated_svm = CalibratedClassifierCV(svm_model, cv=5, method='sigmoid')
    calibrated_svm.fit(X_train, y_train)
    
    # Evaluate
    y_pred_train = calibrated_svm.predict(X_train)
    y_pred_test = calibrated_svm.predict(X_test)
    
    train_acc = accuracy_score(y_train, y_pred_train) * 100
    test_acc = accuracy_score(y_test, y_pred_test) * 100
    
    print(f"\nTrain Accuracy: {train_acc:.2f}%")
    print(f"Test Accuracy:  {test_acc:.2f}%")
    
    # Cross-validation
    cv_scores = cross_val_score(svm_model, X, y_encoded, cv=5, scoring='accuracy')
    print(f"Cross-Val Accuracy: {cv_scores.mean()*100:.2f}% (+/- {cv_scores.std()*100:.2f}%)")
    
    # Classification report
    print("\nClassification Report (Test Set):")
    print(classification_report(y_test, y_pred_test, target_names=le.classes_))
    
    # Compare with other models
    print("\n" + "=" * 60)
    print("Comparison with Other Models")
    print("=" * 60)
    
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.naive_bayes import GaussianNB
    from sklearn.neighbors import KNeighborsClassifier
    
    models = {
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
        'Decision Tree': DecisionTreeClassifier(random_state=42),
        'Naive Bayes': GaussianNB(),
        'KNN': KNeighborsClassifier(n_neighbors=5)
    }
    
    for name, model in models.items():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        acc = accuracy_score(y_test, pred) * 100
        print(f"{name}: {acc:.2f}%")
    
    # Save model and metadata
    model_data = {
        'model': calibrated_svm,
        'label_encoder': le,
        'symptom_columns': symptom_columns,
        'diseases': list(le.classes_),
        'train_accuracy': train_acc,
        'test_accuracy': test_acc
    }
    
    model_path = os.path.join(os.path.dirname(__file__), 'svc.pkl')
    joblib.dump(model_data, model_path)
    print(f"\nModel saved to {model_path}")
    
    # Save symptom list for reference
    symptom_list_path = os.path.join(data_dir, 'symptom_list.json')
    with open(symptom_list_path, 'w') as f:
        # Clean symptom names (replace underscores with spaces)
        clean_symptoms = [s.replace('_', ' ').strip() for s in symptom_columns]
        json.dump({
            'symptoms': clean_symptoms,
            'symptom_to_index': {s.replace('_', ' ').strip(): i for i, s in enumerate(symptom_columns)},
            'raw_columns': symptom_columns
        }, f, indent=2)
    print(f"Symptom list saved to {symptom_list_path}")
    
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)

if __name__ == '__main__':
    train_model()