# -*- coding: utf-8 -*-
"""
Data preprocessing module for real estate RAG pipeline.

This module cleans and prepares property data for vector embedding and retrieval.
"""

import pandas as pd
import re
from typing import Optional, List


def clean_text(text) -> str:
    """Clean text data by removing extra whitespace and newlines."""
    if isinstance(text, str):
        # Remove extra whitespace and newline characters
        text = re.sub("\s+", " ", text).strip()
        return text
    return text


def load_and_clean_data(
    json_file_path: str, output_dir: str = "ready_data"
) -> pd.DataFrame:
    """
    Load and clean real estate data from JSON file.

    Args:
        json_file_path: Path to the input JSON file
        output_dir: Directory to save cleaned output files

    Returns:
        Cleaned pandas DataFrame
    """
    print("Step 1: Loading data...")

    try:
        df = pd.read_json(json_file_path)
        print("✓ JSON file loaded successfully!")
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {json_file_path}")
    except Exception as e:
        raise Exception(f"Error loading file: {e}")

    print("Step 2: Selecting relevant columns...")

    # Define columns to keep (in order of importance)
    columns_to_keep = [
        "property_id",
        "property_url",
        "price",
        "property_type",
        "tenure",
        "bedrooms",
        "bathrooms",
        "receptions",
        "outcode",
        "chain_free",
        "number_of_photos",
        "number_of_floorplans",
        "address",
        "council_tax_band",
        "ground_rent",
        "nearest_stations",
        "nearest_schools",
        "latitude",
        "longitude",
        "epc_rating",
        "size_sqft",
        "title",
        "agent",
        "about_property",
        # Crime data fields
        "crime_summary",
        "crime_data",
    ]

    # Filter to only keep columns that exist in the DataFrame
    existing_columns = [col for col in columns_to_keep if col in df.columns]
    df_cleaned = df[existing_columns].copy()

    # Field mapping for better naming
    field_mapping = {
        "outcode": "postcode",
        "latitude": "lat",
        "longitude": "lng",
        "agent": "agent_name",
        "about_property": "description",
    }

    # Rename fields that exist
    for old_name, new_name in field_mapping.items():
        if old_name in df_cleaned.columns:
            df_cleaned = df_cleaned.rename(columns={old_name: new_name})

    print("✓ Relevant columns selected")

    print("Step 3: Handling missing values...")

    # Check for missing values initially
    missing_counts = df_cleaned.isnull().sum()
    print(f"Missing values found: {missing_counts[missing_counts > 0].to_dict()}")

    # Impute missing values with mode for categorical columns
    categorical_cols = [
        "bathrooms",
        "receptions",
        "property_type",
        "council_tax_band",
        "tenure",
    ]
    for col in categorical_cols:
        if col in df_cleaned.columns and df_cleaned[col].isnull().sum() > 0:
            mode_val = df_cleaned[col].mode()
            if not mode_val.empty:
                df_cleaned[col] = df_cleaned[col].fillna(mode_val[0])
                print(f"✓ Filled missing {col} with mode")

    print("✓ Missing values handled")

    print("Step 4: Converting data types...")

    # Convert numerical columns
    numeric_cols = ["bathrooms", "bedrooms", "price", "receptions", "size_sqft"]
    for col in numeric_cols:
        if col in df_cleaned.columns:
            df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors="coerce")

    print("✓ Data types converted")

    print("Step 5: Cleaning text data...")

    # Clean text data (exclude URLs and coordinates)
    text_cols = [
        "description",
        "address",
        "title",
        "agent_name",
        "nearest_stations",
        "nearest_schools",
        "epc_rating",
        "council_tax_band",
    ]

    for col in text_cols:
        if col in df_cleaned.columns:
            df_cleaned[col] = df_cleaned[col].apply(clean_text)

    print("✓ Text data cleaned")

    print("Step 6: Creating numeric helper columns...")

    # Create numeric helper columns
    if "bedrooms" in df_cleaned.columns:
        df_cleaned["bedrooms_int"] = df_cleaned["bedrooms"].astype("Int64")
    if "bathrooms" in df_cleaned.columns:
        df_cleaned["bathrooms_int"] = df_cleaned["bathrooms"].astype("Int64")
    if "receptions" in df_cleaned.columns:
        df_cleaned["receptions_int"] = df_cleaned["receptions"].astype("Int64")
    if "price" in df_cleaned.columns:
        df_cleaned["price_num"] = df_cleaned["price"].astype("float64")
    if "size_sqft" in df_cleaned.columns:
        df_cleaned["size_sqft_num"] = df_cleaned["size_sqft"].astype("float64")

    print("✓ Numeric helper columns created")

    print("Step 7: Saving cleaned data...")

    # Save cleaned data
    import os

    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(json_file_path))[0]
    csv_path = os.path.join(output_dir, f"{base_name}_cleaned.csv")
    json_path = os.path.join(output_dir, f"{base_name}_cleaned.json")

    df_cleaned.to_csv(csv_path, index=False)
    df_cleaned.to_json(json_path, indent=2, orient="records")

    print(f"✓ Cleaned data saved to:")
    print(f"  CSV: {csv_path}")
    print(f"  JSON: {json_path}")

    return df_cleaned


def load_crime_data(crime_file_path: str) -> pd.DataFrame:
    """
    Load crime data from JSON file.

    Args:
        crime_file_path: Path to the crime data JSON file

    Returns:
        Crime data pandas DataFrame
    """
    try:
        df_crime = pd.read_json(crime_file_path)
        print(f"✓ Crime data loaded from {crime_file_path}")
        return df_crime
    except FileNotFoundError:
        print(f"⚠️  Crime data file not found: {crime_file_path}")
        return pd.DataFrame()
    except Exception as e:
        print(f"⚠️  Error loading crime data: {e}")
        return pd.DataFrame()


if __name__ == "__main__":
    # Example usage
    try:
        # Load and clean the main property data and save to ready_data folder
        df_cleaned = load_and_clean_data(
            "18-august-12pm_page1-ALL_property1-10_cleaned.json"
        )

        print("\n🎉 Data preprocessing completed successfully!")
        print(f"Final dataset shape: {df_cleaned.shape}")

    except Exception as e:
        print(f"❌ Error during preprocessing: {e}")
