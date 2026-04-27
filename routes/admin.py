from flask import render_template, Blueprint, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from models.user import User
from models.diagnosis import Diagnosis
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
def check_admin():
    if not current_user.is_authenticated or not current_user.is_admin():
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))

@admin_bp.route('/dashboard')
def dashboard():
    total_users = User.query.count()
    total_diagnoses = Diagnosis.query.count()
    
    today = datetime.utcnow().date()
    active_users = User.query.filter(User.last_login >= datetime.utcnow() - timedelta(days=1)).count()
    
    high_risk = Diagnosis.query.filter_by(doctor_recommended=True).count()
    
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    # Top conditions
    top_conditions = db.session.query(
        Diagnosis.predicted_condition, db.func.count(Diagnosis.id)
    ).group_by(Diagnosis.predicted_condition).order_by(db.func.count(Diagnosis.id).desc()).limit(10).all()
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         total_diagnoses=total_diagnoses,
                         active_users=active_users,
                         high_risk=high_risk,
                         recent_users=recent_users,
                         top_conditions=top_conditions)