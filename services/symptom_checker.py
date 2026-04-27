class SymptomChecker:
    def __init__(self):
        self.symptom_database = {
            "fever": {"related": ["chills", "sweating", "dehydration"], "severity": "medium"},
            "cough": {"related": ["sore throat", "chest pain", "difficulty breathing"], "severity": "medium"},
            "headache": {"related": ["nausea", "light sensitivity", "fatigue"], "severity": "low"},
            "fatigue": {"related": ["weakness", "dizziness", "lack of energy"], "severity": "low"},
        }
    
    def check_related_symptoms(self, symptom):
        if symptom in self.symptom_database:
            return self.symptom_database[symptom]["related"]
        return []
    
    def get_severity(self, symptom):
        if symptom in self.symptom_database:
            return self.symptom_database[symptom]["severity"]
        return "unknown"