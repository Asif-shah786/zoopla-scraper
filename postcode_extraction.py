#!/usr/bin/env python3
"""
Geoapify Geocoding for Zoopla Properties
Uses Geoapify API to get latitude/longitude coordinates for property addresses
"""

import os
import re
import json
import time
import requests
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------- CONFIG ----------
INPUT_CSV = "data/zoopla_properties_august_mini_100.csv"
OUTPUT_CSV = "data/zoopla_properties_august_mini_100_with_geo.csv"
CACHE_FILE = "geoapify_cache.json"
API_KEY = os.getenv("GEOAPIFY_API_KEY")
COUNTRY_CODE = "gb"  # limit to UK
REQUESTS_PER_SECOND = 1  # 1 request per second as requested
MAX_RETRIES = 3
TIMEOUT_SEC = 15

if not API_KEY:
    raise RuntimeError("Please set GEOAPIFY_API environment variable in .env file")

print(f"🔑 API Key loaded: {API_KEY[:8]}...")
print(f"📁 Input file: {INPUT_CSV}")
print(f"📁 Output file: {OUTPUT_CSV}")
print(f"⏱️  Rate limit: {REQUESTS_PER_SECOND} request per second")


# ---------- HELPERS ----------
def normalize_address(addr: str) -> str:
    """Clean up address and add UK context for better geocoding"""
    if not isinstance(addr, str) or not addr.strip():
        return ""

    # Clean up spacing and strip
    a = re.sub(r"\s+", " ", addr).strip()

    # Add UK context if not present
    if "united kingdom" not in a.lower() and "uk" not in a.lower():
        a = f"{a}, United Kingdom"

    return a


def geoapify_geocode(query: str, attempt: int = 1):
    """
    Call Geoapify geocode endpoint for a single query.
    Returns a dict with lat/lon and useful fields, or None on failure.
    """
    if not query:
        return None

    params = {
        "text": query,
        "filter": f"countrycode:{COUNTRY_CODE}",
        "limit": 1,
        "apiKey": API_KEY,
    }

    url = "https://api.geoapify.com/v1/geocode/search"

    try:
        r = requests.get(url, params=params, timeout=TIMEOUT_SEC)

        # Handle different response codes
        if r.status_code == 200:
            data = r.json()
            features = data.get("features", [])

            if features:
                feature = features[0]
                properties = feature.get("properties", {})
                geometry = feature.get("geometry", {})
                coordinates = geometry.get("coordinates", [])

                # Geoapify returns [lon, lat] format
                if len(coordinates) >= 2:
                    lon, lat = coordinates[0], coordinates[1]
                else:
                    lat, lon = None, None

                return {
                    "latitude": lat,
                    "longitude": lon,
                    "postcode": properties.get("postcode"),
                    "city": properties.get("city"),
                    "county": properties.get("county"),
                    "state": properties.get("state"),
                    "result_type": properties.get("result_type"),
                    "formatted": properties.get("formatted"),
                }
            else:
                return None

        elif r.status_code == 429:  # Rate limit
            if attempt <= MAX_RETRIES:
                wait_time = 2**attempt
                print(f"⏰ Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                return geoapify_geocode(query, attempt + 1)
            else:
                print(f"❌ Rate limit exceeded after {MAX_RETRIES} retries")
                return None

        elif r.status_code == 402:  # Payment required
            print("❌ API quota exceeded or payment required")
            return None

        else:
            print(f"⚠️  API error: Status {r.status_code}")
            return None

    except requests.exceptions.Timeout:
        print(f"⏰ Timeout for: {query[:50]}...")
        return None
    except requests.exceptions.RequestException as e:
        print(f"🌐 Network error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


def load_cache(path: str) -> dict:
    """Load existing geocoding cache"""
    if Path(path).exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                cache = json.load(f)
                print(f"📋 Loaded cache with {len(cache)} entries")
                return cache
        except Exception as e:
            print(f"⚠️  Could not load cache: {e}")
    return {}


def save_cache(path: str, cache: dict):
    """Save cache to file"""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        print(f"💾 Cache saved with {len(cache)} entries")
    except Exception as e:
        print(f"⚠️  Could not save cache: {e}")


# ---------- MAIN ----------
def main():
    print("\n🚀 Starting Geoapify Geocoding")
    print("=" * 50)

    # Load dataset
    if not Path(INPUT_CSV).exists():
        print(f"❌ Input file not found: {INPUT_CSV}")
        return

    print(f"📊 Loading CSV file...")
    df = pd.read_csv(INPUT_CSV)
    print(f"✅ Loaded {len(df)} properties")

    # Check for address columns
    address_col = None
    if "address" in df.columns:
        address_col = "address"
        print("📍 Using 'address' column")
    elif "display_address" in df.columns:
        address_col = "display_address"
        print("📍 Using 'display_address' column")
    else:
        print("❌ No address column found. Available columns:")
        print(df.columns.tolist())
        return

    # Load existing cache
    cache = load_cache(CACHE_FILE)

    # Initialize geocoding columns
    df["latitude"] = None
    df["longitude"] = None
    df["postcode_geo"] = None
    df["city_geo"] = None
    df["county_geo"] = None
    df["state_geo"] = None
    df["geo_formatted"] = None
    df["geo_result_type"] = None

    # Process properties with progress bar
    print(f"\n🌍 Starting geocoding...")
    successful = 0
    failed = 0
    cached = 0

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="🌍 Geocoding"):
        address = row[address_col]

        if pd.isna(address) or not address:
            failed += 1
            continue

        # Normalize address
        normalized_addr = normalize_address(address)

        # Check cache first
        if normalized_addr in cache:
            cached += 1
            geo_data = cache[normalized_addr]
        else:
            # Geocode with API
            geo_data = geoapify_geocode(normalized_addr)

            # Cache the result
            if geo_data:
                cache[normalized_addr] = geo_data
                successful += 1
            else:
                failed += 1

            # Rate limiting
            time.sleep(1.0 / REQUESTS_PER_SECOND)

        # Update dataframe
        if geo_data:
            df.at[idx, "latitude"] = geo_data.get("latitude")
            df.at[idx, "longitude"] = geo_data.get("longitude")
            df.at[idx, "postcode_geo"] = geo_data.get("postcode")
            df.at[idx, "city_geo"] = geo_data.get("city")
            df.at[idx, "county_geo"] = geo_data.get("county")
            df.at[idx, "state_geo"] = geo_data.get("state")
            df.at[idx, "geo_formatted"] = geo_data.get("formatted")
            df.at[idx, "geo_result_type"] = geo_data.get("result_type")

    # Save cache periodically
    save_cache(CACHE_FILE, cache)

    # Final summary
    print(f"\n📊 Geocoding Complete!")
    print(f"   ✅ New geocodes: {successful}")
    print(f"   📋 From cache: {cached}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📍 Total with coordinates: {df['latitude'].notna().sum()}")

    # Save results
    print(f"\n💾 Saving results...")
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Saved to: {OUTPUT_CSV}")

    # Show sample results
    print(f"\n📋 Sample Results:")
    sample = df[df["latitude"].notna()].head(3)
    for idx, row in sample.iterrows():
        print(
            f"   {row[address_col][:50]}... → {row['latitude']:.4f}, {row['longitude']:.4f}"
        )


if __name__ == "__main__":
    main()
