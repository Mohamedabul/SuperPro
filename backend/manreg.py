import pandas as pd
import requests

API_BASE = "https://api.sambanova.ai/v1"
MODEL_405B = "Meta-Llama-3.3-70B-Instruct"
API_KEY = "540f8914-997e-46c6-829a-ff76f5d4d265"

def extract_column_names1(llm_response):
    try:
        location_col = llm_response.split('location_column:')[1].split(',')[0].strip()
        regional_col = llm_response.split('regional_column:')[1].strip()
        return location_col, regional_col
    except (IndexError, AttributeError):
        print("Error: Failed to extract column names from LLM response.")
        return None, None

def analyze_columns_with_llm1(df):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    sample_data = df.head(5).to_string()
    columns_list = ", ".join(df.columns.tolist())
    prompt = f"""Given these column names: {columns_list}
    And sample data:
    {sample_data}
    Which column contains business location (country) information and which column contains regional information?
    Return only the exact column names in this format: 'location_column: <name>, regional_column: <name>'"""
    
    payload = {
        "messages": [
            {"role": "system", "content": "You are an expert in data validation for region and location mismatches."},
            {"role": "user", "content": prompt}
        ],
        "model": MODEL_405B,
        "max_tokens": 4000,
        "temperature": 0.1,
        "top_p": 0.1
    }
    
    try:
        response = requests.post(f"{API_BASE}/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except (requests.exceptions.RequestException, KeyError) as e:
        return f"Error analyzing columns: {str(e)}"

def mismatched_index(df, regional_column):
    
    if regional_column is None or regional_column not in df.columns:
        return None
    
    
    valid_regions = {'APAC', 'EMEA', 'EMEA/APAC', 'APAC/EMEA', 'AMERICAS','GLOBAL'}
    
    
    invalid_mask = ~df[regional_column].str.upper().isin(valid_regions)
    
    
    if invalid_mask.any():
        return list(df[invalid_mask].index)
    
    return None

def main():
    file_path = input("Enter the file path (CSV or Excel): ").strip()
    if file_path:
        file_extension = file_path.split('.')[-1]
        try:
            if file_extension == 'csv':
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            llm_result = analyze_columns_with_llm1(df)
            location_column, regional_column = extract_column_names1(llm_result)
            
            invalid_indices = mismatched_index(df, regional_column)
            if invalid_indices:
                print("\nRows with invalid region values found at indices:")
                print(invalid_indices)
            else:
                print("\nNo invalid regions found.")
                
        except Exception as e:
            print(f"Error: {str(e)}")
    else:
        print("No file provided. Exiting.")

if __name__ == "__main__":
    main()