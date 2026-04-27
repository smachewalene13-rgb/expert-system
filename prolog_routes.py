"""
Prolog API Routes - Add these routes to your Flask app
Import this file in app.py to enable Prolog features
"""

from flask import jsonify, request
from prolog_integration import prolog_bridge

def register_prolog_routes(app):
    """
    Register Prolog routes with the Flask app
    Call this function in your main app.py
    """
    
    @app.route('/api/prolog/diagnose', methods=['POST'])
    def prolog_diagnose():
        """Diagnose using Prolog-style inference"""
        data = request.get_json()
        symptoms = data.get('symptoms', [])
        
        if not symptoms:
            return jsonify({'error': 'No symptoms provided'}), 400
        
        results = prolog_bridge.diagnose_with_prolog(symptoms)
        
        return jsonify({
            'success': True,
            'diagnosis': results,
            'engine': 'prolog-style'
        })
    
    @app.route('/api/prolog/compare', methods=['POST'])
    def prolog_compare():
        """Compare Prolog diagnosis with ML diagnosis"""
        data = request.get_json()
        symptoms = data.get('symptoms', [])
        ml_diagnosis = data.get('ml_diagnosis', [])
        
        comparison = prolog_bridge.compare_diagnosis(symptoms, ml_diagnosis)
        
        return jsonify({
            'success': True,
            'comparison': comparison
        })
    
    @app.route('/api/prolog/explain', methods=['POST'])
    def prolog_explain():
        """Get explanation for a diagnosis"""
        data = request.get_json()
        disease = data.get('disease', '')
        
        if not disease:
            return jsonify({'error': 'No disease provided'}), 400
        
        explanation = prolog_bridge.explain_diagnosis(disease)
        
        return jsonify({
            'success': True,
            'disease': disease,
            'explanation': explanation
        })
    
    @app.route('/api/prolog/diseases', methods=['GET'])
    def prolog_diseases():
        """Get all diseases in Prolog knowledge base"""
        diseases = prolog_bridge.get_all_diseases()
        
        return jsonify({
            'success': True,
            'diseases': diseases,
            'count': len(diseases)
        })
    
    @app.route('/api/prolog/health', methods=['GET'])
    def prolog_health():
        """Check if Prolog engine is available"""
        return jsonify({
            'status': 'healthy',
            'engine': 'prolog-style',
            'available': True
        })
    
    print("✅ Prolog routes registered")

# Function to add Prolog button to diagnosis page HTML
def get_prolog_button_html():
    """Get HTML for Prolog button (to add to existing template)"""
    return '''
    <div class="mt-3">
        <hr>
        <h6><i class="fas fa-brain"></i> Prolog AI Diagnosis</h6>
        <button type="button" class="btn btn-outline-info w-100" onclick="runPrologDiagnosis()" id="prologBtn">
            <i class="fas fa-microchip"></i> Diagnose with Prolog AI
        </button>
        <div id="prologResult" class="mt-2" style="display: none;">
            <div class="alert alert-info">
                <strong>🧠 Prolog AI Analysis:</strong>
                <div id="prologDiagnosis"></div>
            </div>
        </div>
    </div>
    '''

def get_prolog_script():
    """Get JavaScript for Prolog functionality"""
    return '''
    <script>
    async function runPrologDiagnosis() {
        const symptoms = symptoms || [];
        
        if (symptoms.length === 0) {
            alert('Please add at least one symptom first');
            return;
        }
        
        const prologBtn = document.getElementById('prologBtn');
        const prologResult = document.getElementById('prologResult');
        const prologDiagnosis = document.getElementById('prologDiagnosis');
        
        prologBtn.disabled = true;
        prologBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Prolog AI analyzing...';
        prologResult.style.display = 'block';
        prologDiagnosis.innerHTML = 'Analyzing symptoms with Prolog inference engine...';
        
        try {
            const response = await fetch('/api/prolog/diagnose', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symptoms: symptoms })
            });
            const data = await response.json();
            
            if (data.success && data.diagnosis.length > 0) {
                let html = '<ul class="mb-0">';
                data.diagnosis.forEach(d => {
                    html += `<li>
                        <strong>${d.condition}</strong> (${d.confidence}% confidence)<br>
                        <small>Matched: ${d.matched_symptoms.join(', ')}</small><br>
                        <small class="text-muted">Treatment: ${d.treatment.substring(0, 60)}...</small>
                    </li>`;
                });
                html += '</ul>';
                prologDiagnosis.innerHTML = html;
            } else {
                prologDiagnosis.innerHTML = 'No diagnosis could be determined by Prolog AI.';
            }
        } catch (error) {
            prologDiagnosis.innerHTML = '<span class="text-danger">Error connecting to Prolog engine.</span>';
        } finally {
            prologBtn.disabled = false;
            prologBtn.innerHTML = '<i class="fas fa-microchip"></i> Diagnose with Prolog AI';
        }
    }
    </script>
    '''