"""
Prolog Integration Bridge for Medical Diagnosis System
This file adds Prolog-style diagnosis WITHOUT modifying existing app.py
"""

from prolog_diagnosis import PrologStyleEngine
import json

class PrologMedicalBridge:
    """
    Bridge between Prolog engine and Flask app
    """
    
    def __init__(self):
        self.engine = PrologStyleEngine()
        print("✅ Prolog Bridge initialized")
    
    def diagnose_with_prolog(self, symptoms):
        """
        Run Prolog-style diagnosis on symptoms
        Returns: List of diagnoses with confidence scores
        """
        # Clear previous symptoms
        self.engine.clear_symptoms()
        
        # Add new symptoms
        for symptom in symptoms:
            self.engine.add_symptom(symptom)
        
        # Get diagnosis
        results = self.engine.diagnose()
        
        # Format for JSON response
        formatted_results = []
        for r in results:
            formatted_results.append({
                'condition': r['disease'],
                'confidence': r['confidence'],
                'matched_symptoms': r['matched_symptoms'],
                'match_count': r['match_count'],
                'total_symptoms': r['total_symptoms'],
                'treatment': r['treatment'],
                'severity': r['severity']
            })
        
        return formatted_results
    
    def compare_diagnosis(self, symptoms, ml_diagnosis):
        """
        Compare Prolog diagnosis with ML-based diagnosis
        """
        prolog_results = self.diagnose_with_prolog(symptoms)
        
        comparison = {
            'prolog_top': prolog_results[0] if prolog_results else None,
            'ml_top': ml_diagnosis[0] if ml_diagnosis else None,
            'prolog_all': prolog_results,
            'ml_all': ml_diagnosis,
            'agreement': False
        }
        
        # Check if both agree on top diagnosis
        if comparison['prolog_top'] and comparison['ml_top']:
            if comparison['prolog_top']['condition'] == comparison['ml_top']['condition']:
                comparison['agreement'] = True
        
        return comparison
    
    def explain_diagnosis(self, disease):
        """
        Get explanation for a Prolog diagnosis
        """
        return self.engine.explain(disease)
    
    def get_all_diseases(self):
        """
        Get all diseases in Prolog knowledge base
        """
        return self.engine.get_all_diseases()

# Create global instance
prolog_bridge = PrologMedicalBridge()