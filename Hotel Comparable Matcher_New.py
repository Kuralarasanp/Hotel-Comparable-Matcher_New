import streamlit as st
import pandas as pd
 
# Mapping for Hotel Class
hotel_class_map = {
    'Economy': 1,
    'Midscale': 2,
    'Upscale': 3,
    'Upper Upscale': 4,
    'Luxury': 5
}
 
# Load Excel file
@st.cache_data
def load_excel(file):
    try:
        df = pd.read_excel(file, engine="openpyxl")
        df.columns = df.columns.str.strip()  # Remove extra spaces from column names
 
        required_cols = ['No. of Rooms', 'Market Value-2024', '2024 VPR', 'Hotel Class', 'Property Address']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            st.error(f"Missing columns in Excel file: {', '.join(missing)}")
            return None
 
        # Clean data types
        df['No. of Rooms'] = pd.to_numeric(df['No. of Rooms'], errors='coerce')
        df['Market Value-2024'] = pd.to_numeric(df['Market Value-2024'], errors='coerce')
        df['2024 VPR'] = pd.to_numeric(df['2024 VPR'], errors='coerce')
        df['Hotel Class Order'] = df['Hotel Class'].map(hotel_class_map)
        df['Property Address'] = df['Property Address'].astype(str).str.strip()
 
        df = df.dropna(subset=['No. of Rooms', 'Market Value-2024', '2024 VPR', 'Hotel Class Order'])
        df['Hotel Class Order'] = df['Hotel Class Order'].astype(int)
 
        return df
    except Exception as e:
        st.error(f"Error loading Excel: {e}")
        return None
 
# Streamlit UI
st.title("🏨 Hotel Match Finder")
 
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
 
if uploaded_file:
    df = load_excel(uploaded_file)
 
    if df is not None:
        target_mv = st.number_input("Enter Market Value-2024", step=1000.0)
        target_vpr = st.number_input("Enter 2024 VPR", step=0.1)
        hotel_class = st.selectbox("Select Hotel Class", list(hotel_class_map.keys()))
        class_order = hotel_class_map[hotel_class]
 
        if st.button("Find Matches"):
            df_filtered = df[df['Hotel Class Order'] == class_order].copy()
            df_filtered['Distance'] = ((df_filtered['Market Value-2024'] - target_mv)**2 +
                                       (df_filtered['2024 VPR'] - target_vpr)**2) ** 0.5
 
            df_result = df_filtered.sort_values(by='Distance').head(5)
 
            st.subheader("Top 5 Closest Matches")
            st.dataframe(df_result[['Property Address', 'Market Value-2024', '2024 VPR', 'Hotel Class']])
