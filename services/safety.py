"""
HealthoAssist - Drug Safety Layer
Checks for allergy conflicts and drug-drug interactions
"""

class SafetyChecker:
    
    # Common drug interaction pairs (simplified for demo)
    DRUG_INTERACTIONS = {
        'aspirin': ['warfarin', 'ibuprofen', 'naproxen', 'heparin'],
        'warfarin': ['aspirin', 'ibuprofen', 'naproxen', 'vitamin k'],
        'metformin': ['alcohol', 'contrast dye'],
        'lisinopril': ['potassium supplements', 'spironolactone'],
        'amoxicillin': ['methotrexate', 'warfarin'],
        'ibuprofen': ['aspirin', 'warfarin', 'lithium', 'methotrexate'],
        'paracetamol': ['warfarin', 'alcohol'],
        'acetaminophen': ['warfarin', 'alcohol'],
        'ciprofloxacin': ['theophylline', 'warfarin', 'antacids'],
        'metoprolol': ['verapamil', 'diltiazem', 'clonidine'],
        'omeprazole': ['clopidogrel', 'methotrexate'],
        'atorvastatin': ['gemfibrozil', 'niacin', 'cyclosporine'],
        'clopidogrel': ['omeprazole', 'esomeprazole'],
    }
    
    @staticmethod
    def check_allergies(medications_list, patient_allergies):
        """
        Check if any recommended medication conflicts with patient allergies.
        
        Args:
            medications_list: list of medication names
            patient_allergies: list of allergy strings
            
        Returns:
            list of warning dicts: [{"drug": "...", "warning": "...", "type": "allergy"}]
        """
        warnings = []
        if not patient_allergies or not medications_list:
            return warnings
        
        allergies_lower = [a.lower().strip() for a in patient_allergies]
        
        for med in medications_list:
            med_lower = med.lower().strip()
            for allergy in allergies_lower:
                if allergy in med_lower or med_lower in allergy:
                    warnings.append({
                        'drug': med,
                        'warning': f'⚠️ ALLERGY ALERT: "{med}" may conflict with your known allergy to "{allergy}". Please consult a doctor before taking this medication.',
                        'type': 'allergy',
                        'severity': 'high'
                    })
        
        return warnings
    
    @staticmethod
    def check_drug_interactions(new_medications, current_medications):
        """
        Check for drug-drug interactions between new and current medications.
        
        Args:
            new_medications: list of newly recommended medication names
            current_medications: list of patient's current medication names
            
        Returns:
            list of warning dicts
        """
        warnings = []
        if not current_medications or not new_medications:
            return warnings
        
        current_lower = [m.lower().strip() for m in current_medications]
        
        for new_med in new_medications:
            new_med_lower = new_med.lower().strip()
            
            # Check our interaction database
            if new_med_lower in SafetyChecker.DRUG_INTERACTIONS:
                interacting_drugs = SafetyChecker.DRUG_INTERACTIONS[new_med_lower]
                for current_med in current_lower:
                    for interact in interacting_drugs:
                        if interact in current_med or current_med in interact:
                            warnings.append({
                                'drug': new_med,
                                'warning': f'⚠️ INTERACTION WARNING: "{new_med}" may interact with your current medication "{current_med}". Please consult your doctor.',
                                'type': 'drug_interaction',
                                'severity': 'medium',
                                'interacting_with': current_med
                            })
        
        return warnings
    
    @staticmethod
    def perform_safety_check(medications_list, patient_allergies, current_medications):
        """
        Perform complete safety check.
        
        Returns:
            dict with 'warnings' list, 'safe_medications' list, 'flagged_medications' list
        """
        all_warnings = []
        
        # Check allergies
        allergy_warnings = SafetyChecker.check_allergies(medications_list, patient_allergies)
        all_warnings.extend(allergy_warnings)
        
        # Check drug interactions
        ddi_warnings = SafetyChecker.check_drug_interactions(medications_list, current_medications)
        all_warnings.extend(ddi_warnings)
        
        # Categorize medications
        flagged_drugs = set()
        for w in all_warnings:
            flagged_drugs.add(w['drug'].lower())
        
        safe_meds = [m for m in medications_list if m.lower() not in flagged_drugs]
        flagged_meds = [m for m in medications_list if m.lower() in flagged_drugs]
        
        return {
            'warnings': all_warnings,
            'safe_medications': safe_meds,
            'flagged_medications': flagged_meds,
            'has_warnings': len(all_warnings) > 0
        }