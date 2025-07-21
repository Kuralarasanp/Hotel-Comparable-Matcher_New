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
 
# Load Excel function with openpyxl engine

@st.cache_data

def load_excel(uploaded_file):

    df = pd.read_excel(uploaded_file, engine="openpyxl")

    df.columns = [col.strip() for col in df.columns]

    cols_to_numeric = ['No. of Rooms', 'Market Value-2024', '2024 VPR']

    for col in cols_to_numeric:

        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.dropna(subset=cols_to_numeric)

    df['Hotel Class Order'] = df['Hotel Class'].map(hotel_class_map)

    df = df.dropna(subset=['Hotel Class Order'])

    df['Hotel Class Order'] = df['Hotel Class Order'].astype(int)

    df['Property Address'] = df['Property Address'].astype(str).str.strip()

    return df
 
st.title("Hotel Match Finder (Market Value & VPR Based)")
 
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:

    df = load_excel(uploaded_file)
 
    # User input for matching

    target_mv = st.number_input("Enter Market Value-2024", step=1000.0)

    target_vpr = st.number_input("Enter 2024 VPR", step=0.1)

    hotel_class = st.selectbox("Select Hotel Class", options=list(hotel_class_map.keys()))

    class_order = hotel_class_map[hotel_class]
 
    if st.button("Find Matches"):

        df_filtered = df[df['Hotel Class Order'] == class_order].copy()

        df_filtered['distance'] = ((df_filtered['Market Value-2024'] - target_mv)**2 + 

                                   (df_filtered['2024 VPR'] - target_vpr)**2) ** 0.5

        df_sorted = df_filtered.sort_values(by='distance').head(5)
 
        st.write("Top 5 Closest Matches:")

        st.dataframe(df_sorted[['Property Address', 'Market Value-2024', '2024 VPR', 'Hotel Class']])

 
