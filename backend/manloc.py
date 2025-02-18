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

# def mismatch_data(df, location_column, regional_column):
#     """
#     Identifies mismatches between location and regional columns in the dataframe.
    
#     Args:
#         df (pandas.DataFrame): Input dataframe containing location and regional data
#         location_column (str): Name of the column containing country information
#         regional_column (str): Name of the column containing regional information
    
#     Returns:
#         list: Indices of rows where location and region don't match
#     """
#     # Define the regions and their corresponding countries
    # APAC_COUNTRIES = {
    #     'Afghanistan', 'Australia', 'Bangladesh', 'Bhutan', 'Brunei', 'Cambodia', 
    #     'China', 'Fiji', 'India', 'Indonesia', 'Japan', 'Kazakhstan', 'Kiribati',
    #     'Kyrgyzstan', 'Laos', 'Malaysia', 'Maldives', 'Marshall Islands', 
    #     'Micronesia', 'Mongolia', 'Myanmar', 'Nauru', 'Nepal', 'New Zealand',
    #     'North Korea', 'Pakistan', 'Palau', 'Papua New Guinea', 'Philippines',
    #     'Samoa', 'Singapore', 'Solomon Islands', 'South Korea', 'Sri Lanka',
    #     'Taiwan', 'Tajikistan', 'Thailand', 'Timor-Leste', 'Tonga', 'Turkmenistan',
    #     'Tuvalu', 'Uzbekistan', 'Vanuatu', 'Vietnam'
    # }
    
    # EMEA_COUNTRIES = {
    #     'Albania', 'Algeria', 'Andorra', 'Angola', 'Armenia', 'Austria', 
    #     'Azerbaijan', 'Bahrain', 'Belarus', 'Belgium', 'Benin', 
    #     'Bosnia and Herzegovina', 'Botswana', 'Bulgaria', 'Burkina Faso',
    #     'Burundi', 'Cabo Verde', 'Cameroon', 'Central African Republic',
    #     'Chad', 'Comoros', 'Congo', 'Croatia', 'Cyprus', 'Czech Republic',
    #     'Denmark', 'Djibouti', 'Egypt', 'Equatorial Guinea', 'Eritrea',
    #     'Estonia', 'Eswatini', 'Ethiopia', 'Finland', 'France', 'Gabon',
    #     'Gambia', 'Georgia', 'Germany', 'Ghana', 'Greece', 'Guinea',
    #     'Guinea-Bissau', 'Hungary', 'Iceland', 'Iran', 'Iraq', 'Ireland',
    #     'Israel', 'Italy', 'Ivory Coast', 'Jordan', 'Kenya', 'Kuwait',
    #     'Latvia', 'Lebanon', 'Lesotho', 'Liberia', 'Libya', 'Liechtenstein',
    #     'Lithuania', 'Luxembourg', 'Madagascar', 'Malawi', 'Mali', 'Malta',
    #     'Mauritania', 'Mauritius', 'Moldova', 'Monaco', 'Montenegro',
    #     'Morocco', 'Mozambique', 'Namibia', 'Netherlands', 'Niger', 'Nigeria'
    # }
    
#     mismatched_indices = []
    
#     # Iterate through the dataframe
#     for idx, row in df.iterrows():
#         location = str(row[location_column]).strip()
#         region = str(row[regional_column]).strip().upper()
        
#         # Check for mismatches
#         is_mismatch = False
        
#         if region == 'APAC':
#             if location not in APAC_COUNTRIES:
#                 is_mismatch = True
#         elif region == 'EMEA':
#             if location not in EMEA_COUNTRIES:
#                 is_mismatch = True
#         else:
#             # If region is neither APAC nor EMEA, it's a mismatch
#             is_mismatch = True
            
#         if is_mismatch:
#             mismatched_indices.append(idx)
    
#     return mismatched_indices


