import streamlit as st
import pandas as pd
import re
import io
from difflib import get_close_matches

# ---------------------------- Parsing Logic ----------------------------

UNIT_MAP = {
    'FLOZ': 'FLUID OUNCE', 'FLUIDOUNCE': 'FLUID OUNCE', 'FLUID OUNCE': 'FLUID OUNCE', 'FL': 'FLUID OUNCE',
    'OZ': 'FLUID OUNCE', 'OUNCE': 'FLUID OUNCE', 'OZCANS': 'FLUID OUNCE', 'OZ.': 'FLUID OUNCE',
    'ML': 'ML', 'MILLILITRE': 'ML', 'MILLILITER': 'ML',
    'LTR': 'L', 'LITRE': 'L', 'LT': 'L', 'L': 'L',
    'GALLON': 'GAL', 'GAL': 'GAL'
}

COUNT_KEYWORDS = ['COUNT', 'CT', 'PACK', 'PK', 'P', 'PK/', '-PK', '-Pk']

def clean_description(desc):
    desc = desc.upper()
    desc = re.sub(r'[^\w\s.\-/]', ' ', desc)
    return re.sub(r'\s+', ' ', desc).strip()

def standardize_unit(unit):
    unit_clean = unit.replace(" ", "").replace(".", "").upper()
    match = get_close_matches(unit_clean, UNIT_MAP.keys(), n=1, cutoff=0.8)
    return UNIT_MAP.get(match[0]) if match else None

def extract_size(desc):
    size_patterns = [
        re.compile(r'(\d+(?:\.\d+)?)\s*([A-Z.\-]+)'),
        re.compile(r'(\d+(?:\.\d+)?)\s*[-xX/]\s*(\d+(?:\.\d+)?)\s*([A-Z.\-]+)')
    ]
    for pattern in size_patterns:
        match = pattern.search(desc)
        if match:
            if len(match.groups()) == 3:
                count, size_val, unit_raw = match.groups()
            else:
                size_val, unit_raw = match.groups()
                count = None
            size_unit = standardize_unit(unit_raw)
            if size_unit:
                return count, size_val, size_unit, match.group(0)
    return None, None, None, None

def extract_count(desc):
    for keyword in COUNT_KEYWORDS:
        match = re.search(rf'(\d+)\s*{keyword}', desc)
        if match:
            return match.group(1), keyword, match.group(0)
    match = re.search(r'PACK OF (\d+)', desc)
    if match:
        return match.group(1), 'PACK', match.group(0)
    return '1', 'COUNT', None

def extract_name(desc, count_text, size_text):
    if count_text:
        desc = desc.replace(count_text, '')
    if size_text:
        desc = desc.replace(size_text, '')
    desc = re.sub(r'[\-\|\*]+', ' ', desc)
    return re.sub(r'\s+', ' ', desc).title().strip()

def parse_description(original_description):
    desc = clean_description(original_description)
    count, count_unit, count_text = extract_count(desc)
    combo_count, size_val, size_unit, size_text = extract_size(desc)
    if combo_count:
        count = combo_count
    name = extract_name(desc, count_text, size_text)
    size = f"{size_val} {size_unit}" if size_val and size_unit else None
    return {
        'Product Description': original_description,
        'Product Name': name,
        'Product Size': size,
        'Product Count': f"{count} COUNT"
    }

# ---------------------------- Streamlit UI ----------------------------

st.set_page_config(page_title="NIQ", layout="centered")

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
        '12-12 FL OZ Coca Cola Cans',
        'Pack of 35 Nestle Water Bottles 16.9 oz',
       
