import json
import math
from collections import Counter

class AIDiagnosisEngine:
    def __init__(self):
        self.load_medical_data()
    
    def load_medical_data(self):
        """Load medical conditions database"""
        self.conditions = {
            "common_cold": {
                "name": "Common Cold",
                "symptoms": ["runny nose", "sneezing", "cough", "sore throat", "mild fever", "fatigue"],
                "treatment": "Rest, fluids, over-the-counter cold medicine",
                "urgency": "low",
                "see_doctor": False
            },
            "influenza": {
                "name": "Influenza (Flu)",
                "symptoms": ["high fever", "body aches", "chills", "fatigue", "headache", "dry cough"],
                "treatment": "Antiviral medication, rest, fluids, fever reducers",
                "urgency": "medium",
                "see_doctor": True
            },
            "covid19": {
                "name": "COVID-19",
                "symptoms": ["fever", "dry cough", "fatigue", "loss of taste", "loss of smell", "difficulty breathing"],
                "treatment": "Isolation, monitor oxygen levels, seek medical care if severe",
                "urgency": "high",
                "see_doctor": True
            },
            "allergy": {
                "name": "Seasonal Allergies",
                "symptoms": ["sneezing", "itchy eyes", "runny nose", "nasal congestion", "watery eyes"],
                "treatment": "Antihistamines, avoid allergens, nasal spray",
                "urgency": "low",
                "see_doctor": False
            },
            "migraine": {
                "name": "Migraine",
                "symptoms": ["severe headache", "nausea", "sensitivity to light", "sensitivity to sound"],
                "treatment": "Rest in dark room, pain relievers, hydration",
                "urgency": "medium",
                "see_doctor": True
            }
        }
        
        self.symptom_synonyms = {
            "fever": ["fever", "high temperature", "hot"],
            "cough": ["cough", "coughing", "dry cough"],
            "headache": ["headache", "head pain"],
            "fatigue": ["fatigue", "tired", "exhausted"],
            "nausea": ["nausea", "queasy"],
            "runny nose": ["runny nose", "nasal discharge"],
            "sore throat": ["sore throat", "throat pain"]
        }
    
    def normalize_symptom(self, symptom):
        symptom_lower = symptom.lower().strip()
        for standard, variants in self.symptom_synonyms.items():
            if symptom_lower in variants:
                return standard
        return symptom_lower
    
    def calculate_confidence(self, user_symptoms):
        normalized = [self.normalize_symptom(s) for s in user_symptoms]
        results = []
        
        for cond_id, condition in self.conditions.items():
            condition_symptoms = [s.lower() for s in condition["symptoms"]]
            matches = [s for s in normalized if s in condition_symptoms]
            match_count = len(matches)
            
            if match_count > 0:
                confidence = min(95, (match_count / len(condition_symptoms)) * 100 + 10)
                results.append({
                    "condition": condition["name"],
                    "confidence": round(confidence, 1),
                    "matched_symptoms": matches,
                    "match_count": match_count,
                    "total_symptoms": len(condition["symptoms"]),
                    "treatment": condition["treatment"],
                    "urgency": condition["urgency"],
                    "see_doctor": condition["see_doctor"]
                })
        
        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results
    
    def check_emergency(self, symptoms):
        emergency_symptoms = ["chest pain", "difficulty breathing", "severe bleeding", "loss of consciousness"]
        for s in symptoms:
            if s.lower() in emergency_symptoms:
                return True
        return False
    
    def get_general_advice(self, age, duration):
        advice = {
            "rest": "Get adequate rest (7-9 hours of sleep daily)",
            "hydration": "Drink plenty of water (8-10 glasses per day)",
            "monitor": "Monitor symptoms and track temperature daily",
            "when_to_see_doctor": "Consult a doctor if symptoms worsen or persist beyond 5-7 days"
        }
        
        if age and age.isdigit() and int(age) > 60:
            advice["elderly"] = "As an older adult, monitor closely and seek care earlier if concerned."
        elif age and age.isdigit() and int(age) < 12:
            advice["pediatric"] = "For children, monitor hydration carefully and consult pediatrician if fever persists."
        
        return advice
    
    def get_all_symptoms(self):
        all_symptoms = set()
        for condition in self.conditions.values():
            all_symptoms.update(condition["symptoms"])
        return sorted(list(all_symptoms))
    
    def get_all_conditions(self):
        return [{"name": c["name"], "urgency": c["urgency"]} for c in self.conditions.values()]