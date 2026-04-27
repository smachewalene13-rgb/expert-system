from flask import render_template, redirect, url_for, flash, request, Blueprint
from flask_login import login_required, current_user
from app import db
from models.diagnosis import Diagnosis
from services.report_generator import generate_pdf_report
from datetime import datetime, timedelta

patient_bp = Blueprint('patient', __name__)

@patient_bp.route('/dashboard')
@login_required
def dashboard():
    # Get statistics
    diagnoses = Diagnosis.query.filter_by(user_id=current_user.id).all()
    diagnosis_count = len(diagnoses)
    
    high_risk_count = Diagnosis.query.filter_by(user_id=current_user.id, doctor_recommended=True).count()
    
    week_ago = datetime.utcnow() - timedelta(days=7)
    last_week_count = Diagnosis.query.filter(
        Diagnosis.user_id == current_user.id,
        Diagnosis.created_at >= week_ago
    ).count()
    
    # Average confidence
    avg_confidence = db.session.query(db.func.avg(Diagnosis.confidence_score)).filter_by(user_id=current_user.id).scalar() or 0
    
    recent_diagnoses = Diagnosis.query.filter_by(user_id=current_user.id).order_by(Diagnosis.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html',
                         diagnosis_count=diagnosis_count,
                         high_risk_count=high_risk_count,
                         last_week_count=last_week_count,
                         avg_confidence=int(avg_confidence),
                         recent_diagnoses=recent_diagnoses)

@patient_bp.route('/history')
@login_required
def history():
    diagnoses = Diagnosis.query.filter_by(user_id=current_user.id).order_by(Diagnosis.created_at.desc()).all()
    return render_template('history.html', diagnoses=diagnoses)

@patient_bp.route('/view/<int:id>')
@login_required
def view_diagnosis(id):
    diagnosis = Diagnosis.query.get_or_404(id)
    if diagnosis.user_id != current_user.id and not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('patient.dashboard'))
    return render_template('view_diagnosis.html', diagnosis=diagnosis)

@patient_bp.route('/export-pdf/<int:id>')
@login_required
def export_pdf(id):
    diagnosis = Diagnosis.query.get_or_404(id)
    if diagnosis.user_id != current_user.id and not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('patient.dashboard'))
    
    pdf_file = generate_pdf_report(diagnosis, current_user)
    return pdf_file

@patient_bp.route('/export-data')
@login_required
def export_data():
    # Export all user data as JSON
    import json
    diagnoses = Diagnosis.query.filter_by(user_id=current_user.id).all()
    data = []
    for d in diagnoses:
        data.append({
            'date': d.created_at.isoformat(),
            'symptoms': d.symptoms,
            'diagnosis': d.predicted_condition,
            'confidence': d.confidence_score
        })
    return jsonify(data)