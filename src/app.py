from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
from datetime import datetime
from src.analysis import QuantAnalyzer

app = Flask(__name__, template_folder='../templates')
app.config['UPLOAD_FOLDER'] = 'data'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure data directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

analyzer = QuantAnalyzer()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload CSV file endpoint"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Only CSV files are allowed'}), 400
    
    try:
        # Save the file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'current_data.csv')
        file.save(filepath)
        
        # Load the data
        analyzer.load_data(filepath)
        
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'rows': len(analyzer.df),
            'date_range': {
                'start': analyzer.df['Date'].min().strftime('%Y-%m-%d'),
                'end': analyzer.df['Date'].max().strftime('%Y-%m-%d')
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/best-day-of-week', methods=['POST'])
def best_day_of_week():
    """Calculate best day of week for a given period"""
    try:
        data = request.json
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if not analyzer.df is not None and len(analyzer.df) > 0:
            return jsonify({'error': 'Please upload data first'}), 400
        
        result = analyzer.best_day_of_week(start_date, end_date)
        
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/load-default', methods=['POST'])
def load_default():
    """Load default SPX500 data"""
    try:
        default_file = 'spx500.csv'
        if os.path.exists(default_file):
            analyzer.load_data(default_file)
            return jsonify({
                'success': True,
                'message': 'Default SPX500 data loaded',
                'rows': len(analyzer.df),
                'date_range': {
                    'start': analyzer.df['Date'].min().strftime('%Y-%m-%d'),
                    'end': analyzer.df['Date'].max().strftime('%Y-%m-%d')
                }
            })
        else:
            return jsonify({'error': 'Default data file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
