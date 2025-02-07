import pandas as pd
from collections import Counter
import json
from typing import Dict, List, Tuple
import os

class DelimiterAnalyzer:
    def __init__(self):
        self.common_delimiters = [',', '-', '/', '|', ';', ':', '\\']

    def analyze_file(self, file_path: str) -> Dict:
        """
        Analyze delimiters in a CSV or Excel file.
        Returns a dictionary with column names as keys and lists of defect row indices as values.
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext == '.csv':
            df = pd.read_csv(file_path, dtype=str)
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path, dtype=str)
        else:
            raise ValueError("Unsupported file format. Please use CSV or Excel files.")

        results = {}
        
        for column in df.columns:
            column_defects = self._analyze_column(df[column])
            if column_defects and column_defects['defect_rows']:
                results[column] = sorted(map(int, column_defects['defect_rows'].keys()))
                
        return results

    def _analyze_column(self, series: pd.Series) -> Dict:
        """
        Analyze delimiters in a single column.
        Returns defect information if found, marking all non-primary delimiters as defects.
        """
        all_delimiter_counts = Counter()
        defect_rows = {}
        row_details = {}

        for idx, value in series.items():
            if pd.isna(value):
                continue
                
            value_str = str(value)
            delims_in_value = {d: value_str.count(d) for d in self.common_delimiters if d in value_str}
            
            if delims_in_value:
                for delim, count in delims_in_value.items():
                    all_delimiter_counts[delim] += count
                row_details[idx] = {
                    'value': value_str,
                    'delimiters': delims_in_value
                }

        if not all_delimiter_counts:
            return None

        primary_delimiter, primary_count = all_delimiter_counts.most_common(1)[0]
        for idx, row_info in row_details.items():
            row_defects = {}
            
            for delim, count in row_info['delimiters'].items():
                if delim != primary_delimiter:  
                    row_defects[delim] = {
                        'count': count,
                        'total_in_column': all_delimiter_counts[delim],
                        'reasoning': (f"Secondary delimiter (used {all_delimiter_counts[delim]} times in column) "
                                    f"vs primary delimiter '{primary_delimiter}' (used {primary_count} times)")
                    }
            
            if row_defects:
                defect_rows[idx] = {
                    'value': row_info['value'],
                    'defects': row_defects
                }

        return {
            'primary_delimiter': {
                'character': primary_delimiter,
                'total_occurrences': primary_count
            },
            'all_delimiters': dict(all_delimiter_counts),
            'defect_rows': defect_rows,
            'total_rows_with_defects': len(defect_rows),
            'total_rows_analyzed': len(row_details)
        }

def main():
    analyzer = DelimiterAnalyzer()
    file_path = input("Enter the path to your CSV or Excel file: ")
    try:
        results = analyzer.analyze_file(file_path)
        print(results)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
