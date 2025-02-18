import pandas as pd
import requests

API_BASE = "https://api.sambanova.ai/v1"
MODEL_405B = "Meta-Llama-3.3-70B-Instruct"
API_KEY = "540f8914-997e-46c6-829a-ff76f5d4d265"

def extract_column_names(llm_response):
    try:
        location_col = llm_response.split('location_column:')[1].split(',')[0].strip()
        regional_col = llm_response.split('regional_column:')[1].strip()
        print(location_col, regional_col)
        return location_col, regional_col
    except (IndexError, AttributeError):
        print("Failed to extract column names from LLM response")
        return None, None
   
def analyze_columns_with_llm(df):
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

def check_location_mismatch(df, location_column, regional_column):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
    You are an expert in data validation for business location. You are given a dataset with two columns, one is business location and the other is regional. You have to check whether all the locatins given in the location column are name of countries or Worldwide, no regions like APAC, EMEA , etc should be present in the location column.

    Your task is to identify ALL mismatches based on these **strict rules**:

    ### **Matching Rules:**
    1. Location column should have only country names or Worldwide else it should be highlighted.

    **Analyze in depth, and you have to find the maximum number of mismatches.**

    Analyze this data:
    {df[[location_column]].to_string()}

    Output Format:
    Location : [Index of all the rows that do have regions like EMEA/APAC in the location column instead of country name or worldwide]
    **Only display the tables, no additional text.**
    """

    df[location_column] = df[location_column].str.strip()
    df[regional_column] = df[regional_column].str.strip()

    payload = {
        "messages": [
            {"role": "system", "content": "You are an expert in data validation for business location and it's region mismatches."},
            {"role": "user", "content": f"{prompt}"}
        ],
        "model": MODEL_405B,
        "max_tokens": 4000,
        "temperature": 0.1,
        "top_p": 0.1,
        "presence_penalty": 0.1,
        "frequency_penalty": 0.1
    }

    try:
        response = requests.post(f"{API_BASE}/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except (requests.exceptions.RequestException, KeyError) as e:
        return None

def main():
    uploaded_file = input("Enter the file path (CSV or Excel): ").strip()

    if uploaded_file:
        file_extension = uploaded_file.split('.')[-1]

        try:
            if file_extension == 'csv':
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            llm_result = analyze_columns_with_llm(df)
            location_column, regional_column = extract_column_names(llm_result)
            mismatches = check_location_mismatch(df, location_column, regional_column)

            if mismatches:
                print(mismatches)
            else:
                print("\nNo mismatches found.")

        except Exception as e:
            print(f"Error: {str(e)}")
    else:
        print("No file provided. Exiting.")

if __name__ == "__main__":
    main()
 