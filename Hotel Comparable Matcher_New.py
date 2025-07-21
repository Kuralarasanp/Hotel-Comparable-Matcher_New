import streamlit as st
import pandas as pd
 
# Hotel Class Mapping
hotel_class_map = {
    'Economy': 1,
    'Midscale': 2,
    'Upscale': 3,
    'Upper Upscale': 4,
    'Luxury': 5
}
 
# Load Excel function
@st.cache_data
def load_excel(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
        df.columns = df.columns.str.strip()  # Remove leading/trailing spaces
 
        # Check if required columns exist
        required_cols = ['No. of Rooms', 'Market Value-2024', '2024 VPR', 'Hotel Class', 'Property Address']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Missing columns in Excel file: {', '.join(missing_cols)}")
            return None
 
        # Convert and clean
        df['No. of Rooms'] = pd.to_numeric(df['No. of Rooms'], errors='coerce')
        df['Market Value-2024'] = pd.to_numeric(df['Market Value-2024'], errors='coerce')
        df['2024 VPR'] = pd.to_numeric(df['2024 VPR'], errors='coerce')
        df['Hotel Class Order'] = df['Hotel Class'].map(hotel_class_map)
 
        df = df.dropna(subset=['No. of Rooms', 'Market Value-2024', '2024 VPR', 'Hotel Class Order'])
        df['Hotel Class Order'] = df['Hotel Class Order'].astype(int)
        df['Property Address'] = df['Property Address'].astype(str).str.strip()
 
        return df
    except Exception as e:
        st.error(f"Error loading Excel: {e}")
        return None
 
# App Title
st.title("🏨 Hotel Match Finder")
 
# File Upload
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
 
if uploaded_file:
    df = load_excel(uploaded_file)
 
    if df is not None:
        # User Inputs
        target_mv = st.number_input("Enter Market Value-2024", step=1000.0)
        target_vpr = st.number_input("Enter 2024 VPR", step=0.1)
        hotel_class = st.selectbox("Select Hotel Class", options=list(hotel_class_map.keys()))
        class_order = hotel_class_map[hotel_class]
 
        # Button to trigger matching
        if st.button("Find Matches"):
            df_filtered = df[df['Hotel Class Order'] == class_order].copy()
            df_filtered['distance'] = ((df_filtered['Market Value-2024'] - target_mv)**2 + 
                                       (df_filtered['2024 VPR'] - target_vpr)**2) ** 0.5
            df_sorted = df_filtered.sort_values(by='distance').head(5)
 
            st.subheader("Top 5 Closest Matches")
            st.dataframe(df_sorted[['Property Address', 'Market Value-2024', '2024 VPR', 'Hotel Class']])
