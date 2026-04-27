"""
AI Medical Diagnosis System - Complete Working Version
Includes: Health Charts, Export Data, Daily Health Tips, PDF Reports (Fully Functional)
"""
from flask import Flask, render_template_string, request, jsonify, flash, redirect, url_for, send_file, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import re
import functools
import os
import json
import random
import csv
from io import BytesIO, StringIO
from collections import defaultdict

# ==================== TRY TO IMPORT PDF LIBRARY ====================
REPORTLAB_AVAILABLE = False
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
    print("✅ ReportLab loaded - PDF generation enabled")
except ImportError:
    print("⚠️ ReportLab not installed. PDF generation disabled. Install with: pip install reportlab")

# ==================== HEALTH TIPS DATABASE ====================
HEALTH_TIPS = [
    "💧 Drink 8 glasses of water daily for optimal hydration",
    "😴 Get 7-9 hours of quality sleep each night",
    "🏃 Exercise for at least 30 minutes daily",
    "🧼 Wash hands frequently to prevent infections",
    "🥗 Eat more fruits and vegetables for vitamins",
    "🚭 Avoid smoking and limit alcohol consumption",
    "🧘 Practice stress management techniques like meditation",
    "🩺 Schedule regular health check-ups",
    "💊 Take medications as prescribed by your doctor",
    "🌞 Get 15-20 minutes of sunlight for Vitamin D",
    "📱 Take breaks from screens to reduce eye strain",
    "🍎 Eat a balanced diet with all food groups",
    "🧠 Keep your mind active with puzzles and learning",
    "🤝 Maintain social connections for mental health",
    "🩸 Monitor your blood pressure regularly",
    "⚖️ Maintain a healthy weight through diet and exercise",
    "🦷 Brush and floss teeth twice daily",
    "💉 Stay up to date with vaccinations",
    "🧴 Use sunscreen to protect your skin",
    "👨‍⚕️ Don't ignore persistent symptoms - consult a doctor"
]

# ==================== HELPER FUNCTIONS ====================
def truncate_text(text, max_length=100, suffix='...'):
    if not text:
        return ''
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def format_date(date_obj, format_str='%Y-%m-%d %H:%M:%S'):
    if date_obj is None:
        return 'N/A'
    return date_obj.strftime(format_str)

def sanitize_input(text, max_length=500):
    if not text:
        return ''
    text = re.sub(r'<[^>]+>', '', text)
    if len(text) > max_length:
        text = text[:max_length]
    return text.strip()

# ==================== SIMPLE VALIDATION ====================
def validate_registration(username, email, password, confirm):
    if not username or not username.strip():
        return False, "Username is required"
    if not email or not email.strip():
        return False, "Email is required"
    if not password:
        return False, "Password is required"
    if password != confirm:
        return False, "Passwords do not match"
    if len(password) < 4:
        return False, "Password must be at least 4 characters"
    return True, ""

# ==================== DECORATORS ====================
def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        if current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def handle_errors(default_message="An error occurred. Please try again."):
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                print(f"Error: {str(e)}")
                flash(default_message, 'danger')
                return redirect(url_for('index'))
        return decorated_function
    return decorator

# ==================== INITIALIZE FLASK APP ====================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medical.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create uploads directory if not exists
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'reports')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# ==================== DATABASE MODELS ====================
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='patient')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Diagnosis(db.Model):
    __tablename__ = 'diagnoses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symptoms = db.Column(db.Text, nullable=False)
    predicted_condition = db.Column(db.String(200))
    confidence_score = db.Column(db.Float)
    treatment_advice = db.Column(db.Text)
    doctor_recommended = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='diagnoses')

