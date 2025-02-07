import streamlit as st
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
    You are given a dataset with two columns, one is business location aand the other is regional.
    Your task is to identify ALL mismatches based on these **strict rules**:

    ### **Matching Rules:**
    1. If business location is `'Worldwide'` or `'WORLDWIDE'` or contains multiple regions, then regional **must** be `'Global'`
    2. If business location contains **only APAC countries**, then regional **must** be `'APAC'`
    3. If business location contains **only EMEA countries**, then regional **must** be `'EMEA'`
    4. If business location contains **both APAC and EMEA countries**, then regional **must** be `'APAC/EMEA'`
    5. Handle multiple locations separated by commas, semicolons, or other delimiters
    6. Check for spelling variations and common typos in region names
    7. If location is worldwide, regional should be global

    Analyze the data and provide:
    1. A table of Row indexes where the mismatched location/regional has occured, no need of the actual values of location and regional, or any other thing in the table

    **Only display the tables, no additional text.**
    """

    if 'Locations' not in df.columns or 'Regional' not in df.columns:
        st.error("Required columns 'Locations' and 'Regional' not found in the dataset")
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
        st.error(f"API Request Error: {str(e)}")
        return None
    except KeyError as e:
        st.error(f"API Response Format Error: {str(e)}")
        return None


def main():
    st.title("Region-Location Mismatch Checker")
    st.write("Upload a CSV or Excel file containing 'Locations' and 'Regional' columns.")

    uploaded_file = st.file_uploader("Upload your data file", type=["csv", "xlsx", "xls"])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            else:
                df = pd.read_excel(uploaded_file)

            def highlight_mismatches(row):
                styles = [''] * len(row)
                if pd.isna(row['Locations']) or pd.isna(row['Regional']):
                    return ['background-color: yellow'] * len(row)
               
                location = str(row['Locations']).upper()
                regional = str(row['Regional']).upper()
               
                if 'WORLDWIDE' in location and regional != 'GLOBAL':
                    return ['background-color: red'] * len(row)
                elif any(region in location for region in ['APAC', 'EMEA']) and regional not in ['APAC', 'EMEA', 'APAC/EMEA']:
                    return ['background-color: red'] * len(row)
               
                return styles

            st.write("### Full Dataset with Highlighted Mismatches")
            styled_df = df.style.apply(highlight_mismatches, axis=1)
            st.dataframe(styled_df)

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                styled_df.to_excel(writer, index=False)
           
            st.download_button(
                label="Download Full Dataset with Mismatch Status",
                data=buffer.getvalue(),
                file_name="mismatch_analysis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            mismatches = check_region_location_mismatch(df)

            if mismatches:
                st.write("### Detailed Mismatch Analysis")
                st.markdown(mismatches, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error processing file: {str(e)}")


if __name__ == "__main__":
    main()