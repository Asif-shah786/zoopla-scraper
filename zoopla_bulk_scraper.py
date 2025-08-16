"""
zoopla_bulk_scraper.py
----------------------
Hybrid bulk scraper combining:
1. Original working headers/cookies for proper data access
2. Enhanced fields_extractor for comprehensive data extraction
3. Configurable property limit (set to 2 properties for testing)
"""

import curl_cffi
import asyncio
import json
import re
import time
import csv
from datetime import datetime
from fields_extractor import extract_from_html
from zoopla import scrape_to_json
import config

# The working headers with proper cookies for accessing full data
SEARCH_HEADERS = {
    "accept": "*/*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "next-router-state-tree": "%5B%22%22%2C%7B%22children%22%3A%5B%22(site)%22%2C%7B%22children%22%3A%5B%22(lsrp)%22%2C%7B%22children%22%3A%5B%22for-sale%22%2C%7B%22children%22%3A%5B%5B%22search-path%22%2C%22property%2Fgreater-manchester%22%2C%22c%22%5D%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%2Ctrue%5D",
    "next-url": "/for-sale/property/greater-manchester",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "rsc": "1",
    "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "cookie": 'zooplasid=0198a93dfa64728e99389a015815e7d6; __Host-zooplaat=eyJhbGciOiJQUzI1NiJ9.eyJzdWIiOiIwMTk4YTkzZGZhNjQ3MjhlOTkzODlhMDE1ODE1ZTdkNiIsInR5cGUiOiJhbm9uIiwicGxhdGZvcm0iOiJ3ZWIiLCJhdWQiOlsid3d3Lnpvb3BsYS5jby51ayIsImdyYXBocWwuem9vcGxhLmNvLnVrIl0sImlzcyI6Ind3dy56b29wbGEuY28udWsiLCJpYXQiOjE3NTUxODYwNjgsImV4cCI6MTc1NTE4Nzg2OH0.gmEytTNdIXHDMX9BNUXrtt4vK6h2Y58ydmczsLsHeDDGZYnJ5jCbINhut9gszWvboGUIxLjCBQWvvCEsK8FdOC8Lz00iAfcUEkeg5DEMfvtUcC9zgGMS3tlMQdKFKTMofd78EQPSlmOeNe0U4AFKHbUUhBrJ9pAV5vluvRIJ9k3g0ecl9sJkJ86VP3TQUnQWaLfLz-x4ar1muNlKXQKUASKBlA7jwkJHFdDi2Xc7ajljBYEfHA67LtCU-d-OC_cG0ZUPQKUQZ4214WBJKb7YJlFYn1rO-nen0yrr0y30KlIWtVN9jTtjvRlg9PpyD7VXkGrWjQj2TE279UaSiarLrg; __Host-zooplart=eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwia2lkIjoiRnFHdFpWOU85Sm45d2dHelhFd2prRWZ5S0Z6SmNDQkUyVktwUUlrcFFhZnc5UmVJVkI5dUZpblEzS25RT3JkTG85T0FpVFM3eWF3V21IOWJXdVdkcmcifQ..BImQ1CLT0HYY-LGtrBMZHA.5ExDZFcLW-91-xecJrToe0JECZTQg1wMM1oBN9pfhH8UA4GoYeRWb4ET11zPJX6F3BZRYmDp-5ljm8i5EDZGjq9fiEOMGFpIaDdP4pW3WtpZOfw2SehsNmiiF6YDnTMF6nAphR2R7-weYdC_xU9UAMtieZFy0b_JPRN2i67xBS_bN6LF28POkfHBPbfijypQ1KKiVZ9BGJCvjK7Ecd-R8PpgvA2YovznJoYxGVhGti2mdyffiqMPHxnV-iKulhwT5FUES-v8xUjlguaNPLz9CBNkC3RxIquqAAoi6a3hzkillhM9n9cn8GxO65nNQk3s4h1994Be5EFbvHg3uYT9lGUFkMliwKYBKaRzV59RuFmC7HFKsy1mdriHPiNlmLN82gXy-VLJSSQKXBJw0ridDngbg3cQKdRZYF6YrwAzmHTyhjPqVILh78y67zCql3jB5Z19aCbiFHJScSBicUbRswDQB3jwwpdCrrZhujYBfDA.kqUP_imPJRZM7nrRRq6Zh-zHk_xWjMGCYo9-tgNuy5Q; zooplapsid=cdb9d97ccb4e457bba44923225eb97c1; ajs_anonymous_id=51e11bf18f464f9ab48b74a16dfcd743; cookie_consents={"schemaVersion":4,"content":{"brand":1,"consentSelected":true,"consents":[{"apiVersion":1,"stored":false,"date":"Thu, 14 Aug 2025 15:41:12 GMT","categories":[{"id":1,"consentGiven":true},{"id":3,"consentGiven":true},{"id":4,"consentGiven":true}]}]}}; _lr_retry_request=true; _lr_env_src_ats=false; _lr_geo_location=PK; active_session=anon; rl_page_init_referrer=RS_ENC_v3_Imh0dHBzOi8vd3d3Lmdvb2dsZS5jb20vIg%3D%3D; rl_page_init_referring_domain=RS_ENC_v3_Ind3dy5nb29nbGUuY29tIg%3D%3D; rl_anonymous_id=RS_ENC_v3_IjUxZTExYmYxOGY0NjRmOWFiNDhiNzRhMTZkZmNkNzQzIg%3D%3D; idw-fe-id=2ba4f4e2-e831-4e0b-9e34-576cdd150265; optExp=1; _gcl_au=1.1.1181211119.1755186077; permutive-id=7f1eab09-d8e5-40eb-9e83-d00277da5b0c; _cs_c=0; _fbp=fb.2.1755186078467.536790398601362882; _ga=GA1.1.1395085212.1755186080; rl_trait=RS_ENC_v3_eyJjb25zZW50XzEiOnRydWUsImNvbnNlbnRfMyI6dHJ1ZSwiY29uc2VudF80Ijp0cnVlLCJmYnAiOiJmYi4yLjE3NTUxODYwNzg0NjcuNTM2NzkwMzk4NjAxMzYyODgyIiwiZ2FfY2xpZW50X2lkIjoiMTM5NTA4NTIxMi4xNzU1MTg2MDgwIn0%3D; optFea=1; _lr_sampling_rate=100; sp_fs_1=no_prefs; __cf_bm=c_2v6SNPfhmM7.26jHfzRsriNsHCHo.QTEPuOzZUgOA-1755186602-1.0.1.1-GBrwaXQFT1OSpOyNLH86hWscJFTZ8lIKUHmPCpnqtwtv.p.cCsPKwjZ6f30hY8PyJbYPF8JNhH.Nf7YElJo7Bv1stm0mjeq._Fh2ydiPBlU; _cfuvid=73kexmySj2_BZqG461_ShOfAGh0rT22XO_pMCtrEIwE-1755186602657-0.0.1.1-604800000; cf_clearance=Ls9URBwLH1DlIkFaV2IRwUChdhvC_TV746CXuizqmXg-1755186609-1.2.1.1-YpiQCvXbQuY1GCXFDyDxLsObUPtxQNv1fmOB.xfTFKBpzJvzoj2b_92AOPss1jV_wB3gVfl3tpYzWQyD34MYtVnrf1VhoH.W5gfWvH.xBDL8o9nN5FsZMqhLha.4j43Hyyeiu3fcv._yp3yjYQYsQ3zR82QYm8VHsZaEyCZZ1q.URLqpl0swLam47oUVT1KUZXFMHT0yU1BH0ED2a1nioGoRsnyo7lnzINcX0pl.vg8; cto_bundle=jxp0UF95WWYlMkZBRDUwMDJKUGxaaG9jZWclMkZmcjk5bXZ5bXdzUW9EZUVPMnN6UEo5dlRTTUxXRSUyQkJjeVpIcnVaT1FhanBSU1ZrRnVkSmZWN29rVW43WhaZzRtUTBESWtOcWlDSU91aEJ4T0x3WFVLUHhkc0ZQcDdOMWxqeU9vc3cxUWYxVDBXdlclMkYlMkJSRGUyekZ5V3FvS2xyV0lkbkoxbjRXckIxRUF1SENyWlhhUWRUOVlTZkwlMkJmZmlHOWxTayUyRjFDUm9PUGdjJTJCTm15VCUyRk1ycEVBa0MzdUltb1lnJTNEJTNE; rl_session=RS_ENC_v3_eyJhdXRvVHJhY2siOnRydWUsInRpbWVvdXQiOjE4MDAwMDAsImV4cGlyZXNBdCI6MTc1NTE4ODUxMDE0NSwiaWQiOjE3NTUxODYwNzQ0MTksInNlc3Npb25TdGFydCI6ZmFsc2V9; _cs_cvars=%7B%221%22%3A%5B%22page%22%2C%22%2Ffor-sale%2Fresults%2F%22%5D%2C%222%22%3A%5B%22activity%22%2C%22listing_search%22%5D%2C%223%22%3A%5B%22country_code%22%2C%22gb%22%5D%2C%225%22%3A%5B%22signed_in_status%22%2C%22signed%20out%22%5D%2C%228%22%3A%5B%22ab_test%22%2C%22control%7Cexpanded_search_result_filters%22%5D%2C%2211%22%3A%5B%22outcode%22%2C%22WN1%22%5D%7D; _cs_id=1b3f6041-ff44-a401-a4a2-e6a4b273d459.1755186078.1.1755186710.1755186078.1732186172.1789350078179.1.x; _ga_HMGEC3FKSZ=GS2.1.s1755186080$o1$g1$t1755186710$j58$l0$h0; _uetsid=1efe8e10792511f0a67b4d048d3a3032; _uetvid=1efe7eb0792511f088f5d57c9b24fe70; _cs_s=8.0.U.9.1755188706141; __gads=ID=5e1c5a560c832302:T=1755186073:RT=1755186912:S=ALNI_MYoGCE_h7jGjxM0RBPuVCiI4J-upQ; __gpi=UID=000012530c8330f8:T=1755186073:RT=1755186912:S=ALNI_MaS5RSJxNiAXFiKQ2iE6ZuDOb5KDQ; __eoi=ID=5f73f221c5a3ed44:T=1755186073:RT=1755186912:S=AA-AfjbDkiX9EuNbqW9E8SKrnt4M',
}

