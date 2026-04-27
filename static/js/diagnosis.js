// Diagnosis specific JavaScript
class DiagnosisApp {
    constructor() {
        this.symptoms = [];
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadSymptoms();
    }
    
    bindEvents() {
        $('#symptomInput').on('keypress', (e) => {
            if (e.key === 'Enter') this.addSymptom();
        });
    }
    
    addSymptom() {
        const symptom = $('#symptomInput').val().trim().toLowerCase();
        if (symptom && !this.symptoms.includes(symptom)) {
            this.symptoms.push(symptom);
            this.updateSymptomsList();
            $('#symptomInput').val('');
        }
    }
    
    removeSymptom(index) {
        this.symptoms.splice(index, 1);
        this.updateSymptomsList();
    }
    
    updateSymptomsList() {
        const container = $('#symptomsList');
        if (this.symptoms.length === 0) {
            container.html('<p class="text-muted">No symptoms added</p>');
            return;
        }
        
        let html = '';
        this.symptoms.forEach((s, i) => {
            html += `<span class="symptom-tag">${s} <i class="fas fa-times" onclick="diagnosisApp.removeSymptom(${i})"></i></span>`;
        });
        container.html(html);
    }
    
    async getDiagnosis() {
        if (this.symptoms.length === 0) {
            alert('Please add at least one symptom');
            return;
        }
        
        $('#resultsContainer').html('<div class="text-center py-5"><div class="spinner-border text-primary"></div><p>Analyzing symptoms...</p></div>');
        
        try {
            const response = await fetch('/api/diagnose', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    symptoms: this.symptoms,
                    age: $('#age').val(),
                    duration: $('#duration').val()
                })
            });
            const data = await response.json();
            this.displayResults(data);
        } catch (error) {
            $('#resultsContainer').html('<div class="alert alert-danger">Error connecting to server</div>');
        }
    }
    
    displayResults(data) {
        let html = '';
        
        if (data.emergency_warning) {
            html += '<div class="emergency result-item"><strong>⚠️ EMERGENCY WARNING</strong><br>Please seek immediate medical attention!</div>';
        }
        
        html += `<div class="result-item"><strong>Patient Summary:</strong><br>Age: ${data.patient_info.age} | Duration: ${data.patient_info.duration} | Symptoms: ${data.patient_info.symptom_count}</div>`;
        
        if (data.diagnosis && data.diagnosis.length > 0) {
            data.diagnosis.forEach(d => {
                html += `<div class="result-item">
                            <strong>${d.condition}</strong> (${d.confidence}% match)<br>
                            <small>Matched: ${d.matched_symptoms.join(', ')} (${d.match_count}/${d.total_symptoms})</small><br>
                            <strong>Treatment:</strong> ${d.treatment}<br>
                            ${d.see_doctor ? '<span class="text-warning">⚠️ Consider consulting a doctor</span>' : ''}
                        </div>`;
            });
        } else {
            html += '<div class="result-item">No specific conditions matched. Monitor symptoms and consult a doctor if needed.</div>';
        }
        
        html += `<div class="result-item">
                    <strong>💡 General Advice</strong><br>
                    • ${data.advice.rest}<br>
                    • ${data.advice.hydration}<br>
                    • ${data.advice.monitor}<br>
                    • ${data.advice.when_to_see_doctor}
                </div>`;
        
        $('#resultsContainer').html(html);
    }
    
    clearAll() {
        this.symptoms = [];
        this.updateSymptomsList();
        $('#age').val('');
        $('#duration').val('');
        $('#resultsContainer').html('<p class="text-center text-muted py-5">Add symptoms and click "Get Diagnosis" to see results</p>');
    }
    
    async loadSymptoms() {
        try {
            const response = await fetch('/api/symptoms');
            const data = await response.json();
            const datalist = $('#symptomList');
            data.symptoms.forEach(symptom => {
                datalist.append(`<option value="${symptom}">`);
            });
        } catch (error) {
            console.error('Error loading symptoms:', error);
        }
    }
}

const diagnosisApp = new DiagnosisApp();