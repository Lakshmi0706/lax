import streamlit as st
import pandas as pd
import re
import io

# ---------------------------- Core Parsing Functions ----------------------------

UNIT_MAP = {
    'FLOZ': 'FLUID OUNCE', 'FLUIDOUNCE': 'FLUID OUNCE', 'FLUID OUNCE': 'FLUID OUNCE', 'FL': 'FLUID OUNCE',
    'OZ': 'FLUID OUNCE', 'OUNCE': 'FLUID OUNCE', 'OZ.': 'FLUID OUNCE', 'OZCANS': 'FLUID OUNCE', ' OZ': 'FLUID OUNCE',
    'FL. OZ.': 'FLUID OUNCE', 'OZ CANS': 'FLUID OUNCE', 'FLUID-OZ': 'FLUID OUNCE', 'FLUID OZ': 'FLUID OUNCE',
    'FL.OZ.': 'FLUID OUNCE', 'Ozbottles': 'FLUID OUNCE', 'Flozcans': 'FLUID OUNCE', 'FLOZCANS': 'FLUID OUNCE',
    'OZBOTTLES': 'FLUID OUNCE', 'ozbottles': 'FLUID OUNCE', 'oz bottles': 'FLUID OUNCE', 'OZ bottles': 'FLUID OUNCE',
    'FLOZBOTTLES': 'FLUID OUNCE', 'OUNCES': 'FLUID OUNCE', 'ounnces': 'FLUID OUNCE',
    'ML': 'ML', 'MILLILITRE': 'ML', 'MILLILITER': 'ML',
    'LTR': 'L', 'LITRE': 'L', 'LT': 'L', 'L': 'L',
    'GALLON': 'GAL', 'GAL': 'GAL'
}

COUNT_KEYWORDS = ['COUNT', 'CT', 'PACK', 'PK', 'P', 'PK/', '-PK', '-Pk']

def clean_description(desc):
    desc = desc.upper()
    desc = re.sub(r'[^\w\s.\-\|/]', ' ', desc)
    desc = re.sub(r'\s+', ' ', desc)
    return desc.strip()

def standardize_unit(unit):
    unit_clean = unit.replace(" ", "").replace(".", "").upper()
    return UNIT_MAP.get(unit_clean, None)

def extract_size_and_count(description):
    desc = clean_description(description)
    count = '1'
    count_unit = 'COUNT'
    size_value = None
    size_unit = None
    size_text_to_remove = None
    count_text_to_remove = None

    # --- Detect Pack Count (12-PK, 8 PK, 10 CT, etc.)
    pack_inline_match = re.search(r'(\d+)\s*(?:-?\s*)(PK|PACK|CT|COUNT|P)(?=[\s/]|$)', desc)
    if pack_inline_match:
        count = pack_inline_match.group(1)
        count_unit = 'COUNT'
        count_text_to_remove = pack_inline_match.group(0)

    # --- Detect combined patterns like "8 x 500ml"
    combo_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*[-xX]\s*(\d+(?:\.\d+)?)\s*([A-Z.\s\-]+)')
    combo_match = combo_pattern.search(desc)
    if combo_match:
        count = combo_match.group(1)
        size_value = combo_match.group(2)
        unit_raw = combo_match.group(3).strip()
        size_unit = standardize_unit(unit_raw)
        size_text_to_remove = combo_match.group(0)
        count_text_to_remove = combo_match.group(1)
        return extract_name(desc, count_text_to_remove, size_text_to_remove, count, size_value, size_unit)

    # --- Detect "PACK OF 6"
    pack_of_match = re.search(r'PACK OF (\d+)', desc)
    if pack_of_match:
        count = pack_of_match.group(1)
        count_text_to_remove = pack_of_match.group(0)

    # --- Detect size like "16.9 FL OZ"
    size_patterns = [re.compile(r'(\d+(?:\.\d+)?)[\-\s]?([A-Z.\-]+)')]
    for pattern in size_patterns:
        for match in pattern.finditer(desc):
            num = match.group(1)
            unit_raw = match.group(2).strip()
            std_unit = standardize_unit(unit_raw)
            if std_unit:
                size_value = num
                size_unit = std_unit
                size_text_to_remove = match.group(0)
                break
        if size_value and size_unit:
            break

    return extract_name(desc, count_text_to_remove, size_text_to_remove, count, size_value, size_unit)

