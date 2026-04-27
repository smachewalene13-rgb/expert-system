// static/js/charts.js
function createSymptomChart(symptoms, matches) {
    const ctx = document.getElementById('symptomChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: symptoms,
            datasets: [{
                label: 'Match Score',
                data: matches,
                backgroundColor: '#667eea'
            }]
        }
    });
}