#!/usr/bin/env python3
"""
Create Simple JSON from Cleaned CSV
Extracts 5 items and creates a clean, simple JSON file
"""

import pandas as pd
import json


def create_simple_json():
    # Load the cleaned CSV
    df = pd.read_csv("data/zoopla_properties_august_mini_100_with_geo_cleaned.csv")

    print(f"📊 Loaded {len(df)} properties from cleaned CSV")

    # Take first 5 items
    sample_df = df.head(5)

    # Create simple JSON structure
    properties = []

    for idx, row in sample_df.iterrows():
        property_data = {
            "id": idx + 1,
            "title": row.get("listing_title", ""),
            "address": row.get("address", ""),
            "price": row.get("price", ""),
            "property_type": row.get("property_type", ""),
            "bedrooms": row.get("bedrooms_int", ""),
            "bathrooms": row.get("bathrooms_int", ""),
            "receptions": row.get("receptions_int", ""),
            "tenure": row.get("tenure", ""),
            "status": row.get("status", ""),
            "location": {
                "latitude": row.get("lat", ""),
                "longitude": row.get("lon", ""),
                "postcode": row.get("postcode", ""),
                "city": row.get("town_city", ""),
                "county": row.get("county", ""),
            },
            "details": {
                "size_sqft": row.get("size_sqft", ""),
                "price_per_sqft": row.get("price_per_sqft", ""),
                "council_tax_band": row.get("council_tax_band", ""),
                "agent": row.get("agent_name", ""),
            },
        }

        # Clean up empty values
        for key, value in property_data.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if pd.isna(sub_value) or sub_value == "":
                        property_data[key][sub_key] = None
            else:
                if pd.isna(value) or value == "":
                    property_data[key] = None

        properties.append(property_data)

    # Create final JSON structure
    output_data = {
        "total_properties": len(properties),
        "source": "zoopla_properties_august_mini_100_with_geo_cleaned.csv",
        "properties": properties,
    }

    # Save to JSON file
    output_file = "data/simple_properties_sample.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Created simple JSON with {len(properties)} properties")
    print(f"📁 Saved to: {output_file}")

    # Show sample of what was created
    print(f"\n📋 Sample JSON structure:")
    print(json.dumps(properties[0], indent=2, ensure_ascii=False)[:500] + "...")

    return output_file


if __name__ == "__main__":
    create_simple_json()
