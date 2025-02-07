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
        Returns a dictionary with defect information for each column.
        """
        # Read the file based on extension
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext == '.csv':
            df = pd.read_csv(file_path, dtype=str)
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path, dtype=str)
        else:
            raise ValueError("Unsupported file format. Please use CSV or Excel files.")

        results = {}
        
        # Analyze each column
        for column in df.columns:
            column_defects = self._analyze_column(df[column])
            if column_defects:
                results[column] = column_defects
                
        return results

    def _analyze_value_delimiters(self, value: str) -> Dict:
        """
        Analyze delimiters in a single value.
        Returns detailed analysis of delimiter usage.
        """
        # Count occurrences of each delimiter
        delimiter_counts = {d: value.count(d) for d in self.common_delimiters if d in value}
        
        if not delimiter_counts:
            return None
            
        # Find the most common delimiter
        max_delimiter = max(delimiter_counts.items(), key=lambda x: x[1])
        
        # Identify defect delimiters (any delimiter that's not the most common one)
        defects = {
            delim: {
                'count': count,
                'reasoning': f"Less frequent than primary delimiter '{max_delimiter[0]}' ({count} vs {max_delimiter[1]} occurrences)"
            }
            for delim, count in delimiter_counts.items()
            if delim != max_delimiter[0]
        }
        
        return {
            'value': value,
            'non_defect_delimiter': max_delimiter[0],
            'non_defect_count': max_delimiter[1],
            'defects': defects
        }

    def _analyze_column(self, series: pd.Series) -> Dict:
        """
        Analyze delimiters in a single column.
        Returns defect information if found, marking all non-primary delimiters as defects.
        """
        all_delimiter_counts = Counter()
        defect_rows = {}
        row_details = {}

        # First pass: count all delimiters in the column
        for idx, value in series.items():
            if pd.isna(value):
                continue
                
            value_str = str(value)
            # Count all delimiters in this value
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

        # Determine the primary (most used) delimiter
        primary_delimiter, primary_count = all_delimiter_counts.most_common(1)[0]

        # Second pass: mark all non-primary delimiters as defects
        for idx, row_info in row_details.items():
            row_defects = {}
            
            for delim, count in row_info['delimiters'].items():
                if delim != primary_delimiter:  # Any delimiter that's not the primary one is a defect
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
        
        print("\nDelimiter Analysis Results:")
        for column, analysis in results.items():
            print(f"\n{'='*50}")
            print(f"Column: {column}")
            print(f"Primary delimiter: '{analysis['primary_delimiter']['character']}' "
                  f"(found {analysis['primary_delimiter']['total_occurrences']} times)")
            
            print("\nAll delimiter usage:")
            for delim, count in analysis['all_delimiters'].items():
                if delim == analysis['primary_delimiter']['character']:
                    print(f"  '{delim}': {count} occurrences (PRIMARY)")
                else:
                    print(f"  '{delim}': {count} occurrences (DEFECT)")
            
            if analysis['defect_rows']:
                print(f"\nFound {analysis['total_rows_with_defects']} rows with secondary delimiters:")
                for row_idx, defect_info in analysis['defect_rows'].items():
                    print(f"\nRow {row_idx}:")
                    print(f"Value: {defect_info['value']}")
                    print("Secondary delimiters found:")
                    for delim, details in defect_info['defects'].items():
                        print(f"  - '{delim}': {details['count']} occurrences in this row")
                        print(f"    {details['reasoning']}")
            else:
                print("\nNo secondary delimiters found in this column.")
                
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
