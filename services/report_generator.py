from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
from flask import send_file
from datetime import datetime

def generate_pdf_report(diagnosis, user):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2563eb'),
        alignment=1
    )
    story.append(Paragraph("Medical Diagnosis Report", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Patient Info
    story.append(Paragraph(f"<b>Patient:</b> {user.username}", styles['Normal']))
    story.append(Paragraph(f"<b>Date:</b> {diagnosis.created_at.strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Symptoms
    story.append(Paragraph("<b>Symptoms Reported:</b>", styles['Heading2']))
    story.append(Paragraph(diagnosis.symptoms, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Diagnosis
    story.append(Paragraph("<b>Diagnosis:</b>", styles['Heading2']))
    story.append(Paragraph(diagnosis.predicted_condition or "Analysis in progress", styles['Normal']))
    story.append(Paragraph(f"<b>Confidence Score:</b> {diagnosis.confidence_score}%", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Recommendations
    story.append(Paragraph("<b>Recommendations:</b>", styles['Heading2']))
    story.append(Paragraph("• Rest adequately", styles['Normal']))
    story.append(Paragraph("• Stay hydrated", styles['Normal']))
    story.append(Paragraph("• Monitor symptoms", styles['Normal']))
    
    if diagnosis.doctor_recommended:
        story.append(Paragraph("<b><font color='red'>⚠️ Please consult a healthcare provider</font></b>", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f"diagnosis_report_{diagnosis.id}.pdf", mimetype='application/pdf')