# Headers for individual property pages (standard browser-like)
PROPERTY_HEADERS = {
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

# Configuration imported from config.py
# You can modify settings in config.py instead of changing them here


def extract_property_urls_from_response(response_text: str, page_number: int) -> list:
    """Extracts property URLs from Zoopla's search results page."""
    property_urls = []

    try:
        # Look for property detail URLs in the response
        url_patterns = [
            r'https://www\.zoopla\.co\.uk/for-sale/details/(\d+)/[^"\s]*',
            r'/for-sale/details/(\d+)/[^"\s]*',
            r'"url":\s*"([^"]*for-sale/details/\d+[^"]*)"',
        ]

        for pattern in url_patterns:
            matches = re.finditer(pattern, response_text)

            for match in matches:
                if pattern.startswith("https://"):
                    url = match.group(0)
                elif pattern.startswith("/for-sale/"):
                    url = f"https://www.zoopla.co.uk{match.group(0)}"
                else:
                    url = match.group(1)

                # Extract property ID from URL
                id_match = re.search(r"/for-sale/details/(\d+)/", url)
                if id_match:
                    property_id = id_match.group(1)

                    property_data = {
                        "page": str(page_number),
                        "scraped_at": datetime.now().isoformat(),
                        "source": "zoopla",
                        "property_id": property_id,
                        "property_url": url,
                    }

                    property_urls.append(property_data)

        # Remove duplicates based on property ID
        unique_urls = []
        seen_ids = set()
        for prop in property_urls:
            if prop["property_id"] not in seen_ids:
                seen_ids.add(prop["property_id"])
                unique_urls.append(prop)

        return unique_urls

    except Exception as e:
        print(f"Error extracting property URLs from page {page_number}: {e}")
        return []


def extract_property_details_legacy(response_text: str, property_id: str) -> dict:
    """Legacy extraction function for stations/schools data from original working code."""
    details = {}

    try:
        # Extract nearest stations and distances - this is the working logic
        nearest_stations_patterns = [
            r'"nearestStations":\s*\[([^\]]+)\]',
            r'"nearestStations":\s*\["([^"]+)"(?:,\s*"([^"]+)")*\]',
        ]

        for pattern in nearest_stations_patterns:
            match = re.search(pattern, response_text)
            if match:
                stations_text = match.group(1)
                stations = [
                    s.strip().strip('"')
                    for s in stations_text.split(",")
                    if s.strip().strip('"')
                ]
                if stations:
                    details["nearest_stations"] = ", ".join(stations)
                break

        # Extract nearest stations distances
        nearest_stations_distances_patterns = [
            r'"nearestStationsInMiles":\s*\[([^\]]+)\]',
            r'"nearestStationsInMiles":\s*\[([0-9.,\s]+)\]',
        ]

        for pattern in nearest_stations_distances_patterns:
            match = re.search(pattern, response_text)
            if match:
                distances_text = match.group(1)
                distances = [d.strip() for d in distances_text.split(",") if d.strip()]
                if distances:
                    details["nearest_stations_distances"] = ", ".join(distances)
                break

        # Extract nearest schools
        nearest_schools_patterns = [
            r'"nearestSchools":\s*\[([^\]]+)\]',
            r'"nearestSchools":\s*\["([^"]+)"(?:,\s*"([^"]+)")*\]',
        ]

        for pattern in nearest_schools_patterns:
            match = re.search(pattern, response_text)
            if match:
                schools_text = match.group(1)
                schools = [
                    s.strip().strip('"')
                    for s in schools_text.split(",")
                    if s.strip().strip('"')
                ]
                if schools:
                    details["nearest_schools"] = ", ".join(schools)
                break

        # Try to extract schools from the description text as fallback
        if "nearest_schools" not in details:
            if "Good and Outstanding schools" in response_text:
                details["nearest_schools"] = "Good and Outstanding schools in the area"
            elif "local schools" in response_text:
                details["nearest_schools"] = "Local schools nearby"

    except Exception as e:
        print(f"Error in legacy extraction for {property_id}: {e}")

    return details


async def fetch_zoopla_page(page_number: int):
    """Fetches a specific results page from Zoopla and extracts property URLs."""
    print(f"\nFetching page {page_number}...")

    # Define the URL and parameters
    base_url = config.SEARCH_BASE_URL
    params = {
        "q": "Greater Manchester",
        "search_source": "for-sale",
        "_rsc": "muwg0",
        "pn": page_number,
    }

    # Update headers for this request
    headers = SEARCH_HEADERS.copy()
    if page_number > 1:
        headers["Referer"] = (
            f"{base_url}?q=Greater+Manchester&search_source=for-sale&pn={page_number - 1}"
        )
    else:
        headers["Referer"] = f"{base_url}?q=Greater+Manchester&search_source=for-sale"

    try:
        response = curl_cffi.get(
            base_url,
            params=params,
            headers=headers,
            impersonate=config.IMPERSONATE_BROWSER,
            timeout=config.REQUEST_TIMEOUT,
        )

        print(f"Status Code for page {page_number}: {response.status_code}")

        # Extract property URLs from the response
        property_urls = extract_property_urls_from_response(response.text, page_number)
        print(f"Extracted {len(property_urls)} property URLs from page {page_number}")

        return property_urls

    except Exception as e:
        print(f"An error occurred while fetching page {page_number}: {e}")
        return []


def extract_stations_schools_only(html: str, property_id: str) -> dict:
    """Extract ONLY stations and schools data using the working legacy patterns."""
    legacy_details = extract_property_details_legacy(html, property_id)
    
    # Return only stations and schools fields
    stations_schools = {}
    for key in ["nearest_stations", "nearest_stations_distances", "nearest_schools"]:
        if key in legacy_details and legacy_details[key]:
            stations_schools[key] = legacy_details[key]
    
    return stations_schools


def export_to_csv(properties_data: list, filename: str) -> None:
    """Export properties data to CSV format."""
    if not properties_data:
        return
    
    # Get all unique field names from all properties
    all_fields = set()
    for prop in properties_data:
        all_fields.update(prop.keys())
    
    # Sort fields for consistent column order
    sorted_fields = sorted(all_fields)
    
    # Write CSV file
    csv_filename = filename.replace('.json', '.csv')
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=sorted_fields)
        
        # Write header
        writer.writeheader()
        
        # Write data rows
        for prop in properties_data:
            # Clean data for CSV (handle multiline text)
            clean_prop = {}
            for key, value in prop.items():
                if isinstance(value, str):
                    # Replace newlines with semicolons for better CSV readability
                    clean_value = value.replace('\n', '; ').replace('\r', '')
                    clean_prop[key] = clean_value
                else:
                    clean_prop[key] = value
            
            writer.writerow(clean_prop)
    
    print(f"📄 CSV export saved to: {csv_filename}")


