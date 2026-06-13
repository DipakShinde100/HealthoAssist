"""
Converts Kaggle dataset.csv (Format 1: symptom names)
into Training.csv (Format 2: binary matrix)
"""

import pandas as pd
import os

def convert_dataset():
    # ============================================
    # STEP 1: Load your dataset.csv
    # ============================================
    input_file = os.path.join('data', 'dataset.csv')
    output_file = os.path.join('data', 'Training.csv')
    
    if not os.path.exists(input_file):
        print(f"ERROR: {input_file} not found!")
        print("Put your dataset.csv in the data/ folder")
        return
    
    df = pd.read_csv(input_file)
    print(f"Loaded dataset.csv: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"Columns: {list(df.columns)}")
    print(f"\nFirst 3 rows:")
    print(df.head(3))
    
    # ============================================
    # STEP 2: Detect format
    # ============================================
    
    # Check if it's already binary format
    first_col = df.columns[0].lower().strip()
    last_col = df.columns[-1].lower().strip()
    
    if last_col == 'prognosis' and df.iloc[0, 0] in [0, 1, '0', '1']:
        print("\n✅ File is ALREADY in binary format!")
        print("Just rename dataset.csv to Training.csv")
        df.to_csv(output_file, index=False)
        print(f"Saved to {output_file}")
        return
    
    # ============================================
    # STEP 3: Find disease column and symptom columns
    # ============================================
    
    # Try to find the disease/prognosis column
    disease_col = None
    possible_disease_cols = ['disease', 'prognosis', 'Disease', 'Prognosis', 
                              'disease_name', 'Disease_Name', 'diagnosis']
    
    for col in possible_disease_cols:
        if col in df.columns:
            disease_col = col
            break
    
    # If not found, check first or last column
    if disease_col is None:
        # Check if first column has disease names (string values)
        if df.iloc[:, 0].dtype == 'object':
            disease_col = df.columns[0]
        elif df.iloc[:, -1].dtype == 'object':
            disease_col = df.columns[-1]
    
    if disease_col is None:
        print("ERROR: Cannot find disease column!")
        print("Please check your CSV and tell me the column names")
        return
    
    print(f"\nDisease column found: '{disease_col}'")
    
    # ============================================
    # STEP 4: Get all symptom columns
    # ============================================
    symptom_cols = [col for col in df.columns if col != disease_col]
    print(f"Symptom columns: {symptom_cols}")
    
    # ============================================
    # STEP 5: Collect ALL unique symptoms
    # ============================================
    all_symptoms = set()
    
    for col in symptom_cols:
        symptoms_in_col = df[col].dropna().unique()
        for symptom in symptoms_in_col:
            s = str(symptom).strip().lower().replace(' ', '_')
            if s and s != 'nan' and s != '' and s != '0' and s != '0.0':
                all_symptoms.add(s)
    
    all_symptoms = sorted(list(all_symptoms))
    print(f"\nTotal unique symptoms found: {len(all_symptoms)}")
    print(f"Sample symptoms: {all_symptoms[:10]}")
    
    # ============================================
    # STEP 6: Create binary matrix
    # ============================================
    print("\nCreating binary feature matrix...")
    
    # Create empty dataframe with symptom columns
    binary_df = pd.DataFrame(0, 
                              index=range(len(df)), 
                              columns=all_symptoms)
    
    # Fill in 1s where symptoms exist
    for idx, row in df.iterrows():
        for col in symptom_cols:
            symptom_value = row[col]
            if pd.notna(symptom_value):
                s = str(symptom_value).strip().lower().replace(' ', '_')
                if s in all_symptoms:
                    binary_df.at[idx, s] = 1
    
    # Add disease column as 'prognosis'
    binary_df['prognosis'] = df[disease_col].values
    
    # ============================================
    # STEP 7: Clean and save
    # ============================================
    
    # Remove any rows where no symptoms are marked
    symptom_sum = binary_df[all_symptoms].sum(axis=1)
    binary_df = binary_df[symptom_sum > 0].reset_index(drop=True)
    
    # Save
    binary_df.to_csv(output_file, index=False)
    
    print(f"\n✅ Training.csv created successfully!")
    print(f"   Rows: {binary_df.shape[0]}")
    print(f"   Symptom features: {len(all_symptoms)}")
    print(f"   Diseases: {binary_df['prognosis'].nunique()}")
    print(f"   Disease list: {sorted(binary_df['prognosis'].unique())}")
    print(f"\n   Saved to: {output_file}")
    
    # ============================================
    # STEP 8: Also save symptom list
    # ============================================
    import json
    symptom_list_path = os.path.join('data', 'symptom_list.json')
    with open(symptom_list_path, 'w') as f:
        json.dump({
            'symptoms': [s.replace('_', ' ') for s in all_symptoms],
            'symptom_to_index': {s.replace('_', ' '): i for i, s in enumerate(all_symptoms)},
            'raw_columns': all_symptoms
        }, f, indent=2)
    print(f"   Symptom list saved to: {symptom_list_path}")
    
    # ============================================
    # STEP 9: Auto-generate description.csv if not exists
    # ============================================
    desc_path = os.path.join('data', 'description.csv')
    if not os.path.exists(desc_path):
        diseases = sorted(binary_df['prognosis'].unique())
        desc_df = pd.DataFrame({
            'Disease': diseases,
            'Description': [f'{d} is a medical condition. Please consult a doctor for details.' for d in diseases]
        })
        desc_df.to_csv(desc_path, index=False)
        print(f"   Auto-generated description.csv")
    
    print("\n🎉 Conversion complete! You can now run: python train_model.py")


if __name__ == '__main__':
    convert_dataset()