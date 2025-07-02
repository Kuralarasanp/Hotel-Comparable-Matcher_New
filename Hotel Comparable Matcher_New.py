import streamlit as st
import pandas as pd
import numpy as np
import io

# Hotel class mapping
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

def get_least_one(df):
    return df.sort_values(['Market Value-2024', '2024 VPR'], ascending=[True, True]).head(1)

def get_top_one(df):
    return df.sort_values(['Market Value-2024', '2024 VPR'], ascending=[False, False]).head(1)

def get_nearest_three(df, target_mv, target_vpr):
    df = df.copy()
    df['distance'] = np.sqrt((df['Market Value-2024'] - target_mv) ** 2 + (df['2024 VPR'] - target_vpr) ** 2)
    return df.sort_values('distance').head(3).drop(columns='distance')

# UI
st.title("🏨 Hotel Comparable Matcher Tool")

uploaded_file = st.file_uploader("📤 Upload Excel File", type=['xlsx'])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = [col.strip() for col in df.columns]

    # Preprocessing
    for col in ['No. of Rooms', 'Market Value-2024', '2024 VPR']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['No. of Rooms', 'Market Value-2024', '2024 VPR'])

    df['Hotel Class Order'] = df['Hotel Class'].map(hotel_class_map)
    df = df.dropna(subset=['Hotel Class Order'])
    df['Hotel Class Order'] = df['Hotel Class Order'].astype(int)
    df['Project / Hotel Name'] = df['Project / Hotel Name'].astype(str).str.strip()

    project_names = df['Project / Hotel Name'].dropna().unique().tolist()

    selected_hotels = st.multiselect(
        "🏨 Select Hotel(s)",
        options=["[SELECT ALL]"] + project_names,
        default=["[SELECT ALL]"]
    )

    if "[SELECT ALL]" in selected_hotels:
        selected_rows = df.copy()
    else:
        selected_rows = df[df['Project / Hotel Name'].isin(selected_hotels)]

    # Filters
    mv_min = st.number_input("🔽 Market Value Min Filter %", 0.0, 500.0, 80.0, 1.0)
    mv_max = st.number_input("🔼 Market Value Max Filter %", mv_min, 500.0, 120.0, 1.0)
    vpr_min = st.number_input("🔽 VPR Min Filter %", 0.0, 500.0, 80.0, 1.0)
    vpr_max = st.number_input("🔼 VPR Max Filter %", vpr_min, 500.0, 120.0, 1.0)

    max_results_per_row = 5
    all_columns = df.columns.tolist()

    if st.button("🚀 Run Matching"):
        result_rows = []

        with st.spinner("🔍 Matching in progress..."):
            for _, base_row in selected_rows.iterrows():
                base_name = base_row['Project / Hotel Name']
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
                    subset=['Project / Hotel Name', 'Owner Street Address', 'Owner Name/ LLC Name'],
                    keep='first'
                )

                if not matching_rows.empty:
                    nearest_3 = get_nearest_three(matching_rows, base_market_val, base_vpr)
                    remaining = matching_rows[~matching_rows.index.isin(nearest_3.index)]
                    least_1 = get_least_one(remaining)
                    remaining = remaining[~remaining.index.isin(least_1.index)]
                    top_1 = get_top_one(remaining)

                    final_matches = pd.concat([nearest_3, least_1, top_1]).drop_duplicates().reset_index(drop=True)

                    for idx in range(min(max_results_per_row, len(final_matches))):
                        match_row = final_matches.iloc[idx]
                        combined = match_row.copy()
                        combined['Base Hotel'] = base_name
                        combined['Result No.'] = idx + 1
                        result_rows.append(combined)
                else:
                    st.info(f"No matches found for **{base_name}**.")

        if result_rows:
            result_df = pd.DataFrame(result_rows)
            st.success("✅ Matching complete")
            st.dataframe(result_df)

            output = io.BytesIO()
            result_df.to_excel(output, index=False)
            st.download_button(
                label="📥 Download All Matched Results",
                data=output.getvalue(),
                file_name="hotel_matched_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("⚠️ No matching results to download.")