async def fetch_property_details(property_data: dict):
    """Fetches detailed information using complete zoopla.py function + append stations/schools."""
    property_id = property_data["property_id"]
    property_url = property_data["property_url"]

    print(f"\nFetching property details for ID: {property_id}")
    print(f"URL: {property_url}")

    try:
        # Step 1: Use the complete zoopla.py scrape_to_json function
        print(f"   🔄 Using zoopla.py complete extraction...")
        complete_data = scrape_to_json(property_url, property_id=property_id)
        print(f"✅ Complete extraction successful for property {property_id}")

        # Step 2: Fetch HTML with working headers for stations/schools extraction
        print(f"   🔄 Fetching HTML for stations/schools extraction...")
        working_headers = SEARCH_HEADERS.copy()
        working_headers["Referer"] = config.SEARCH_BASE_URL

        response = curl_cffi.get(
            property_url,
            headers=working_headers,
            impersonate=config.IMPERSONATE_BROWSER,
            timeout=config.REQUEST_TIMEOUT,
        )
        html = response.text
        print(f"✅ Successfully fetched HTML with working headers")

        # Step 3: Extract ONLY stations and schools data using legacy patterns
        stations_schools_data = extract_stations_schools_only(html, property_id)

        # Step 4: Append stations/schools to the complete data
        complete_data.update(stations_schools_data)

        # Step 5: Merge with original property data (preserving page info, etc.)
        final_data = property_data.copy()
        final_data.update(complete_data)

        print(f"✅ Extracted complete details for property {property_id}")

        # Debug: Check if we got stations/schools data
        if "nearest_stations" in final_data:
            print(
                f"   📍 Found {len(final_data['nearest_stations'].split(','))} stations"
            )
        if "nearest_schools" in final_data:
            print(f"   🏫 Found schools data")

        return final_data

    except Exception as e:
        print(f"❌ Error fetching property {property_id}: {e}")
        return property_data


