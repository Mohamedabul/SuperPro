import pandas as pd
import requests
import os
import io


API_BASE = "https://api.sambanova.ai/v1"
MODEL_405B = "Meta-Llama-3.3-70B-Instruct"
API_KEY = "f2321685-3794-4924-91dd-a0d9ee7c365b"

def check_region_location_mismatch(df):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
    You are an expert in data validation for region and location mismatches. You are given a dataset with two columns, one is business location aand the other is regional. You have to compare the location and regional columns and identify whether the regional column is correct with respect to the location column.
    Your task is to identify ALL mismatches based on these **strict rules**:
 
    ### **Matching Rules:**
    1. If business location column contains **only EMEA countries**, then regional must only be 'EMEA'.
    2. If business location column contains **only APAC countries**, then regional must only be 'APAC'.
    3. If business location column contains **both APAC and EMEA countries**, then regional must be 'APAC/EMEA'.
    4. If business location is 'Worldwide' or 'WORLDWIDE' or contains multiple regions, then regional **must** be 'Global'.
    5. If regional contains 'APAC/EMEA' but the location is only APAC or EMEA, then it is a mismatch.
    6. If location contains both countries of "APAC and EMEA" but the location is only 'APAC' or 'EMEA', then it is a mismatch.
    7. Check for spelling variations and common typos in region names
    8. If location is worldwide, regional must be global
    9. You **must not** consider blanks in regional as a mismatch, only if location and regional is filled then take it for the comparision, if regional is empty then skip the comparision.
 
    Analyze the data and provide:
    1. A table of Row indexes of regional column where the mismatched location/regional has occured, no need of the actual values of location and regional, or any other thing in the table

    Output Format :

    Regional : [Row Index]
    **Only display the tables, no additional text.**
    """

    if 'Locations' not in df.columns or 'Regional' not in df.columns:
        return None

    df['Locations'] = df['Locations'].str.strip().str.upper()
    df['Regional'] = df['Regional'].str.strip().str.upper()

    payload = {
        "messages": [
            {"role": "system", "content": "You are an expert in data validation for region and location mismatches."},
            {"role": "user", "content": f"{prompt}\n\nData:\n{df[['Locations', 'Regional']].to_string()}"}
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
    except requests.exceptions.RequestException as e:
        return None
    except KeyError as e:
        return None
    
def main():
    file_path = input("Enter the path to your CSV or Excel file: ")

    if os.path.exists(file_path):
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8')
            else:
                df = pd.read_excel(file_path)

            # Rest of your analysis code
            mismatches = check_region_location_mismatch(df)
            if mismatches:
                print(mismatches)
            else:
                print("No mismatches found in the data.")

        except Exception as e:
            print(f"Error processing file: {str(e)}")
    else:
        print(f"File not found: {file_path}")



if __name__ == "__main__":
    main()