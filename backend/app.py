from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_file(file_path):
    try:
        # Read the file
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        # Get missing value positions and TBD positions
        missing_positions = {}
        tbd_positions = {}
        
        for column in df.columns:
            # Find missing values (NaN)
            missing_positions[column] = df[df[column].isna()].index.tolist()
            
            # Find TBD values (case insensitive)
            tbd_mask = df[column].astype(str).str.upper().isin(['TBD', 'TO BE DETERMINED'])
            tbd_positions[column] = df[tbd_mask].index.tolist()
        
        # Basic analysis
        analysis = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'columns': list(df.columns),
            'missing_values': {
                col: int(df[col].isna().sum()) 
                for col in df.columns
            },
            'tbd_values': {
                col: len(tbd_positions[col])
                for col in df.columns
            },
            'missing_percentage': {
                col: float(df[col].isna().sum() / len(df) * 100) 
                for col in df.columns
            },
            'tbd_percentage': {
                col: float(len(tbd_positions[col]) / len(df) * 100)
                for col in df.columns
            },
            'data_types': {
                col: str(df[col].dtype) 
                for col in df.columns
            },
            'missing_positions': missing_positions,
            'tbd_positions': tbd_positions,
            'data': df.fillna('').to_dict('records')
        }
        return analysis, None
    except Exception as e:
        return None, str(e)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        analysis, error = analyze_file(filepath)
        if error:
            return jsonify({'error': error}), 500
            
        return jsonify({
            'message': 'File uploaded successfully',
            'analysis': analysis
        })
    
    return jsonify({'error': 'File type not allowed'}), 400

if __name__ == '__main__':
    app.run(debug=True)
