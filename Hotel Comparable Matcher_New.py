import streamlit as st
import pandas as pd
import numpy as np
import io

# -----------------------------
# Mapping Definitions
# -----------------------------
hotel_class_map = {
    "Budget (Low End)": 1,
    "Economy (Name Brand)": 2,
    "Midscale": 3,
    "Upper Midscale": 4,
    "Upscale": 5,
    "Upper Upscale First Class": 6,
    "Luxury Class": 7,
    "Independent Hotel": 8
}

allowed_orders_map = {
    1: [1, 2, 3],
    2: [1, 2, 3, 4],
    3: [2, 3, 4, 5],
    4: [3, 4, 5, 6],
    5: [4, 5, 6, 7],
    6: [5, 6, 7, 8],
    7: [6, 7, 8],
    8: [7, 8]
}

# -----------------------------
# Helper Functions
# -----------------------------
def get_least_one(df):
    return df.sort_values(['Market Value-2024', '2024 VPR'], ascending=[True, True]).head(1)

def get_top_one(df):
    return df.sort_values(['Market Value-2024', '2024 VPR'], ascending=[False, False]).head(1)

def get_nearest_three(df, target_mv, target_vpr):
    df = df.copy()
    df['distance'] = np.sqrt((df['Market Value-2024'] - target_mv) ** 2 + (df['2024 VPR'] - target_vpr) ** 2)
    return df.sort_values('distance').head(3).drop(columns='distance')

@st.cache_data
def load_excel(uploaded_file):
    df = pd.read_excel(uploaded_file)
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

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Hotel Matcher", layout="wide")
st.title("🏨 Hotel Comparable Matcher Tool")

uploaded_file = st.file_uploader("📤 Upload Excel File (.xlsx)", type=['xlsx'])

if uploaded_file:
    try:
        df = load_excel(uploaded_file)
    except Exception as e:
        st.error(f"❌ Failed to read Excel file: {e}")
        st.stop()

    property_list = df['Property Address'].dropna().tolist()

    selected_hotels = st.multiselect(
        "🏨 Select Property Address",
        options=["[SELECT ALL]"] + property_list,
        default=["[SELECT ALL]"]
    )

    if "[SELECT ALL]" in selected_hotels:
        selected_rows = df.copy()
    else:
        selected_rows = df[df['Property Address'].isin(selected_hotels)]

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        mv_min = st.number_input("🔽 Market Value Min %", 0.0, 500.0, 80.0)
    with col2:
        mv_max = st.number_input("🔼 Market Value Max %", mv_min, 500.0, 120.0)

    col3, col4 = st.columns(2)
    with col3:
        vpr_min = st.number_input("🔽 VPR Min %", 0.0, 500.0, 80.0)
    with col4:
        vpr_max = st.number_input("🔼 VPR Max %", vpr_min, 500.0, 120.0)

    max_results_per_row = st.slider("🔢 Max Matches Per Hotel", 1, 10, 5)

    if st.button("🚀 Run Matching"):
        results_rows = []
        match_columns = [
            'Property Address', 'State', 'Property County',
            'No. of Rooms', 'Market Value-2024', '2024 VPR',
            'Hotel Class', 'Hotel Class Order'
        ]
        all_columns = [col for col in df.columns if col != 'Hotel Class Order'] + ['Hotel Class Order']

        with st.spinner("🔍 Matching in progress..."):
            for _, base_row in selected_rows.iterrows():
                try:
                    base_market_val = base_row['Market Value-2024']
                    base_vpr = base_row['2024 VPR']
                    base_order = base_row['Hotel Class Order']
                    allowed_orders = allowed_orders_map.get(base_order, [])
                    subset = df[df.index != base_row.name]

                    mask = (
                        (subset['State'] == base_row['State']) &
                        (subset['Property County'] == base_row['Property County']) &
                        (subset['No. of Rooms'] < base_row['No. of Rooms']) &
                        (subset['Market Value-2024'].between(base_market_val * (mv_min / 100), base_market_val * (mv_max / 100))) &
                        (subset['2024 VPR'].between(base_vpr * (vpr_min / 100), base_vpr * (vpr_max / 100))) &
                        (subset['Hotel Class Order'].isin(allowed_orders))
                    )

                    matching_rows = subset[mask].drop_duplicates(
                        subset=['Project / Hotel Name', 'Owner Street Address', 'Owner Name/ LLC Name'], keep='first'
                    )

                    base_data = base_row[match_columns].to_dict()

                    if not matching_rows.empty:
                        nearest_3 = get_nearest_three(matching_rows, base_market_val, base_vpr)
                        remaining = matching_rows[~matching_rows.index.isin(nearest_3.index)]
                        least_1 = get_least_one(remaining)
                        remaining = remaining[~remaining.index.isin(least_1.index)]
                        top_1 = get_top_one(remaining)

                        selected_rows_final = pd.concat([nearest_3, least_1, top_1]).drop_duplicates().reset_index(drop=True)
                        result_count = min(len(selected_rows_final), max_results_per_row)

                        combined_row = base_data.copy()
                        combined_row['Matching Results Count / Status'] = f"Total: {len(matching_rows)} | Selected: {result_count}"

                        for idx in range(max_results_per_row):
                            prefix = f"Result {idx + 1} - "
                            if idx < result_count:
                                match_row = selected_rows_final.iloc[idx]
                                for col in all_columns:
                                    combined_row[prefix + col] = match_row[col]
                            else:
                                for col in all_columns:
                                    combined_row[prefix + col] = None

                        results_rows.append(combined_row)
                    else:
                        combined_row = base_data.copy()
                        combined_row['Matching Results Count / Status'] = 'No_Match_Case'
                        for idx in range(max_results_per_row):
                            prefix = f"Result {idx + 1} - "
                            for col in all_columns:
                                combined_row[prefix + col] = None
                        results_rows.append(combined_row)

                except Exception as e:
                    st.error(f"❌ Error on hotel '{base_row['Property Address']}': {e}")

        if results_rows:
            result_df = pd.DataFrame(results_rows)
            st.success("✅ Matching Completed")

            selected_indices = st.multiselect(
                "🔘 Select rows to download",
                options=result_df.index.tolist(),
                format_func=lambda x: f"Row {x}: {result_df.at[x, 'Property Address']}"
            )

            st.dataframe(result_df)

            match_count = (result_df['Matching Results Count / Status'] != 'No_Match_Case').sum()
            total_processed = len(result_df)

            st.write("### 📊 Summary")
            st.write(f"- ✅ Matches Found: {match_count}")
            st.write(f"- ❌ No Matches: {total_processed - match_count}")
            st.write(f"- 🔢 Total Processed: {total_processed}")

            if selected_indices:
                filtered_df = result_df.loc[selected_indices]
                output = io.BytesIO()
                filtered_df.to_excel(output, index=False)
                st.download_button(
                    label="📥 Download Selected Matches",
                    data=output.getvalue(),
                    file_name="hotel_selected_matches.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.info("ℹ️ Select rows above to enable download.")
