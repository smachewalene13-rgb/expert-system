from app import db
from datetime import datetime

class Symptom(db.Model):
    __tablename__ = 'symptoms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    synonyms = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_synonyms_list(self):
        if self.synonyms:
            return [s.strip() for s in self.synonyms.split(',')]
        return []
    
    def __repr__(self):
        return f'<Symptom {self.name}>'