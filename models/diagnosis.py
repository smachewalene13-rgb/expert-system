from app import db
from datetime import datetime

class Diagnosis(db.Model):
    __tablename__ = 'diagnoses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symptoms = db.Column(db.Text, nullable=False)
    predicted_condition = db.Column(db.String(200))
    confidence_score = db.Column(db.Float)
    severity = db.Column(db.String(20))
    treatment_recommendation = db.Column(db.Text)
    doctor_recommended = db.Column(db.Boolean, default=False)
    matched_symptoms = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_matched_symptoms_list(self):
        if self.matched_symptoms:
            return self.matched_symptoms.split(',')
        return []
    
    def __repr__(self):
        return f'<Diagnosis {self.id} - {self.predicted_condition}>'