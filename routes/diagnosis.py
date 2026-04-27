from flask import render_template, request, jsonify, Blueprint
from flask_login import login_required, current_user
from app import db
from models.diagnosis import Diagnosis
from services.ai_diagnosis import AIDiagnosisEngine
from datetime import datetime

diagnosis_bp = Blueprint('diagnosis', __name__)
ai_engine = AIDiagnosisEngine()

@diagnosis_bp.route('/api/diagnose', methods=['POST'])
def diagnose():
    data = request.get_json()
    symptoms = data.get('symptoms', [])
    age = data.get('age', '')
    duration = data.get('duration', '')
    
    if not symptoms:
        return jsonify({"error": "Please enter at least one symptom"}), 400
    
    # Get AI diagnosis
    results = ai_engine.calculate_confidence(symptoms)
    
    # Save to database if user is logged in
    if current_user.is_authenticated:
        diagnosis = Diagnosis(
            user_id=current_user.id,
            symptoms=', '.join(symptoms),
            predicted_condition=results[0]['condition'] if results else None,
            confidence_score=results[0]['confidence'] if results else None,
            matched_symptoms=','.join(results[0]['matched_symptoms']) if results else '',
            created_at=datetime.utcnow()
        )
        db.session.add(diagnosis)
        db.session.commit()
    
    return jsonify({
        "success": True,
        "diagnosis": results[:5],
        "emergency_warning": ai_engine.check_emergency(symptoms),
        "patient_info": {
            "age": age if age else "Not provided",
            "duration": duration if duration else "Not specified",
            "symptom_count": len(symptoms)
        },
        "advice": ai_engine.get_general_advice(age, duration)
    })

@diagnosis_bp.route('/api/symptoms', methods=['GET'])
def get_symptoms():
    symptoms = ai_engine.get_all_symptoms()
    return jsonify({"symptoms": symptoms})

@diagnosis_bp.route('/api/conditions', methods=['GET'])
def get_conditions():
    conditions = ai_engine.get_all_conditions()
    return jsonify({"conditions": conditions})