def extract_name(description, count_text, size_text, count, size_value, size_unit):
    name_desc = description
    if count_text:
        name_desc = name_desc.replace(count_text, '')
    if size_text:
        name_desc = name_desc.replace(size_text, '')
    name_desc = re.sub(r'[\-\|\*]+', ' ', name_desc)
    name_desc = re.sub(r'\s+', ' ', name_desc).strip()
    name = name_desc.title()
    size = f"{size_value} {size_unit}" if size_value and size_unit else None
    count_combined = f"{count} COUNT"
    return name, size, count, count_combined

def parse_description(original_description):
    name, size, _, count_combined = extract_size_and_count(original_description)
    return {
        'Product Description': original_description,
        'Product Name': name,
        'Product Size': size,
        'Product Count': count_combined
    }

# ---------------------------- Streamlit App Starts Here ----------------------------

st.set_page_config(page_title="NIQ", layout="wide")

st.markdown("""
    <div style='text-align:center; padding:20px; background-color:#0077B6; color:white; border-radius:10px;'>
        <h1 style='margin-bottom:0;'>NIQ</h1>
        <p style='font-size:18px;'>Product Description Parser</p>
    </div>
""", unsafe_allow_html=True)

st.markdown("#### 📥 Upload an Excel file with product descriptions")
uploaded_file = st.file_uploader("Drop your `.xlsx` or `.xlsm` file here", type=["xlsx", "xlsm"])

# 📄 Sample Excel Download
sample_df = pd.DataFrame({
    'ProductDescriptions': [
        '12-PK 12 FL OZ Coca Cola Cans',
        'Pack of 35 Nestle Water Bottles 16.9 oz',
        '8 x 500ml Pepsi Max Bottles',
        'Cocacola Cherry Soda Mini Cans 10-PK / 7.5 FL OZ'
    ]
})
excel_buffer = io.BytesIO()
sample_df.to_excel(excel_buffer, index=False, engine='openpyxl')
st.download_button(
    label="📄 Download Sample Excel File",
    data=excel_buffer.getvalue(),
    file_name="sample_product_descriptions.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.markdown("---")

if uploaded_file:
    try:
        excel_data = pd.read_excel(uploaded_file, engine='openpyxl')
        st.success("✅ Excel file uploaded successfully!")

        with st.expander("🔍 Preview Uploaded Data", expanded=True):
            st.dataframe(excel_data.head(), use_container_width=True)

        column_options = list(excel_data.columns)
        selected_column = st.selectbox("Select the column containing product descriptions:", column_options)

        st.markdown("### 🧩 Select additional columns to include in the output")
        selected_extra_columns = []
        for col in column_options:
            if col != selected_column and st.checkbox(f"Include column: {col}", value=False):
                selected_extra_columns.append(col)

        if st.button("🚀 Parse Descriptions"):
            description_lines = excel_data[selected_column].dropna().astype(str).tolist()
            results = [parse_description(desc) for desc in description_lines]
            parsed_df = pd.DataFrame(results)

            for col in selected_extra_columns:
                parsed_df[col] = excel_data[col]

            st.success("✅ Parsing complete!")
            st.dataframe(parsed_df, use_container_width=True)

            csv = parsed_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Combined CSV", data=csv, file_name="parsed_products_with_columns.csv", mime="text/csv")

    except Exception as e:
        st.error(f"❌ Failed to read Excel file: {e}")
else:
    st.info("Please upload an Excel file to begin.")