# ==================== PDF REPORT GENERATION (FULLY FUNCTIONAL) ====================
def generate_pdf_report(diagnosis, patient):
    """Generate a professional PDF report for a diagnosis"""
    if not REPORTLAB_AVAILABLE:
        return None
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2563eb'),
        alignment=1,
        spaceAfter=30
    )
    
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=10,
        spaceBefore=10
    )
    
    # Report Title
    story.append(Paragraph("🏥 AI Medical Diagnosis Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Report Metadata
    story.append(Paragraph(f"<b>Report ID:</b> #{diagnosis.id}", styles['Normal']))
    story.append(Paragraph(f"<b>Date Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Patient Information
    story.append(Paragraph("📋 PATIENT INFORMATION", header_style))
    story.append(Paragraph(f"<b>Name:</b> {patient.username}", styles['Normal']))
    story.append(Paragraph(f"<b>Email:</b> {patient.email}", styles['Normal']))
    story.append(Paragraph(f"<b>Member Since:</b> {format_date(patient.created_at, '%Y-%m-%d')}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Diagnosis Information
    story.append(Paragraph("🩺 DIAGNOSIS INFORMATION", header_style))
    story.append(Paragraph(f"<b>Diagnosis Date:</b> {format_date(diagnosis.created_at, '%Y-%m-%d %H:%M')}", styles['Normal']))
    story.append(Paragraph(f"<b>Reported Symptoms:</b> {diagnosis.symptoms}", styles['Normal']))
    story.append(Paragraph(f"<b>Predicted Condition:</b> {diagnosis.predicted_condition or 'Analysis in progress'}", styles['Normal']))
    story.append(Paragraph(f"<b>Confidence Score:</b> {diagnosis.confidence_score}%", styles['Normal']))
    
    # Confidence level indicator
    if diagnosis.confidence_score and diagnosis.confidence_score >= 70:
        confidence_level = "High"
        conf_color = colors.green
    elif diagnosis.confidence_score and diagnosis.confidence_score >= 40:
        confidence_level = "Medium"
        conf_color = colors.orange
    else:
        confidence_level = "Low"
        conf_color = colors.red
    
    story.append(Paragraph(f"<b>Confidence Level:</b> <font color='{conf_color}'>{confidence_level}</font>", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Treatment Recommendations
    story.append(Paragraph("💊 TREATMENT RECOMMENDATIONS", header_style))
    story.append(Paragraph(diagnosis.treatment_advice or "No specific treatment advice available. Please consult a healthcare provider.", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Doctor Consultation Warning
    if diagnosis.doctor_recommended:
        story.append(Paragraph("<b><font color='red'>⚠️ IMPORTANT: Please consult a healthcare provider</font></b>", styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
    
    # General Health Advice
    story.append(Paragraph("💡 GENERAL HEALTH ADVICE", header_style))
    advice_items = [
        "• Get adequate rest (7-9 hours of sleep daily)",
        "• Stay hydrated (8-10 glasses of water per day)",
        "• Monitor your symptoms and track temperature",
        "• Maintain a healthy diet to support recovery",
        "• Avoid contact with others if contagious"
    ]
    for item in advice_items:
        story.append(Paragraph(item, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Disclaimer
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("="*60, styles['Normal']))
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Italic'],
        fontSize=9,
        textColor=colors.HexColor('#94a3b8'),
        alignment=1
    )
    story.append(Paragraph("DISCLAIMER: This report is generated by an AI system for informational purposes only.", disclaimer_style))
    story.append(Paragraph("It is not a substitute for professional medical advice, diagnosis, or treatment.", disclaimer_style))
    story.append(Paragraph("Always seek the advice of your physician or other qualified health provider.", disclaimer_style))
    story.append(Paragraph(f"Generated by AI Medical Diagnosis System • {datetime.now().year}", disclaimer_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

# ==================== IMPROVED MEDICAL KNOWLEDGE BASE ====================
MEDICAL_CONDITIONS = {
    "common_cold": {
        "name": "Common Cold",
        "symptoms": ["runny nose", "sneezing", "cough", "sore throat", "mild fever", "fatigue", "nasal congestion"],
        "treatment": "Rest, fluids, over-the-counter cold medicine, honey for cough, saline nasal spray",
        "see_doctor": False
    },
    "influenza": {
        "name": "Influenza (Flu)",
        "symptoms": ["high fever", "body aches", "chills", "fatigue", "headache", "dry cough", "sore throat", "muscle pain"],
        "treatment": "Antiviral medication, rest, fluids, fever reducers, electrolyte drinks",
        "see_doctor": True
    },
    "covid19": {
        "name": "COVID-19",
        "symptoms": ["fever", "dry cough", "fatigue", "loss of taste", "loss of smell", "difficulty breathing", "sore throat", "headache", "muscle aches"],
        "treatment": "Isolation, monitor oxygen levels, hydration, fever reducers, seek medical care if breathing difficulties",
        "see_doctor": True
    },
    "allergy": {
        "name": "Seasonal Allergies",
        "symptoms": ["sneezing", "itchy eyes", "runny nose", "nasal congestion", "watery eyes", "scratchy throat"],
        "treatment": "Antihistamines, avoid allergens, nasal spray, air purifier",
        "see_doctor": False
    },
    "migraine": {
        "name": "Migraine Headache",
        "symptoms": ["severe headache", "nausea", "sensitivity to light", "sensitivity to sound", "vomiting", "throbbing pain"],
        "treatment": "Rest in dark room, cold compress, pain relievers, hydration, avoid triggers",
        "see_doctor": True
    },
    "bronchitis": {
        "name": "Acute Bronchitis",
        "symptoms": ["persistent cough", "chest discomfort", "phlegm", "fatigue", "shortness of breath", "mild fever"],
        "treatment": "Rest, fluids, cough medicine, humidifier, avoid smoke",
        "see_doctor": True
    },
    "gastroenteritis": {
        "name": "Gastroenteritis (Stomach Flu)",
        "symptoms": ["nausea", "vomiting", "diarrhea", "stomach pain", "mild fever", "headache"],
        "treatment": "Hydration, rest, bland diet (BRAT), electrolytes",
        "see_doctor": True
    },
    "sinusitis": {
        "name": "Sinus Infection",
        "symptoms": ["facial pain", "nasal congestion", "headache", "thick nasal discharge", "cough", "fever"],
        "treatment": "Nasal irrigation, decongestants, rest, hydration, warm compress",
        "see_doctor": False
    },
    "strep_throat": {
        "name": "Strep Throat",
        "symptoms": ["severe sore throat", "painful swallowing", "fever", "swollen lymph nodes", "white patches on tonsils"],
        "treatment": "Antibiotics, rest, warm salt water gargle, throat lozenges",
        "see_doctor": True
    }
}

SYMPTOM_SYNONYMS = {
    "fever": ["fever", "high temperature", "high temp", "hot", "febrile", "pyrexia"],
    "cough": ["cough", "coughing", "dry cough", "wet cough", "productive cough"],
    "headache": ["headache", "head pain", "migraine", "cephalalgia"],
    "fatigue": ["fatigue", "tired", "exhausted", "weakness", "low energy", "lethargy"],
    "nausea": ["nausea", "queasy", "sick to stomach", "nauseous"],
    "vomiting": ["vomiting", "throwing up", "puking", "emesis"],
    "diarrhea": ["diarrhea", "loose stools", "watery stool"],
    "runny nose": ["runny nose", "nasal discharge", "sniffles", "rhinorrhea"],
    "sore throat": ["sore throat", "throat pain", "scratchy throat", "pharyngitis"],
    "body aches": ["body aches", "muscle pain", "myalgia", "body pain", "muscle soreness"],
    "shortness of breath": ["shortness of breath", "difficulty breathing", "breathing trouble", "dyspnea"],
    "chills": ["chills", "shivering", "rigors"],
    "loss of taste": ["loss of taste", "taste loss", "ageusia"],
    "loss of smell": ["loss of smell", "smell loss", "anosmia"],
    "nasal congestion": ["nasal congestion", "stuffy nose", "blocked nose", "congested"]
}

def normalize_symptom(symptom):
    symptom_lower = symptom.lower().strip()
    
    for standard, variants in SYMPTOM_SYNONYMS.items():
        if symptom_lower == standard:
            return standard
        if symptom_lower in variants:
            return standard
    
    for standard, variants in SYMPTOM_SYNONYMS.items():
        if symptom_lower in standard or standard in symptom_lower:
            return standard
        for variant in variants:
            if symptom_lower in variant or variant in symptom_lower:
                return standard
    
    return symptom_lower

def get_diagnosis(symptoms):
    normalized = [normalize_symptom(s) for s in symptoms]
    results = []
    
    for condition in MEDICAL_CONDITIONS.values():
        condition_symptoms = [s.lower() for s in condition["symptoms"]]
        matches = [s for s in normalized if s in condition_symptoms]
        match_count = len(matches)
        
        if match_count > 0:
            base_percentage = (match_count / len(condition["symptoms"])) * 100
            
            if match_count >= 3:
                final_confidence = min(95, base_percentage * 1.3)
            elif match_count >= 2:
                final_confidence = min(90, base_percentage * 1.15)
            else:
                final_confidence = min(70, base_percentage * 1.05)
            
            if condition["see_doctor"] and match_count >= 2:
                final_confidence = min(95, final_confidence + 10)
            
            final_confidence = max(15, round(final_confidence, 1))
            
            results.append({
                "condition": condition["name"],
                "confidence": final_confidence,
                "matched_symptoms": matches,
                "match_count": match_count,
                "total_symptoms": len(condition["symptoms"]),
                "treatment": condition["treatment"],
                "see_doctor": condition["see_doctor"]
            })
    
    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results[:5]

def check_emergency(symptoms):
    emergency = ["chest pain", "difficulty breathing", "severe bleeding", "loss of consciousness", "seizure"]
    for s in symptoms:
        if s.lower() in emergency:
            return True
    return False

def generate_condition_advice(condition, age, duration):
    condition_advice = {
        "Common Cold": {
            "rest": "Rest is crucial for recovery from cold.",
            "hydration": "Drink warm fluids like tea with honey to soothe your throat.",
            "specific": "Use saline nasal spray for congestion. Gargle with salt water for sore throat.",
            "when_to_see_doctor": "See a doctor if fever exceeds 101°F or symptoms last more than 10 days."
        },
        "Influenza (Flu)": {
            "rest": "Get plenty of rest - the flu requires significant energy to fight.",
            "hydration": "Drink electrolyte solutions to prevent dehydration from fever.",
            "specific": "Take fever reducers. Stay home to avoid spreading the virus.",
            "when_to_see_doctor": "Seek medical care if you have difficulty breathing or chest pain."
        },
        "COVID-19": {
            "rest": "Isolate immediately. Rest is essential for recovery.",
            "hydration": "Stay well hydrated. Monitor your oxygen levels.",
            "specific": "Monitor for emergency warning signs: trouble breathing, chest pain, confusion.",
            "when_to_see_doctor": "Seek emergency care immediately if you have difficulty breathing."
        },
        "Seasonal Allergies": {
            "rest": "Allergies may cause fatigue - rest when needed.",
            "hydration": "Drink water to thin mucus. Use a humidifier.",
            "specific": "Take antihistamines. Avoid known allergens. Shower after being outdoors.",
            "when_to_see_doctor": "See an allergist if symptoms interfere with daily activities."
        },
        "Migraine Headache": {
            "rest": "Rest in a dark, quiet room.",
            "hydration": "Stay hydrated - dehydration can trigger migraines.",
            "specific": "Apply cold compress to forehead. Avoid known triggers.",
            "when_to_see_doctor": "See a doctor if migraines are frequent or severe."
        },
        "Acute Bronchitis": {
            "rest": "Rest to help your body fight the infection.",
            "hydration": "Drink warm fluids to loosen mucus.",
            "specific": "Use a humidifier. Avoid smoke and irritants.",
            "when_to_see_doctor": "See a doctor if cough persists more than 3 weeks."
        },
        "Gastroenteritis (Stomach Flu)": {
            "rest": "Rest your stomach - avoid solid foods initially.",
            "hydration": "Sip clear fluids or oral rehydration solutions frequently.",
            "specific": "Follow the BRAT diet (Bananas, Rice, Applesauce, Toast).",
            "when_to_see_doctor": "Seek care if you can't keep liquids down for 24 hours."
        },
        "Sinus Infection": {
            "rest": "Rest with head elevated to help sinus drainage.",
            "hydration": "Drink plenty of water to thin nasal mucus.",
            "specific": "Use saline nasal irrigation. Apply warm compresses to your face.",
            "when_to_see_doctor": "See a doctor if symptoms last more than 10 days."
        },
        "Strep Throat": {
            "rest": "Rest your voice and body.",
            "hydration": "Drink warm soothing liquids like tea with honey.",
            "specific": "Gargle with warm salt water. Use throat lozenges for pain.",
            "when_to_see_doctor": "See a doctor promptly - strep throat requires antibiotics."
        }
    }
    
    default_advice = {
        "rest": "Get adequate rest (7-9 hours of sleep daily)",
        "hydration": "Drink plenty of water (8-10 glasses daily)",
        "specific": "Monitor your symptoms and rest as needed.",
        "when_to_see_doctor": "Consult a doctor if symptoms worsen or persist beyond 5-7 days"
    }
    
    specific = condition_advice.get(condition, default_advice)
    
    age_advice = ""
    if age and age.isdigit():
        age_num = int(age)
        if age_num > 60:
            age_advice = "⚠️ As an older adult (65+), you're at higher risk. Seek care earlier if concerned."
        elif age_num < 12:
            age_advice = "⚠️ For children, monitor hydration carefully. Consult a pediatrician if fever persists."
    
    duration_advice = ""
    if duration == "more_than_week":
        duration_advice = "⚠️ Your symptoms have persisted over a week. Medical evaluation is recommended."
    
    return {
        "rest": specific["rest"],
        "hydration": specific["hydration"],
        "specific_advice": specific["specific"],
        "when_to_see_doctor": specific["when_to_see_doctor"],
        "age_advice": age_advice,
        "duration_advice": duration_advice
    }

# ==================== HEALTH STATISTICS FUNCTION ====================
def get_health_statistics(user_id):
    diagnoses = Diagnosis.query.filter_by(user_id=user_id).all()
    
    conditions = defaultdict(int)
    months = defaultdict(int)
    total_confidence = 0
    
    for d in diagnoses:
        if d.predicted_condition:
            conditions[d.predicted_condition] += 1
        if d.created_at:
            month_key = d.created_at.strftime('%B %Y')
            months[month_key] += 1
        total_confidence += d.confidence_score or 0
    
    return {
        'conditions': dict(conditions),
        'monthly_trend': dict(months),
        'total_diagnoses': len(diagnoses),
        'avg_confidence': round(total_confidence / len(diagnoses), 1) if diagnoses else 0,
        'doctor_recommended_count': sum(1 for d in diagnoses if d.doctor_recommended)
    }

# ==================== USER LOADER ====================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== ROUTES ====================
@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        
        valid, msg = validate_registration(username, email, password, confirm)
        if not valid:
            flash(msg, 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))
        
        user = User(
            username=sanitize_input(username),
            email=email.lower(),
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template_string(REGISTER_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = sanitize_input(request.form.get('username'))
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'danger')
    
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    
    diagnoses = Diagnosis.query.filter_by(user_id=current_user.id).order_by(Diagnosis.created_at.desc()).all()
    total_diagnoses = len(diagnoses)
    
    stats = get_health_statistics(current_user.id)
    
    return render_template_string(DASHBOARD_HTML, 
                                 diagnoses=diagnoses, 
                                 total_diagnoses=total_diagnoses,
                                 stats=stats,
                                 truncate_text=truncate_text, 
                                 format_date=format_date)

@app.route('/diagnose')
@login_required
def diagnose_page():
    return render_template_string(DIAGNOSE_HTML)

@app.route('/api/diagnose', methods=['POST'])
@login_required
@handle_errors("Failed to process diagnosis")
def api_diagnose():
    data = request.get_json()
    symptoms = data.get('symptoms', [])
    age = data.get('age', '')
    duration = data.get('duration', '')
    
    if not symptoms:
        return jsonify({"error": "Please enter at least one symptom"}), 400
    
    results = get_diagnosis(symptoms)
    is_emergency = check_emergency(symptoms)
    
    if results:
        top = results[0]
        diagnosis = Diagnosis(
            user_id=current_user.id,
            symptoms=', '.join(symptoms),
            predicted_condition=top['condition'],
            confidence_score=top['confidence'],
            treatment_advice=top['treatment'],
            doctor_recommended=top['see_doctor']
        )
        db.session.add(diagnosis)
        db.session.commit()
        
        personalized_advice = generate_condition_advice(top['condition'], age, duration)
    else:
        personalized_advice = generate_condition_advice(None, age, duration)
    
    return jsonify({
        "success": True,
        "diagnosis": results,
        "emergency_warning": is_emergency,
        "patient_info": {
            "age": age if age else "Not provided",
            "duration": duration if duration else "Not specified",
            "symptom_count": len(symptoms)
        },
        "advice": personalized_advice
    })

@app.route('/api/health-stats')
@login_required
def health_stats():
    stats = get_health_statistics(current_user.id)
    return jsonify(stats)

@app.route('/api/daily-tip')
def daily_tip():
    tip = random.choice(HEALTH_TIPS)
    return jsonify({'tip': tip, 'date': datetime.now().strftime('%Y-%m-%d')})

@app.route('/export-data')
@login_required
def export_patient_data():
    """Export patient medical data as downloadable JSON file"""
    diagnoses = Diagnosis.query.filter_by(user_id=current_user.id).order_by(Diagnosis.created_at.desc()).all()
    
    data = {
        'export_date': datetime.now().isoformat(),
        'patient_name': current_user.username,
        'patient_email': current_user.email,
        'total_diagnoses': len(diagnoses),
        'diagnoses': []
    }
    
    for d in diagnoses:
        data['diagnoses'].append({
            'id': d.id,
            'date': d.created_at.isoformat(),
            'symptoms': d.symptoms,
            'diagnosis': d.predicted_condition,
            'confidence_score': d.confidence_score,
            'treatment': d.treatment_advice,
            'doctor_recommended': d.doctor_recommended
        })
    
    json_data = json.dumps(data, indent=2, ensure_ascii=False)
    
    filename = f"medical_history_{current_user.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    return Response(
        json_data,
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

@app.route('/export-csv')
@login_required
def export_patient_csv():
    """Export patient medical data as downloadable CSV file"""
    diagnoses = Diagnosis.query.filter_by(user_id=current_user.id).order_by(Diagnosis.created_at.desc()).all()
    
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['Date', 'Symptoms', 'Diagnosis', 'Confidence (%)', 'Treatment', 'Doctor Recommended'])
    
    for d in diagnoses:
        writer.writerow([
            d.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            d.symptoms,
            d.predicted_condition or 'N/A',
            d.confidence_score or 0,
            d.treatment_advice or 'N/A',
            'Yes' if d.doctor_recommended else 'No'
        ])
    
    output.seek(0)
    filename = f"medical_history_{current_user.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

@app.route('/report/<int:diagnosis_id>')
@login_required
def download_report(diagnosis_id):
    """Generate and download PDF report for a diagnosis"""
    diagnosis = Diagnosis.query.get_or_404(diagnosis_id)
    
    # Check permission
    if diagnosis.user_id != current_user.id and current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if reportlab is available
    if not REPORTLAB_AVAILABLE:
        flash('PDF generation not available. Please install reportlab: pip install reportlab', 'danger')
        # Fallback to HTML report
        return generate_html_report(diagnosis)
    
    try:
        pdf_buffer = generate_pdf_report(diagnosis, diagnosis.user)
        
        if pdf_buffer:
            filename = f"diagnosis_report_{diagnosis.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
        else:
            flash('Failed to generate PDF report', 'danger')
            return redirect(url_for('dashboard'))
    except Exception as e:
        print(f"PDF Generation Error: {str(e)}")
        flash(f'Error generating PDF report: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

def generate_html_report(diagnosis):
    """Generate HTML report as fallback when PDF is not available"""
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Medical Diagnosis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ text-align: center; color: #2563eb; }}
            .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }}
            .emergency {{ background: #fee2e2; border-left: 4px solid #dc2626; }}
            @media print {{
                .no-print {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="no-print" style="text-align: right; margin-bottom: 20px;">
            <button onclick="window.print()">🖨️ Print / Save as PDF</button>
            <button onclick="window.close()">❌ Close</button>
        </div>
        
        <div class="header">
            <h1>🏥 AI Medical Diagnosis Report</h1>
            <p>Report ID: #{diagnosis.id} | Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="section">
            <h2>📋 PATIENT INFORMATION</h2>
            <p><strong>Name:</strong> {diagnosis.user.username}</p>
            <p><strong>Email:</strong> {diagnosis.user.email}</p>
        </div>
        
        <div class="section">
            <h2>🩺 DIAGNOSIS INFORMATION</h2>
            <p><strong>Date:</strong> {diagnosis.created_at.strftime('%Y-%m-%d %H:%M')}</p>
            <p><strong>Symptoms:</strong> {diagnosis.symptoms}</p>
            <p><strong>Diagnosis:</strong> {diagnosis.predicted_condition or 'Analysis in progress'}</p>
            <p><strong>Confidence Score:</strong> {diagnosis.confidence_score}%</p>
        </div>
        
        <div class="section">
            <h2>💊 TREATMENT RECOMMENDATIONS</h2>
            <p>{diagnosis.treatment_advice or 'No specific treatment advice available. Please consult a healthcare provider.'}</p>
        </div>
        
        {'<div class="section emergency"><h2>⚠️ IMPORTANT</h2><p>Please consult a healthcare provider for proper evaluation and treatment.</p></div>' if diagnosis.doctor_recommended else ''}
        
        <div class="section">
            <h2>💡 GENERAL HEALTH ADVICE</h2>
            <ul>
                <li>Get adequate rest (7-9 hours of sleep daily)</li>
                <li>Stay hydrated (8-10 glasses of water per day)</li>
                <li>Monitor your symptoms and track temperature</li>
                <li>Maintain a healthy diet to support recovery</li>
            </ul>
        </div>
        
        <div class="section">
            <p style="font-size: 12px; color: #666; text-align: center;">
                <strong>Disclaimer:</strong> This report is generated by an AI system for informational purposes only.<br>
                It is not a substitute for professional medical advice, diagnosis, or treatment.
            </p>
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/admin')
@login_required
@admin_required
@handle_errors("Failed to load admin dashboard")
def admin_dashboard():
    users = User.query.all()
    diagnoses = Diagnosis.query.all()
    return render_template_string(ADMIN_DASHBOARD_HTML, 
                                 users=users, 
                                 diagnoses=diagnoses,
                                 truncate_text=truncate_text, 
                                 format_date=format_date)

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.role == 'admin':
        flash('Cannot delete admin users!', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    Diagnosis.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User "{user.username}" has been deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-diagnosis/<int:diagnosis_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_diagnosis(diagnosis_id):
    diagnosis = Diagnosis.query.get_or_404(diagnosis_id)
    db.session.delete(diagnosis)
    db.session.commit()
    
    flash('Diagnosis record has been deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-all-diagnoses', methods=['POST'])
@login_required
@admin_required
def admin_delete_all_diagnoses():
    count = Diagnosis.query.count()
    Diagnosis.query.delete()
    db.session.commit()
    
    flash(f'All {count} diagnosis records have been deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-all-users', methods=['POST'])
@login_required
@admin_required
def admin_delete_all_users():
    users = User.query.filter(User.role != 'admin').all()
    count = len(users)
    
    for user in users:
        Diagnosis.query.filter_by(user_id=user.id).delete()
        db.session.delete(user)
    
    db.session.commit()
    
    flash(f'All {count} non-admin users have been deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

# ==================== HTML TEMPLATES ====================
INDEX_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Medical Diagnosis System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .hero-card { background: white; border-radius: 20px; padding: 50px; margin-top: 50px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); }
        .btn-gradient { background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; }
        .btn-gradient:hover { transform: scale(1.05); box-shadow: 0 4px 12px rgba(102,126,234,0.4); }
        .feature-card { transition: transform 0.3s; }
        .feature-card:hover { transform: translateY(-5px); }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏥 AI Medical Diagnosis</a>
            <div class="navbar-nav ms-auto">
                {% if current_user.is_authenticated %}
                    <span class="nav-link text-light">Welcome, {{ current_user.username }}</span>
                    <a class="nav-link" href="/dashboard">Dashboard</a>
                    <a class="nav-link" href="/diagnose">Diagnosis</a>
                    {% if current_user.role == 'admin' %}
                        <a class="nav-link" href="/admin">Admin</a>
                    {% endif %}
                    <a class="nav-link" href="/logout">Logout</a>
                {% else %}
                    <a class="nav-link" href="/login">Login</a>
                    <a class="nav-link" href="/register">Register</a>
                {% endif %}
            </div>
        </div>
    </nav>
    
    <div class="container">
        <div class="alert alert-info text-center mt-3" id="dailyTip">
            <i class="fas fa-lightbulb"></i> Loading health tip...
        </div>
        
        <div class="hero-card text-center">
            <i class="fas fa-brain fa-4x" style="color: #667eea;"></i>
            <h1 class="display-4 fw-bold mt-3">AI Medical Diagnosis Assistant</h1>
            <p class="lead mt-3">Advanced symptom checker powered by artificial intelligence</p>
            <hr class="my-4">
            <p>Enter your symptoms and get AI-powered preliminary diagnosis, treatment recommendations, and medical advice.</p>
            {% if current_user.is_authenticated %}
                <a href="/diagnose" class="btn btn-gradient btn-lg mt-3"><i class="fas fa-stethoscope"></i> Start Diagnosis</a>
            {% else %}
                <a href="/register" class="btn btn-gradient btn-lg mt-3"><i class="fas fa-user-plus"></i> Get Started</a>
            {% endif %}
        </div>
        
        <div class="row mt-5 mb-5">
            <div class="col-md-4 mb-3">
                <div class="card feature-card text-center h-100">
                    <div class="card-body">
                        <i class="fas fa-robot fa-3x" style="color: #667eea;"></i>
                        <h5 class="mt-3">AI-Powered Analysis</h5>
                        <p>Advanced algorithms analyze your symptoms</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4 mb-3">
                <div class="card feature-card text-center h-100">
                    <div class="card-body">
                        <i class="fas fa-chart-line fa-3x" style="color: #667eea;"></i>
                        <h5 class="mt-3">Health Analytics</h5>
                        <p>Track your health trends over time</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4 mb-3">
                <div class="card feature-card text-center h-100">
                    <div class="card-body">
                        <i class="fas fa-file-pdf fa-3x" style="color: #667eea;"></i>
                        <h5 class="mt-3">PDF Reports</h5>
                        <p>Generate and share medical reports</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        fetch('/api/daily-tip')
            .then(res => res.json())
            .then(data => {
                document.getElementById('dailyTip').innerHTML = `<i class="fas fa-lightbulb"></i> 💡 Health Tip: ${data.tip}`;
            });
    </script>
</body>
</html>
'''

REGISTER_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Register - AI Medical Diagnosis</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .card { border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-5">
                <div class="card">
                    <div class="card-header bg-primary text-white text-center">
                        <h4><i class="fas fa-user-plus"></i> Create Account</h4>
                    </div>
                    <div class="card-body">
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% for category, message in messages %}
                                <div class="alert alert-{{ category }}">{{ message }}</div>
                            {% endfor %}
                        {% endwith %}
                        <form method="POST">
                            <div class="mb-3">
                                <label>Username</label>
                                <input type="text" name="username" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label>Email</label>
                                <input type="email" name="email" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label>Password</label>
                                <input type="password" name="password" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label>Confirm Password</label>
                                <input type="password" name="confirm_password" class="form-control" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Register</button>
                        </form>
                    </div>
                    <div class="card-footer text-center">
                        <p>Already have an account? <a href="/login">Login here</a></p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Login - AI Medical Diagnosis</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .card { border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-5">
                <div class="card">
                    <div class="card-header bg-primary text-white text-center">
                        <h4><i class="fas fa-sign-in-alt"></i> Login</h4>
                    </div>
                    <div class="card-body">
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% for category, message in messages %}
                                <div class="alert alert-{{ category }}">{{ message }}</div>
                            {% endfor %}
                        {% endwith %}
                        <form method="POST">
                            <div class="mb-3">
                                <label>Username</label>
                                <input type="text" name="username" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label>Password</label>
                                <input type="password" name="password" class="form-control" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Login</button>
                        </form>
                    </div>
                    <div class="card-footer text-center">
                        <p>Don't have an account? <a href="/register">Register here</a></p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - AI Medical Diagnosis</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .confidence-high { background-color: #22c55e; color: white; padding: 2px 8px; border-radius: 20px; display: inline-block; }
        .confidence-medium { background-color: #f59e0b; color: white; padding: 2px 8px; border-radius: 20px; display: inline-block; }
        .confidence-low { background-color: #ef4444; color: white; padding: 2px 8px; border-radius: 20px; display: inline-block; }
        .btn-pdf { background-color: #dc2626; color: white; padding: 4px 10px; border-radius: 5px; text-decoration: none; font-size: 12px; }
        .btn-pdf:hover { background-color: #b91c1c; color: white; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏥 AI Medical Diagnosis</a>
            <div class="navbar-nav ms-auto">
                <span class="nav-link text-light">Welcome, {{ current_user.username }}</span>
                <a class="nav-link" href="/dashboard">Dashboard</a>
                <a class="nav-link" href="/diagnose">Diagnosis</a>
                <a class="nav-link" href="/logout">Logout</a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        <h2><i class="fas fa-tachometer-alt"></i> Patient Dashboard</h2>
        
        <div class="row mt-4">
            <div class="col-md-3">
                <div class="card bg-primary text-white">
                    <div class="card-body text-center">
                        <h2 class="display-4">{{ stats.total_diagnoses }}</h2>
                        <p>Total Diagnoses</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-success text-white">
                    <div class="card-body text-center">
                        <h2 class="display-4">{{ stats.doctor_recommended_count }}</h2>
                        <p>Doctor Recommended</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-info text-white">
                    <div class="card-body text-center">
                        <h2 class="display-4">{{ stats.avg_confidence }}%</h2>
                        <p>Avg Confidence</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-warning text-white">
                    <div class="card-body text-center">
                        <h2 class="display-4">{{ stats.conditions|length }}</h2>
                        <p>Conditions</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header bg-info text-white">
                        <h5><i class="fas fa-chart-bar"></i> Most Common Conditions</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="conditionsChart" height="200"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header bg-info text-white">
                        <h5><i class="fas fa-chart-line"></i> Monthly Trend</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="trendChart" height="200"></canvas>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-3">
            <div class="col-12 text-end">
                <div class="btn-group">
                    <a href="/export-data" class="btn btn-success">
                        <i class="fas fa-download"></i> Export as JSON
                    </a>
                    <a href="/export-csv" class="btn btn-info">
                        <i class="fas fa-file-excel"></i> Export as CSV
                    </a>
                </div>
            </div>
        </div>
        
        <div class="card mt-4">
            <div class="card-header">
                <h5><i class="fas fa-history"></i> Recent Diagnoses</h5>
            </div>
            <div class="card-body">
                {% if diagnoses %}
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr><th>Date</th><th>Symptoms</th><th>Diagnosis</th><th>Confidence</th><th>Doctor</th><th>Report</th></tr>
                        </thead>
                        <tbody>
                            {% for d in diagnoses[:10] %}
                            <tr>
                                <td>{{ format_date(d.created_at, '%Y-%m-%d') }}</td>
                                <td>{{ truncate_text(d.symptoms, 40) }}</td>
                                <td>{{ d.predicted_condition }}</td>
                                <td>
                                    {% set conf = d.confidence_score|float %}
                                    {% if conf >= 70 %}
                                        <span class="confidence-high">{{ conf }}%</span>
                                    {% elif conf >= 40 %}
                                        <span class="confidence-medium">{{ conf }}%</span>
                                    {% else %}
                                        <span class="confidence-low">{{ conf }}%</span>
                                    {% endif %}
                                </td>
                                <td>{% if d.doctor_recommended %}⚠️ Yes{% else %}No{% endif %}</td>
                                <td>
                                    <a href="{{ url_for('download_report', diagnosis_id=d.id) }}" class="btn-pdf" target="_blank">
                                        <i class="fas fa-file-pdf"></i> PDF
                                    </a>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <p class="text-center">No diagnoses yet. <a href="/diagnose">Start your first diagnosis</a></p>
                {% endif %}
            </div>
        </div>
        
        <div class="text-center mt-3">
            <a href="/diagnose" class="btn btn-primary"><i class="fas fa-stethoscope"></i> New Diagnosis</a>
        </div>
    </div>
    
    <script>
        fetch('/api/health-stats')
            .then(res => res.json())
            .then(data => {
                const conditionsLabels = Object.keys(data.conditions);
                const conditionsValues = Object.values(data.conditions);
                
                if (conditionsLabels.length > 0) {
                    new Chart(document.getElementById('conditionsChart'), {
                        type: 'bar',
                        data: {
                            labels: conditionsLabels,
                            datasets: [{
                                label: 'Number of Diagnoses',
                                data: conditionsValues,
                                backgroundColor: '#667eea',
                                borderRadius: 5
                            }]
                        }
                    });
                }
                
                const monthsLabels = Object.keys(data.monthly_trend);
                const monthsValues = Object.values(data.monthly_trend);
                
                if (monthsLabels.length > 0) {
                    new Chart(document.getElementById('trendChart'), {
                        type: 'line',
                        data: {
                            labels: monthsLabels,
                            datasets: [{
                                label: 'Diagnoses per Month',
                                data: monthsValues,
                                borderColor: '#22c55e',
                                backgroundColor: 'rgba(34, 197, 94, 0.1)',
                                fill: true,
                                tension: 0.4
                            }]
                        }
                    });
                }
            });
    </script>
</body>
</html>
'''

DIAGNOSE_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Medical Diagnosis - AI Medical Diagnosis</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        .symptom-tag { background: #667eea; color: white; padding: 5px 12px; border-radius: 20px; display: inline-block; margin: 5px; cursor: pointer; }
        .symptom-tag i { margin-left: 8px; }
        .result-item { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 10px; border-left: 4px solid #667eea; }
        .emergency { background: #fee2e2; border-left-color: #dc2626; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏥 AI Medical Diagnosis</a>
            <div class="navbar-nav ms-auto">
                <span class="nav-link text-light">Welcome, {{ current_user.username }}</span>
                <a class="nav-link" href="/dashboard">Dashboard</a>
                <a class="nav-link" href="/diagnose">Diagnosis</a>
                <a class="nav-link" href="/logout">Logout</a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        <div class="row">
            <div class="col-md-5">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h5><i class="fas fa-notes-medical"></i> Enter Your Symptoms</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <div class="input-group">
                                <input type="text" id="symptomInput" class="form-control" placeholder="e.g., fever, headache, cough">
                                <button class="btn btn-primary" onclick="addSymptom()">Add</button>
                            </div>
                        </div>
                        <div id="symptomsList" class="mb-3" style="min-height: 80px; background: #f8f9fa; padding: 10px; border-radius: 8px;">
                            <p class="text-muted">No symptoms added</p>
                        </div>
                        <div class="mb-3">
                            <label>Age (optional)</label>
                            <input type="number" id="age" class="form-control" placeholder="e.g., 35">
                        </div>
                        <div class="mb-3">
                            <label>Duration</label>
                            <select id="duration" class="form-select">
                                <option value="">Select duration</option>
                                <option value="less_than_24h">Less than 24h</option>
                                <option value="1_3_days">1-3 days</option>
                                <option value="4_7_days">4-7 days</option>
                                <option value="more_than_week">More than a week</option>
                            </select>
                        </div>
                        <button class="btn btn-success w-100 mb-2" onclick="getDiagnosis()">Get Diagnosis</button>
                        <button class="btn btn-secondary w-100" onclick="clearAll()">Clear All</button>
                    </div>
                </div>
            </div>
            <div class="col-md-7">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h5><i class="fas fa-chart-line"></i> Diagnosis Results</h5>
                    </div>
                    <div class="card-body" id="resultsContainer">
                        <p class="text-center text-muted">Add symptoms and click "Get Diagnosis"</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let symptoms = [];
        
        function addSymptom() {
            const input = document.getElementById('symptomInput');
            const symptom = input.value.trim().toLowerCase();
            if (symptom && !symptoms.includes(symptom)) {
                symptoms.push(symptom);
                updateSymptomsList();
                input.value = '';
            }
        }
        
        function removeSymptom(index) {
            symptoms.splice(index, 1);
            updateSymptomsList();
        }
        
        function updateSymptomsList() {
            const container = document.getElementById('symptomsList');
            if (symptoms.length === 0) {
                container.innerHTML = '<p class="text-muted">No symptoms added</p>';
                return;
            }
            container.innerHTML = symptoms.map((s, i) => 
                `<span class="symptom-tag">${s} <i class="fas fa-times" onclick="removeSymptom(${i})"></i></span>`
            ).join('');
        }
        
        function clearAll() {
            symptoms = [];
            updateSymptomsList();
            document.getElementById('age').value = '';
            document.getElementById('duration').value = '';
            document.getElementById('resultsContainer').innerHTML = '<p class="text-center text-muted">Add symptoms and click "Get Diagnosis"</p>';
        }
        
        async function getDiagnosis() {
            if (symptoms.length === 0) {
                alert('Please add at least one symptom');
                return;
            }
            
            document.getElementById('resultsContainer').innerHTML = '<div class="text-center"><div class="spinner-border text-primary"></div><p>Analyzing symptoms...</p></div>';
            
            try {
                const response = await fetch('/api/diagnose', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        symptoms: symptoms,
                        age: document.getElementById('age').value,
                        duration: document.getElementById('duration').value
                    })
                });
                const data = await response.json();
                displayResults(data);
            } catch (error) {
                document.getElementById('resultsContainer').innerHTML = '<div class="alert alert-danger">Error connecting to server.</div>';
            }
        }
        
        function displayResults(data) {
            let html = '';
            
            if (data.emergency_warning) {
                html += '<div class="result-item emergency"><strong>⚠️ EMERGENCY WARNING</strong><br>Seek immediate medical attention!</div>';
            }
            
            html += `<div class="result-item"><strong>Patient Summary:</strong><br>Age: ${data.patient_info.age} | Duration: ${data.patient_info.duration} | Symptoms: ${data.patient_info.symptom_count}</div>`;
            
            if (data.diagnosis && data.diagnosis.length > 0) {
                data.diagnosis.forEach(d => {
                    let confidenceClass = d.confidence >= 70 ? 'text-success fw-bold' : (d.confidence >= 40 ? 'text-warning fw-bold' : 'text-danger fw-bold');
                    html += `<div class="result-item">
                                <strong>${d.condition}</strong> 
                                <span class="${confidenceClass}">(${d.confidence}% match)</span><br>
                                <small>Matched: ${d.matched_symptoms.join(', ')} (${d.match_count}/${d.total_symptoms})</small><br>
                                <strong>Treatment:</strong> ${d.treatment}<br>
                                ${d.see_doctor ? '<span class="text-warning">⚠️ Consider consulting a doctor</span>' : ''}
                            </div>`;
                });
            } else {
                html += '<div class="result-item">No specific conditions matched. Monitor symptoms.</div>';
            }
            
            if (data.advice) {
                html += `<div class="result-item">
                            <strong><i class="fas fa-heartbeat"></i> 💡 Personalized Medical Advice</strong><br><br>
                            <i class="fas fa-bed"></i> <strong>Rest:</strong> ${data.advice.rest}<br>
                            <i class="fas fa-tint"></i> <strong>Hydration:</strong> ${data.advice.hydration}<br>
                            <i class="fas fa-stethoscope"></i> <strong>Specific Care:</strong> ${data.advice.specific_advice}<br>
                            <i class="fas fa-ambulance"></i> <strong>When to See a Doctor:</strong> ${data.advice.when_to_see_doctor}
                        </div>`;
            }
            
            document.getElementById('resultsContainer').innerHTML = html;
        }
        
        document.getElementById('symptomInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') addSymptom();
        });
    </script>
</body>
</html>
'''

ADMIN_DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Admin Dashboard - AI Medical Diagnosis</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        .btn-delete { background-color: #dc2626; color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer; font-size: 12px; }
        .btn-delete:hover { background-color: #b91c1c; }
        .btn-pdf { background-color: #dc2626; color: white; padding: 4px 10px; border-radius: 5px; text-decoration: none; font-size: 12px; }
        .btn-pdf:hover { background-color: #b91c1c; color: white; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏥 AI Medical Diagnosis</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/dashboard">Dashboard</a>
                <a class="nav-link" href="/admin">Admin</a>
                <a class="nav-link" href="/logout">Logout</a>
                <span class="nav-link text-light"><i class="fas fa-user-shield"></i> {{ current_user.username }}</span>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        <h2><i class="fas fa-chart-line"></i> Admin Dashboard</h2>
        <p class="text-muted">Manage users and diagnoses</p>
        
        <div class="row mt-4">
            <div class="col-md-4">
                <div class="card bg-primary text-white">
                    <div class="card-body text-center">
                        <h2 class="display-4">{{ users|length }}</h2>
                        <p>Total Users</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card bg-success text-white">
                    <div class="card-body text-center">
                        <h2 class="display-4">{{ diagnoses|length }}</h2>
                        <p>Total Diagnoses</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card bg-danger text-white">
                    <div class="card-body text-center">
                        <form method="POST" action="/admin/delete-all-diagnoses" onsubmit="return confirm('Delete ALL diagnoses?');">
                            <button type="submit" class="btn btn-light btn-sm">Delete All Diagnoses</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card mt-4">
            <div class="card-header bg-primary text-white">
                <h5><i class="fas fa-users"></i> System Users</h5>
            </div>
            <div class="card-body">
                <table class="table table-bordered">
                    <thead class="table-dark">
                        <tr><th>ID</th><th>Username</th><th>Email</th><th>Role</th><th>Diagnoses</th><th>Action</th></tr>
                    </thead>
                    <tbody>
                        {% for u in users %}
                        <tr>
                            <td>{{ u.id }}</td>
                            <td>{{ u.username }}</td>
                            <td>{{ u.email }}</td>
                            <td>{% if u.role == 'admin' %}Admin{% else %}Patient{% endif %}</td>
                            <td>{{ u.diagnoses|length }}</td>
                            <td>
                                {% if u.role != 'admin' %}
                                    <form method="POST" action="/admin/delete-user/{{ u.id }}" onsubmit="return confirm('Delete {{ u.username }}?');">
                                        <button type="submit" class="btn-delete">Delete</button>
                                    </form>
                                {% else %}
                                    <span class="text-muted">Protected</span>
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="card mt-4">
            <div class="card-header bg-success text-white">
                <h5><i class="fas fa-stethoscope"></i> All Diagnoses</h5>
            </div>
            <div class="card-body">
                <table class="table table-bordered">
                    <thead class="table-dark">
                        <tr><th>ID</th><th>Patient</th><th>Symptoms</th><th>Diagnosis</th><th>Confidence</th><th>Date</th><th>Report</th><th>Action</th></tr>
                    </thead>
                    <tbody>
                        {% for d in diagnoses %}
                        <tr>
                            <td>{{ d.id }}</td>
                            <td>{{ d.user.username }}</td>
                            <td>{{ truncate_text(d.symptoms, 40) }}</td>
                            <td>{{ d.predicted_condition }}</td>
                            <td>{{ d.confidence_score }}%</span></td>
                            <td>{{ format_date(d.created_at, '%Y-%m-%d') }}</td>
                            <td><a href="{{ url_for('download_report', diagnosis_id=d.id) }}" class="btn-pdf" target="_blank">PDF</a></td>
                            <td>
                                <form method="POST" action="/admin/delete-diagnosis/{{ d.id }}" onsubmit="return confirm('Delete this diagnosis?');">
                                    <button type="submit" class="btn-delete">Delete</button>
                                </form>
                            </td>
                        </td>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
'''

# ==================== CREATE DATABASE ====================
with app.app_context():
    db.drop_all()
    db.create_all()
    print("✅ Database created")
    
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@medical.com',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin created: admin / admin123")
    
    if not User.query.filter_by(username='testuser').first():
        test = User(
            username='testuser',
            email='test@medical.com',
            password_hash=generate_password_hash('test123'),
            role='patient'
        )
        db.session.add(test)
        db.session.commit()
        print("✅ Test user: testuser / test123")

# ==================== RUN ====================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🏥 AI MEDICAL DIAGNOSIS SYSTEM - FULLY FUNCTIONAL")
    print("="*60)
    print("📍 Access at: http://127.0.0.1:5000")
    print("👑 Admin: admin / admin123")
    print("👤 Patient: testuser / test123")
    print("="*60)
    
    if REPORTLAB_AVAILABLE:
        print("✅ PDF Report Generation: ENABLED")
    else:
        print("⚠️ PDF Report Generation: DISABLED (Run: pip install reportlab)")
    
    print("📊 Export Features: JSON and CSV available")
    print("="*60 + "\n")
    app.run(debug=True, host='127.0.0.1', port=5000)