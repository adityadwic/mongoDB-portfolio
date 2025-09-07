"""
MongoDB QA Interactive Dashboard
Author: QA Engineer
Description: Create interactive web dashboard for test results
"""

import json
import os
from datetime import datetime
from flask import Flask, render_template_string, jsonify
import threading
import webbrowser
import time


class TestDashboard:
    def __init__(self, reports_dir="reports", port=5000):
        self.reports_dir = reports_dir
        self.port = port
        self.app = Flask(__name__)
        self.setup_routes()

    def load_latest_results(self):
        """Load the latest test results"""
        results = {}

        try:
            # Load summary
            summary_files = [
                f for f in os.listdir(self.reports_dir) if f.startswith("test_summary_")
            ]
            if summary_files:
                latest_summary = sorted(summary_files)[-1]
                with open(os.path.join(self.reports_dir, latest_summary), "r") as f:
                    results["summary"] = json.load(f)

            # Load performance results
            perf_files = [
                f
                for f in os.listdir(self.reports_dir)
                if f.startswith("performance_report_")
            ]
            if perf_files:
                latest_perf = sorted(perf_files)[-1]
                with open(os.path.join(self.reports_dir, latest_perf), "r") as f:
                    results["performance"] = json.load(f)

            # Load security results
            security_files = [
                f
                for f in os.listdir(self.reports_dir)
                if f.startswith("security_report_")
            ]
            if security_files:
                latest_security = sorted(security_files)[-1]
                with open(os.path.join(self.reports_dir, latest_security), "r") as f:
                    results["security"] = json.load(f)

            # Load validation results
            validation_files = [
                f
                for f in os.listdir(self.reports_dir)
                if f.startswith("validation_report_")
            ]
            if validation_files:
                latest_validation = sorted(validation_files)[-1]
                with open(os.path.join(self.reports_dir, latest_validation), "r") as f:
                    results["validation"] = json.load(f)

        except Exception as e:
            print(f"Error loading results: {e}")

        return results

    def setup_routes(self):
        """Setup Flask routes"""

        @self.app.route("/")
        def dashboard():
            return render_template_string(DASHBOARD_HTML)

        @self.app.route("/api/data")
        def get_data():
            return jsonify(self.load_latest_results())

    def run(self, open_browser=True):
        """Run the dashboard server"""
        if open_browser:

            def open_browser_delayed():
                time.sleep(1)
                webbrowser.open(f"http://localhost:{self.port}")

            threading.Thread(target=open_browser_delayed).start()

        print("🚀 Starting MongoDB QA Dashboard...")
        print(f"📊 Dashboard available at: http://localhost:{self.port}")
        print("Press Ctrl+C to stop the server")

        self.app.run(debug=False, port=self.port, host="0.0.0.0")