async def main():
    """Main function to orchestrate the bulk scraping process."""
    # Record start time for filename
    start_time = datetime.now()

    print(f"🚀 Starting Zoopla Bulk Scraper")
    print(
        f"📊 Configuration: {config.MAX_PROPERTIES} properties max, {config.PAGES_TO_SCRAPE} pages, {config.REQUEST_DELAY}s delay"
    )

    all_properties = []

    # Fetch search results pages
    for page in range(1, config.PAGES_TO_SCRAPE + 1):
        property_urls = await fetch_zoopla_page(page)

        # Limit properties based on configuration
        available_slots = config.MAX_PROPERTIES - len(all_properties)
        if available_slots <= 0:
            break

        limited_urls = property_urls[:available_slots]
        all_properties.extend(limited_urls)

        print(f"Added {len(limited_urls)} properties from page {page}")

        if len(all_properties) >= config.MAX_PROPERTIES:
            break

    print(f"\n📊 Total property URLs found: {len(all_properties)}")

    # Now fetch detailed information for each property
    detailed_properties = []

    for i, property_data in enumerate(all_properties):
        print(f"\n--- Processing property {i+1}/{len(all_properties)} ---")

        # Fetch property details using hybrid approach
        detailed_property = await fetch_property_details(property_data)
        detailed_properties.append(detailed_property)

        # Add delay between requests (except for the last one)
        if i < len(all_properties) - 1:
            print(f"⏳ Waiting {config.REQUEST_DELAY} seconds before next request...")
            await asyncio.sleep(config.REQUEST_DELAY)

    # Save all detailed properties to JSON file
    if detailed_properties:
        # Record end time for filename
        end_time = datetime.now()

        # Generate meaningful filename with scraping session details
        total_properties = len(detailed_properties)
        pages_scraped = config.PAGES_TO_SCRAPE

        # Format: day-month-startTime-endTime_pageStart-pageEnd_propertyStart-propertyEnd.json
        day = start_time.strftime("%d")
        month = start_time.strftime("%B").lower()  # e.g., "july"
        start_hour = start_time.strftime("%-I%p").lower()  # e.g., "7pm"
        end_hour = end_time.strftime("%-I%p").lower()  # e.g., "8pm"

        # Page range
        if pages_scraped == 1:
            page_range = "page1"
        else:
            page_range = f"page1-{pages_scraped}"

        # Property range
        if total_properties == 1:
            property_range = "property1"
        else:
            property_range = f"property1-{total_properties}"

        # Create descriptive filename
        filename = (
            f"{day}-{month}-{start_hour}-{end_hour}_{page_range}_{property_range}.json"
        )

        # Export to JSON
        if config.EXPORT_TO_JSON:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(detailed_properties, f, indent=2, ensure_ascii=False)
            print(f"\n✅ JSON export saved to: {filename}")
        
        # Export to CSV
        if config.EXPORT_TO_CSV:
            export_to_csv(detailed_properties, filename)

        print(f"📊 Total properties processed: {len(detailed_properties)}")

        # Summary stats
        stations_count = sum(
            1 for p in detailed_properties if p.get("nearest_stations")
        )
        schools_count = sum(1 for p in detailed_properties if p.get("nearest_schools"))
        print(
            f"📍 Properties with station data: {stations_count}/{len(detailed_properties)}"
        )
        print(
            f"🏫 Properties with school data: {schools_count}/{len(detailed_properties)}"
        )
    else:
        print("\n❌ No properties were processed")


if __name__ == "__main__":
    asyncio.run(main())
