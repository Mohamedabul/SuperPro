from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
from werkzeug.utils import secure_filename
from delimiter import DelimiterAnalyzer
from Regional import check_region_location_mismatch,extract_column_names1,analyze_columns_with_llm1
from loc import check_location_mismatch,extract_column_names,analyze_columns_with_llm
from manloc import mismatch_data

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
        delimiter_analyzer = DelimiterAnalyzer()
        delimiter_results = delimiter_analyzer.analyze_file(file_path)

        # Add location mismatch analysis
        
        llm_result1 = analyze_columns_with_llm1(df)
        location_column1, regional_column1 = extract_column_names1(llm_result1)

        region_mismatches = check_region_location_mismatch(df, location_column1, regional_column1)




        llm_result = analyze_columns_with_llm(df)
        location_column, regional_column = extract_column_names(llm_result)
        location_mismatchs = check_location_mismatch(df, location_column, regional_column)
       
        # Get missing value positions and TBD positions
        missing_positions = {}
        tbd_positions = {}
        duplicate_info = {}
       
        for column in df.columns:
            # Find missing values (NaN)
            missing_positions[column] = df[df[column].isna()].index.tolist()
           
            # Find TBD values (case insensitive)
            tbd_mask = df[column].astype(str).str.upper().isin(['TBD', 'TO BE DETERMINED','-','', "None","Null"])
            tbd_positions[column] = df[tbd_mask].index.tolist()
           
            # Find duplicates in each column
            value_counts = df[column].value_counts()
            duplicates = value_counts[value_counts > 1]
            if not duplicates.empty:
                duplicate_info[column] = {
                    'count': len(duplicates),  
                    'total_occurrences': int(duplicates.sum()),  
                    'values': {
                        str(value): int(count)  
                        for value, count in duplicates.items()
                        if pd.notna(value)  
                    }
                }
            else:
                duplicate_info[column] = {
                    'count': 0,
                    'total_occurrences': 0,
                    'values': {}
                }

        # Find duplicate rows
        duplicate_rows = df.duplicated(keep=False)
        duplicate_row_indices = df[duplicate_rows].index.tolist()
        total_duplicate_rows = len(duplicate_row_indices)
       
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
            'duplicate_info': duplicate_info,
            'duplicate_rows': {
                'total': total_duplicate_rows,
                'percentage': float(total_duplicate_rows / len(df) * 100),
                'indices': duplicate_row_indices
            },
            'data': df.fillna('').to_dict('records'),
            'delimiter_analysis': delimiter_results,
            'region_mismatches': region_mismatches,
            'location_mismatch': location_mismatchs,
            'location_column': location_column,
            'regional_column': regional_column
        }
        # print(analysis)
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
 