def mismatch_data(df, location_column, regional_column):
    """
    Validates location and region combinations based on specific business rules.
    
    Args:
        df (pandas.DataFrame): Input dataframe
        location_column (str): Name of the column containing location information
        regional_column (str): Name of the column containing regional information
    
    Returns:
        list: Indices of rows with invalid location-region combinations
    """
    
    APAC_COUNTRIES = {
    'Afghanistan', 'Armenia', 'Australia', 'Azerbaijan', 'Bangladesh', 'Bhutan', 
    'Brunei', 'Cambodia', 'China', 'East Timor', 'Fiji', 'Georgia', 'India', 
    'Indonesia', 'Japan', 'Kazakhstan', 'Kiribati', 'Kyrgyzstan', 'Laos', 
    'Malaysia', 'Maldives', 'Marshall Islands', 'Micronesia', 'Mongolia', 
    'Myanmar', 'Nauru', 'Nepal', 'New Zealand', 'North Korea', 'Pakistan', 
    'Palau', 'Papua New Guinea', 'Philippines', 'Samoa', 'Singapore', 
    'Solomon Islands', 'South Korea', 'Sri Lanka', 'Taiwan', 'Tajikistan', 
    'Thailand', 'Tonga', 'Turkmenistan', 'Tuvalu', 'Uzbekistan', 'Vanuatu', 'Vietnam'
}

    
    EMEA_COUNTRIES = {
    'Albania', 'Andorra', 'Armenia', 'Austria', 'Azerbaijan', 'Bahrain', 'Belarus', 
    'Belgium', 'Benin', 'Bosnia and Herzegovina', 'Botswana', 'Bulgaria', 'Burkina Faso', 
    'Burundi', 'Cameroon', 'Cape Verde', 'Central African Republic', 'Chad', 'Comoros', 
    'Croatia', 'Cyprus', 'Czech Republic', 'Democratic Republic of the Congo', 'Denmark', 
    'Djibouti', 'Egypt', 'Equatorial Guinea', 'Eritrea', 'Estonia', 'Eswatini', 'Ethiopia', 
    'Faroe Islands', 'Finland', 'France', 'Gabon', 'Gambia', 'Georgia', 'Germany', 'Ghana', 
    'Gibraltar', 'Greece', 'Greenland', 'Guinea', 'Guinea-Bissau', 'Hungary', 'Iceland', 
    'Iran', 'Iraq', 'Ireland', 'Israel', 'Italy', 'Ivory Coast', 'Jordan', 'Kazakhstan', 
    'Kenya', 'Kosovo', 'Kuwait', 'Kyrgyzstan', 'Latvia', 'Lebanon', 'Lesotho', 'Liberia', 
    'Libya', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Madagascar', 'Malawi', 'Mali', 
    'Malta', 'Mauritania', 'Moldova', 'Monaco', 'Montenegro', 'Morocco', 'Mozambique', 
    'Namibia', 'Netherlands', 'Niger', 'Nigeria', 'North Macedonia', 'Norway', 'Oman', 
    'Palestine', 'Poland', 'Portugal', 'Qatar', 'Republic of the Congo', 'Romania', 'Russia', 
    'Rwanda', 'San Marino', 'Saudi Arabia', 'Senegal', 'Serbia', 'Seychelles', 'Sierra Leone', 
    'Slovakia', 'Slovenia', 'Somalia', 'South Africa', 'South Sudan', 'Spain', 'Sudan', 
    'Sweden', 'Switzerland', 'Syria', 'Tanzania', 'Togo', 'Tunisia', 'Turkey', 'Turkmenistan', 
    'Uganda', 'Ukraine', 'United Arab Emirates', 'United Kingdom', 'Uzbekistan', 'Vatican City', 
    'Western Sahara', 'Yemen', 'Zambia', 'Zimbabwe'
}

    
    AMERICAS_COUNTRIES = {
    'Antigua and Barbuda', 'Argentina', 'Bahamas', 'Barbados', 'Belize', 'Bolivia', 
    'Brazil', 'Canada', 'Chile', 'Colombia', 'Costa Rica', 'Cuba', 'Dominica', 
    'Dominican Republic', 'Ecuador', 'El Salvador', 'Grenada', 'Guatemala', 'Guyana', 
    'Haiti', 'Honduras', 'Jamaica', 'Mexico', 'Nicaragua', 'Panama', 'Paraguay', 
    'Peru', 'Saint Kitts and Nevis', 'Saint Lucia', 'Saint Vincent and the Grenadines', 
    'Suriname', 'Trinidad and Tobago', 'United States', 'Uruguay', 'Venezuela', 'US'
}


    def normalize_text(text):
        """Normalize text by removing special characters and standardizing format"""
        if not isinstance(text, str):
            return ''
        return text.strip().upper().replace('/', ' ').replace(',', ' ')

    def extract_items(text):
        """Extract individual items from a combined string"""
        return {item.strip() for item in normalize_text(text).split() if item.strip()}

    def get_region_for_country(country):
        """Determine the region for a given country"""
        country = country.upper()
        if country in {c.upper() for c in APAC_COUNTRIES}:
            return 'APAC'
        if country in {c.upper() for c in EMEA_COUNTRIES}:
            return 'EMEA'
        if country in {c.upper() for c in AMERICAS_COUNTRIES}:
            return 'AMERICAS'
        return None

    def is_valid_combination(locations, regions):
        """
        Validate if the location-region combination is valid according to business rules
        """
        locations = extract_items(locations)
        regions = extract_items(regions)
        
        
        if 'WORLDWIDE' in locations:
            return 'GLOBAL' in regions
        if 'AMERICAS' in locations:
            return 'AMERICAS' in regions or 'GLOBAL' in regions
        if 'GLOBAL' in regions:
            return 'WORLDWIDE' in locations
        
        
        if not locations or not regions:
            return False
            
        
        required_regions = set()
        for location in locations:
            region = get_region_for_country(location)
            if region:
                required_regions.add(region)
            elif location in {'NEWYORK', 'NEW YORK', 'NY'}:
                required_regions.add('AMERICAS')
        
        
        if not required_regions:
            return False
            
        
        return all(region in regions for region in required_regions)

    mismatched_indices = []
    
    for idx, row in df.iterrows():
        location = str(row[location_column])
        region = str(row[regional_column])
        
        if not is_valid_combination(location, region):
            mismatched_indices.append(idx)
    
    return mismatched_indices


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
            mismatches = mismatch_data(df, location_column, regional_column)

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
 