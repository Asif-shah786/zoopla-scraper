"""
zoopla.py
----------
Single-entry Zoopla scraper that:
  - fetches a property listing HTML using curl_cffi
  - extracts fields using fields_extractor.extract_from_html
  - prints/saves a clean JSON

This file supersedes the need for zoopla_property_extract.py.
"""

import json
import re
import time
from datetime import datetime
from typing import Dict, Any, Optional

from curl_cffi import requests
from fields_extractor import extract_from_html

DEFAULT_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
}


def fetch_property_html(
    url: str, referer: Optional[str] = None, timeout: int = 45
) -> str:
    headers = dict(DEFAULT_HEADERS)
    if referer:
        headers["referer"] = referer
    # TLS fingerprinting similar to Chrome to match site expectations
    resp = requests.get(url, headers=headers, impersonate="chrome", timeout=timeout)
    resp.raise_for_status()
    return resp.text


def extract_property_details(
    html: str, property_id: Optional[str] = None
) -> Dict[str, Any]:
    data = extract_from_html(html)

    # Ensure minimal normalisation for your pipeline
    if property_id and "listing_id" not in data:
        data["listing_id"] = str(property_id)

    # Aliases/compat keys
    if "address" not in data and data.get("display_address"):
        data["address"] = data["display_address"]

    # Numeric normalisation
    for k in (
        "price",
        "size_sq_feet",
        "price_per_sqft",
        "bedrooms",
        "bathrooms",
        "receptions",
    ):
        if k in data and isinstance(data[k], str):
            data[k] = data[k].replace(",", "").strip()

    return data


def scrape_to_json(
    url: str, save_html_path: Optional[str] = None, property_id: Optional[str] = None
) -> Dict[str, Any]:
    html = fetch_property_html(url)
    if save_html_path:
        with open(save_html_path, "w", encoding="utf-8") as f:
            f.write(html)

    result = extract_property_details(html, property_id=property_id)
    # Add scrape metadata
    result.update(
        {
            "page": "1",
            "scraped_at": datetime.utcnow().isoformat(),
            "source": "zoopla",
            "property_url": url,
            "property_id": property_id or result.get("listing_id") or "",
        }
    )
    return result


if __name__ == "__main__":
    import argparse, sys, os, pathlib

    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Zoopla property details URL")
    parser.add_argument("--property-id", help="Property/listing id if known")
    parser.add_argument("--save-html", help="Optional: path to save raw HTML")
    parser.add_argument(
        "--out", help="Optional: path to save JSON; prints to stdout if omitted"
    )
    args = parser.parse_args()

    data = scrape_to_json(
        args.url, save_html_path=args.save_html, property_id=args.property_id
    )
    out_json = json.dumps(data, indent=2, ensure_ascii=False)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out_json)
        print(f"Saved JSON to {args.out}")
    else:
        print(out_json)
