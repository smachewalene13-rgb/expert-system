"""
Prolog-style Medical Diagnosis Engine (Pure Python)
No external dependencies required!
"""

from typing import List, Dict, Any

class PrologStyleEngine:
    """
    Prolog-inspired medical diagnosis engine
    Uses rule-based inference similar to Prolog but in pure Python
    """
    
    def __init__(self):
        self.symptoms = []
        self.load_knowledge_base()
    
    def load_knowledge_base(self):
        """Load medical rules (Prolog-style knowledge base)"""
        self.rules = [
            {
                'disease': 'Common Cold',
                'required_symptoms': ['runny nose', 'sneezing', 'cough', 'sore throat'],
                'optional_symptoms': ['mild fever', 'fatigue'],
                'min_required': 3
            },
            {
                'disease': 'Influenza (Flu)',
                'required_symptoms': ['high fever', 'body aches', 'fatigue'],
                'optional_symptoms': ['headache', 'dry cough', 'sore throat'],
                'min_required': 3
            },
            {
                'disease': 'COVID-19',
                'required_symptoms': ['fever', 'dry cough', 'fatigue'],
                'optional_symptoms': ['loss of taste', 'loss of smell', 'difficulty breathing'],
                'min_required': 3
            },
            {
                'disease': 'Strep Throat',
                'required_symptoms': ['severe sore throat', 'fever'],
                'optional_symptoms': ['painful swallowing', 'swollen lymph nodes'],
                'min_required': 2
            },
            {
                'disease': 'Seasonal Allergies',
                'required_symptoms': ['sneezing', 'itchy eyes', 'runny nose'],
                'optional_symptoms': ['nasal congestion', 'watery eyes'],
                'min_required': 2
            },
            {
                'disease': 'Migraine',
                'required_symptoms': ['severe headache', 'nausea'],
                'optional_symptoms': ['sensitivity to light', 'sensitivity to sound', 'vomiting'],
                'min_required': 2
            },
            {
                'disease': 'Bronchitis',
                'required_symptoms': ['persistent cough', 'chest discomfort'],
                'optional_symptoms': ['phlegm', 'fatigue', 'shortness of breath'],
                'min_required': 2
            },
            {
                'disease': 'Sinus Infection',
                'required_symptoms': ['facial pain', 'nasal congestion'],
                'optional_symptoms': ['headache', 'thick discharge', 'cough'],
                'min_required': 2
            },
            {
                'disease': 'Gastroenteritis',
                'required_symptoms': ['nausea', 'vomiting', 'diarrhea'],
                'optional_symptoms': ['stomach pain', 'mild fever'],
                'min_required': 3
            }
        ]
        
        self.treatments = {
            'Common Cold': 'Rest, fluids, over-the-counter cold medicine, honey for cough',
            'Influenza (Flu)': 'Antiviral medication, rest, fluids, fever reducers, electrolytes',
            'COVID-19': 'Isolation, monitor oxygen levels, hydration, fever reducers',
            'Strep Throat': 'Antibiotics, rest, warm salt water gargle, throat lozenges',
            'Seasonal Allergies': 'Antihistamines, avoid allergens, nasal spray',
            'Migraine': 'Rest in dark room, cold compress, pain relievers, hydration',
            'Bronchitis': 'Rest, fluids, cough medicine, humidifier, avoid smoke',
            'Sinus Infection': 'Nasal irrigation, decongestants, rest, hydration',
            'Gastroenteritis': 'Hydration, rest, bland diet (BRAT), electrolytes'
        }
        
        self.symptom_synonyms = {
            'fever': ['fever', 'high temperature', 'high temp', 'hot'],
            'cough': ['cough', 'coughing', 'dry cough', 'wet cough'],
            'headache': ['headache', 'head pain'],
            'fatigue': ['fatigue', 'tired', 'exhausted', 'weakness'],
            'nausea': ['nausea', 'queasy', 'sick to stomach'],
            'vomiting': ['vomiting', 'throwing up', 'puking'],
            'diarrhea': ['diarrhea', 'loose stools'],
            'runny nose': ['runny nose', 'nasal discharge', 'sniffles'],
            'sore throat': ['sore throat', 'throat pain', 'scratchy throat']
        }
    
    def normalize_symptom(self, symptom: str) -> str:
        """Normalize symptom using synonym mapping"""
        symptom_lower = symptom.lower().strip()
        for standard, variants in self.symptom_synonyms.items():
            if symptom_lower == standard or symptom_lower in variants:
                return standard
        return symptom_lower
    
    def add_symptom(self, symptom: str):
        """Add a symptom"""
        normalized = self.normalize_symptom(symptom)
        if normalized not in self.symptoms:
            self.symptoms.append(normalized)
    
    def remove_symptom(self, symptom: str):
        """Remove a symptom"""
        normalized = self.normalize_symptom(symptom)
        if normalized in self.symptoms:
            self.symptoms.remove(normalized)
    
    def clear_symptoms(self):
        """Clear all symptoms"""
        self.symptoms = []
    
    def list_symptoms(self) -> List[str]:
        """List current symptoms"""
        return self.symptoms.copy()
    
    def diagnose(self) -> List[Dict[str, Any]]:
        """Diagnose based on current symptoms"""
        results = []
        
        for rule in self.rules:
            required_matches = [s for s in rule['required_symptoms'] if s in self.symptoms]
            
            if len(required_matches) >= rule['min_required']:
                optional_matches = [s for s in rule['optional_symptoms'] if s in self.symptoms]
                
                total_matches = len(required_matches) + len(optional_matches)
                total_symptoms = len(rule['required_symptoms']) + len(rule['optional_symptoms'])
                
                confidence = min(95, int((total_matches / total_symptoms) * 100) + 10)
                
                results.append({
                    'disease': rule['disease'],
                    'confidence': confidence,
                    'matched_symptoms': required_matches + optional_matches,
                    'match_count': total_matches,
                    'total_symptoms': total_symptoms,
                    'treatment': self.treatments.get(rule['disease'], 'Consult a doctor'),
                    'severity': self._get_severity(rule['disease'])
                })
        
        results.sort(key=lambda x: x['confidence'], reverse=True)
        return results
    
    def _get_severity(self, disease: str) -> str:
        """Get severity level for a disease"""
        severity_map = {
            'Common Cold': 'Low',
            'Influenza (Flu)': 'High',
            'COVID-19': 'High',
            'Strep Throat': 'Medium',
            'Seasonal Allergies': 'Low',
            'Migraine': 'Medium',
            'Bronchitis': 'Medium',
            'Sinus Infection': 'Low',
            'Gastroenteritis': 'Medium'
        }
        return severity_map.get(disease, 'Unknown')
    
    def explain(self, disease: str) -> str:
        """Explain why a disease was diagnosed"""
        for rule in self.rules:
            if rule['disease'] == disease:
                matched = [s for s in rule['required_symptoms'] if s in self.symptoms]
                if matched:
                    return f"Diagnosed as {disease} because you have: {', '.join(matched)}"
                return f"Diagnosed as {disease} based on symptom pattern matching"
        return f"No explanation available for {disease}"
    
    def get_all_diseases(self) -> List[str]:
        """Get all possible diseases"""
        return [rule['disease'] for rule in self.rules]