# HTML Template for Dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MongoDB QA Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; }
        .navbar { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem 0; }
        .navbar h1 { text-align: center; font-size: 2rem; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .card { background: white; border-radius: 10px; padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .card h3 { color: #333; margin-bottom: 1rem; font-size: 1.1rem; }
        .metric { text-align: center; }
        .metric .value { font-size: 2.5rem; font-weight: bold; margin: 0.5rem 0; }
        .metric .label { color: #666; font-size: 0.9rem; }
        .status.pass { color: #28a745; }
        .status.fail { color: #dc3545; }
        .charts { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 2rem; margin-bottom: 2rem; }
        .chart-container { background: white; border-radius: 10px; padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .test-results { background: white; border-radius: 10px; padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .test-item { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; border-bottom: 1px solid #eee; }
        .test-item:last-child { border-bottom: none; }
        .loading { text-align: center; padding: 3rem; color: #666; }
        .refresh-btn { background: #007bff; color: white; border: none; padding: 0.5rem 1rem; border-radius: 5px; cursor: pointer; margin-bottom: 1rem; }
        .refresh-btn:hover { background: #0056b3; }
        .timestamp { text-align: center; color: #666; margin-bottom: 1rem; }
    </style>
</head>
<body>
    <div class="navbar">
        <h1>🗄️ MongoDB QA Dashboard</h1>
    </div>
    
    <div class="container">
        <div class="timestamp" id="timestamp"></div>
        <button class="refresh-btn" onclick="loadData()">🔄 Refresh Data</button>
        
        <div id="loading" class="loading">
            <h3>Loading dashboard data...</h3>
        </div>
        
        <div id="dashboard" style="display: none;">
            <div class="cards">
                <div class="card">
                    <div class="metric">
                        <div class="value status" id="overallStatus">-</div>
                        <div class="label">Overall Status</div>
                    </div>
                </div>
                <div class="card">
                    <div class="metric">
                        <div class="value" id="totalSuites">0</div>
                        <div class="label">Total Test Suites</div>
                    </div>
                </div>
                <div class="card">
                    <div class="metric">
                        <div class="value status pass" id="passedSuites">0</div>
                        <div class="label">Passed Suites</div>
                    </div>
                </div>
                <div class="card">
                    <div class="metric">
                        <div class="value status fail" id="failedSuites">0</div>
                        <div class="label">Failed Suites</div>
                    </div>
                </div>
            </div>
            
            <div class="charts">
                <div class="chart-container">
                    <h3>Test Suite Results</h3>
                    <canvas id="suiteChart"></canvas>
                </div>
                <div class="chart-container">
                    <h3>Performance Metrics</h3>
                    <canvas id="performanceChart"></canvas>
                </div>
            </div>
            
            <div class="test-results">
                <h3>Latest Test Results</h3>
                <div id="testResults"></div>
            </div>
        </div>
    </div>

    <script>
        let suiteChart, performanceChart;
        
        function loadData() {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('dashboard').style.display = 'none';
            
            fetch('/api/data')
                .then(response => response.json())
                .then(data => {
                    updateDashboard(data);
                })
                .catch(error => {
                    console.error('Error loading data:', error);
                    document.getElementById('loading').innerHTML = '<h3>Error loading data</h3>';
                });
        }
        
        function updateDashboard(data) {
            document.getElementById('timestamp').innerText = 'Last Updated: ' + new Date().toLocaleString();
            
            // Update summary cards
            const summary = data.summary?.test_execution_summary || {};
            document.getElementById('overallStatus').innerText = summary.overall_status || 'N/A';
            document.getElementById('overallStatus').className = 'value status ' + (summary.overall_status === 'PASS' ? 'pass' : 'fail');
            document.getElementById('totalSuites').innerText = summary.total_suites || 0;
            document.getElementById('passedSuites').innerText = summary.passed_suites || 0;
            document.getElementById('failedSuites').innerText = summary.failed_suites || 0;
            
            // Update charts
            updateCharts(data);
            
            // Update test results
            updateTestResults(data);
            
            document.getElementById('loading').style.display = 'none';
            document.getElementById('dashboard').style.display = 'block';
        }
        
        function updateCharts(data) {
            const summary = data.summary || {};
            const suiteResults = summary.suite_results || {};
            
            // Suite Results Chart
            const ctx1 = document.getElementById('suiteChart').getContext('2d');
            if (suiteChart) suiteChart.destroy();
            
            const suiteLabels = Object.keys(suiteResults).map(key => key.replace('_', ' ').replace(/\\b\\w/g, l => l.toUpperCase()));
            const suiteData = Object.values(suiteResults).map(status => status === 'PASS' ? 1 : 0);
            
            suiteChart = new Chart(ctx1, {
                type: 'doughnut',
                data: {
                    labels: suiteLabels,
                    datasets: [{
                        data: suiteData,
                        backgroundColor: ['#28a745', '#dc3545', '#ffc107', '#17a2b8'],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom' }
                    }
                }
            });
            
            // Performance Chart
            const ctx2 = document.getElementById('performanceChart').getContext('2d');
            if (performanceChart) performanceChart.destroy();
            
            const performanceData = data.performance?.performance_results || [];
            const insertPerf = performanceData.find(r => r.test_type === 'insert_performance');
            
            if (insertPerf) {
                performanceChart = new Chart(ctx2, {
                    type: 'bar',
                    data: {
                        labels: ['Single Insert', 'Bulk Insert'],
                        datasets: [{
                            label: 'Documents/Second',
                            data: [insertPerf.single_insert_rate || 0, insertPerf.bulk_insert_rate || 0],
                            backgroundColor: ['#FF6B6B', '#4ECDC4'],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: { beginAtZero: true }
                        }
                    }
                });
            }
        }
        
        function updateTestResults(data) {
            const resultsContainer = document.getElementById('testResults');
            let html = '';
            
            // Security results
            if (data.security?.security_results) {
                html += '<h4>Security Tests</h4>';
                data.security.security_results.forEach(test => {
                    html += `<div class="test-item">
                        <span>${test.test_type.replace('_', ' ')}</span>
                        <span class="status ${test.status.toLowerCase()}">${test.status}</span>
                    </div>`;
                });
            }
            
            // Validation results
            if (data.validation?.validation_results) {
                html += '<h4>Data Validation Tests</h4>';
                data.validation.validation_results.forEach(test => {
                    html += `<div class="test-item">
                        <span>${test.test_type.replace('_', ' ')}</span>
                        <span class="status ${test.status.toLowerCase()}">${test.status}</span>
                    </div>`;
                });
            }
            
            resultsContainer.innerHTML = html || '<p>No detailed test results available</p>';
        }
        
        // Load data on page load
        loadData();
        
        // Auto-refresh every 30 seconds
        setInterval(loadData, 30000);
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    dashboard = TestDashboard()
    dashboard.run()
