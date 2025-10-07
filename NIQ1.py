import streamlit as st
import pandas as pd
import re
import io
 
# ---------------------------- Core Parsing Functions ----------------------------
 
UNIT_MAP = {
    'FLOZ': 'FL OZ', 'FLUIDOUNCE': 'FL OZ', 'FLUID OUNCE': 'FL OZ', 'FL': 'FL OZ',
    'OZ': 'FL OZ', 'OUNCE': 'FL OZ', 'OZ.': 'FL OZ', 'OZCANS': 'FL OZ', ' OZ': 'FL OZ',
    'FL. OZ.': 'FL OZ', 'OZ CANS': 'FL OZ', 'FLUID-OZ': 'FL OZ', 'FLUID OZ': 'FL OZ',
    'FL.OZ.': 'FL OZ', 'Ozbottles': 'FL OZ', 'Flozcans': 'FL OZ', 'FLOZCANS': 'FL OZ',
    'OZBOTTLES': 'FL OZ', 'ozbottles': 'FL OZ', 'oz bottles': 'FL OZ', 'OZ bottles': 'FL OZ',
    'FLOZBOTTLES': 'FL OZ', 'OUNCES': 'FL OZ', 'ounnces': 'FL OZ',
    'ML': 'ML', 'MILLILITRE': 'ML', 'MILLILITER': 'ML',
    'LTR': 'L', 'LITRE': 'L', 'LT': 'L', 'L': 'L',
    'GALLON': 'GAL', 'GAL': 'GAL'
}

COUNT_KEYWORDS = ['COUNT', 'CT', 'PACK', 'PK', 'P', 'PK/', '-Pk', '-PK']

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

    # Match patterns like "12 PK", "PACK OF 12"
    pack_inline_match = re.search(r'(\d+)\s*(PK/|PK|CT|PACK|P)(?=[\s/])?', desc)
    if pack_inline_match:
        count = pack_inline_match.group(1)
        count_unit = pack_inline_match.group(2)
        count_text_to_remove = pack_inline_match.group(0)

    # Match patterns like "8 x 500ml"
    combo_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*[-xX]\s*(\d+(?:\.\d+)?)\s*([A-Z.\s\-]+)')
    combo_match = combo_pattern.search(desc)
    if combo_match:
        count = combo_match.group(1)
        size_value = combo_match.group(2)
        unit_raw = combo_match.group(3).strip()
        size_unit = standardize_unit(unit_raw)
        size_text_to_remove = combo_match.group(0)
        count_text_to_remove = count
        return extract_name(desc, count_text_to_remove, size_text_to_remove, count, size_value, size_unit)

    pack_of_match = re.search(r'PACK OF (\d+)', desc)
    if pack_of_match:
        count = pack_of_match.group(1)
        count_unit = 'PACK'
        count_text_to_remove = pack_of_match.group(0)

    tokens = desc.split()
    for i, token in enumerate(tokens):
        if token in COUNT_KEYWORDS and i > 0 and tokens[i - 1].isdigit():
            count = tokens[i - 1]
            count_unit = token
            count_text_to_remove = f"{count} {count_unit}"
            break
        elif token.isdigit() and i + 1 < len(tokens) and tokens[i + 1] in COUNT_KEYWORDS:
            count = token
            count_unit = tokens[i + 1]
            count_text_to_remove = f"{count} {count_unit}"
            break

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

    # Ensure size and count are not left blank
    if not size_value or not size_unit:
        size_value = '1'
        size_unit = 'FL OZ'
    if not count:
        count = '1'

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
    size = f"{size_value} {size_unit}" if size_value and size_unit else "1 FL OZ"
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
