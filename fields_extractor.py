import re
import json
from typing import Dict, Any, Optional, List
from curl_cffi import requests

# --------- Helpers ---------


def _coerce_int(val) -> Optional[int]:
    try:
        return int(str(val).replace(",", "").strip())
    except Exception:
        return None


def _coerce_float(val) -> Optional[float]:
    try:
        return float(str(val).replace(",", "").strip())
    except Exception:
        return None


def _norm_money(val: str) -> Optional[str]:
    if not val:
        return None
    s = str(val).strip().replace(",", "")
    m = re.search(r"£?\s*(\d+(?:\.\d+)?)", s)
    return m.group(1) if m else None


def _textify(html: str) -> str:
    # Very light "visible text" derivation
    txt = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    txt = re.sub(r"<style[\s\S]*?</style>", " ", txt, flags=re.I)
    txt = re.sub(r"<[^>]+>", "\n", txt)
    txt = re.sub(r"\n+", "\n", txt)
    return txt


# --------- Patterns known to exist on Zoopla property pages ---------
ZAD_PATTERN = re.compile(
    r'<script id="__ZAD_TARGETING__"[^>]*>(?P<json>{[\s\S]*?})</script>', re.I
)

LD_JSON_PATTERN = re.compile(
    r'<script[^>]+type="application/ld\+json"[^>]*>(?P<json>{[\s\S]*?})</script>', re.I
)

# --------- Field extractors from visible copy ---------


def _extract_status(text: str) -> Optional[str]:
    m = re.search(r"\b(Just added|Reduced|New listing)\b", text, flags=re.I)
    return m.group(1) if m else None


def _extract_photos_and_floorplans(text: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    m = re.search(r"(\d+)\s*Photos?", text, flags=re.I)
    if m:
        out["number_of_photos"] = m.group(1)
    m = re.search(r"(\d+)\s*Floor plan", text, flags=re.I)
    if m:
        out["number_of_floorplans"] = m.group(1)
    return out


def _extract_epc_rating(text: str) -> Optional[str]:
    m = re.search(r"\bEPC\s*Rating:\s*([A-G])\b", text, flags=re.I)
    return m.group(1).upper() if m else None


def _extract_address(text: str) -> Optional[str]:
    # pattern near header: "<price> ... <title> ... <address>"
    # Given your copy, look for "for sale\n<Address>"
    m = re.search(r"for sale\s*\n\s*([^\n]+)", text, flags=re.I)
    if m:
        return m.group(1).strip()
    # fallback to "display_address" in scripts handled elsewhere
    return None


def _extract_bed_bath_recepts(text: str) -> Dict[str, Any]:
    out = {}
    m = re.search(r"\b(\d+)\s*beds?\b", text, flags=re.I)
    if m:
        out["bedrooms"] = m.group(1)
    m = re.search(r"\b(\d+)\s*bath\b", text, flags=re.I)
    if m:
        out["bathrooms"] = m.group(1)
    m = re.search(r"\b(\d+)\s*receptions?\b", text, flags=re.I)
    if m:
        out["receptions"] = m.group(1)
    return out


def _extract_floor_area(text: str) -> Optional[int]:
    m = re.search(r"([\d,]{3,7})\s*sq\.\s*ft", text, flags=re.I)
    if m:
        return _coerce_int(m.group(1))
    return None


def _extract_price_per_sqft(text: str) -> Optional[int]:
    m = re.search(r"£\s*(\d+)\s*/\s*sq\.\s*ft", text, flags=re.I)
    if m:
        return _coerce_int(m.group(1))
    return None


def _extract_tenure(text: str) -> Optional[str]:
    m = re.search(r"\b(Freehold|Leasehold)\b", text, flags=re.I)
    return m.group(1).lower() if m else None


def _extract_agent(text: str) -> Optional[str]:
    m = re.search(r"Logo of\s+([A-Za-z &]+)", text)
    if m:
        return m.group(1).strip()
    # simple fallback
    m = re.search(r"\n\s*([A-Z][A-Za-z &]{2,})\s*\n\s*Logo", text)
    if m:
        return m.group(1).strip()
    return None


def _extract_council_and_ground(text: str) -> Dict[str, Any]:
    out = {}
    m = re.search(r"Council tax band\s*\n\s*([A-H])\b", text, flags=re.I)
    if m:
        out["council_tax_band"] = m.group(1).upper()
    m = re.search(r"Ground rent\s*\n?\s*£\s*([0-9,]+)", text, flags=re.I)
    if m:
        out["ground_rent"] = f"£{m.group(1)}"
    return out


def _extract_rooms(text: str) -> Dict[str, Any]:
    out = {}
    for name, w, h in re.findall(
        r"([A-Za-z ]+)\s*\((\d+\.\d+)m\s*x\s*(\d+\.\d+)m\)", text
    ):
        key = name.strip().lower().replace(" ", "_")
        out[f"room_{key}_m"] = f"{w}m x {h}m"
    return out


def _extract_nearest_stations(html: str) -> Dict[str, Any]:
    """Extract nearest stations from JSON data in the HTML"""
    out: Dict[str, Any] = {}

    # Extract nearest stations and distances from JSON patterns
    nearest_stations_patterns = [
        r'"nearestStations":\s*\[([^\]]+)\]',
        r'"nearestStations":\s*\["([^"]+)"(?:,\s*"([^"]+)")*\]',
    ]

    for pattern in nearest_stations_patterns:
        match = re.search(pattern, html)
        if match:
            # Extract station names from the array
            stations_text = match.group(1)
            # Clean up and split by comma, removing quotes
            stations = [
                s.strip().strip('"')
                for s in stations_text.split(",")
                if s.strip().strip('"')
            ]
            if stations:
                out["nearest_stations"] = ", ".join(stations)
            break

    # Extract nearest stations distances
    nearest_stations_distances_patterns = [
        r'"nearestStationsInMiles":\s*\[([^\]]+)\]',
        r'"nearestStationsInMiles":\s*\[([0-9.,\s]+)\]',
    ]

    for pattern in nearest_stations_distances_patterns:
        match = re.search(pattern, html)
        if match:
            # Extract distances from the array
            distances_text = match.group(1)
            # Clean up and split by comma, removing whitespace
            distances = [d.strip() for d in distances_text.split(",") if d.strip()]
            if distances:
                # Format distances to one decimal place
                formatted_distances = []
                for d in distances:
                    try:
                        distance = float(d)
                        formatted_distances.append(f"{distance:.1f}")
                    except ValueError:
                        formatted_distances.append(d)
                out["nearest_stations_distances"] = ", ".join(formatted_distances)
            break

    return out


def _extract_schools(html: str) -> Dict[str, Any]:
    """Extract nearest schools from JSON data in the HTML"""
    out: Dict[str, Any] = {}

    # Extract nearest schools from JSON patterns
    nearest_schools_patterns = [
        r'"nearestSchools":\s*\[([^\]]+)\]',
        r'"nearestSchools":\s*\["([^"]+)"(?:,\s*"([^"]+)")*\]',
    ]

    for pattern in nearest_schools_patterns:
        match = re.search(pattern, html)
        if match:
            # Extract school names from the array
            schools_text = match.group(1)
            # Clean up and split by comma, removing quotes
            schools = [
                s.strip().strip('"')
                for s in schools_text.split(",")
                if s.strip().strip('"')
            ]
            if schools:
                out["nearest_schools"] = ", ".join(schools)
            break

    # Try to extract schools from the description text as fallback
    if "nearest_schools" not in out:
        if "Good and Outstanding schools" in html:
            out["nearest_schools"] = "Good and Outstanding schools in the area"
        elif "local schools" in html:
            out["nearest_schools"] = "Local schools nearby"

    return out


def _extract_timeline(text: str) -> Dict[str, Any]:
    out = {}
    m = re.search(
        r"Listed\s*\n\s*([A-Za-z]+\s+\d{4})\s*\n\s*£\s*([\d,]+)", text, flags=re.I
    )
    if m:
        out["listed_date"] = m.group(1)
        out["listed_price"] = f"£{m.group(2)}"
    m = re.search(
        r"Sold\s*\n\s*([A-Za-z]+\s+\d{4})\s*\n\s*£\s*([\d,]+)", text, flags=re.I
    )
    if m:
        out["sold_date"] = m.group(1)
        out["sold_price"] = f"£{m.group(2)}"
    return out


def _extract_about_property(text: str) -> Dict[str, Any]:
    """
    Extract the full "About this property" text (bullets + paragraphs),
    preserving paragraph breaks, and stop before the next major section.
    """
    marker = "About this property"
    idx = text.find(marker)
    if idx == -1:
        return {}
    chunk = text[idx + len(marker) :]

    # Stop at next section marker
    stop_markers = [
        "Read full description",
        "Local area information",
        "Stations",
        "Schools",
        "Property timeline",
        "More information",
        "Report this listing",
    ]
    stop_pos = len(chunk)
    for m in stop_markers:
        p = chunk.find(m)
        if p != -1 and p < stop_pos:
            stop_pos = p
    chunk = chunk[:stop_pos]

    # Clean leading/trailing whitespace, compress excessive blank lines
    lines = [ln.rstrip() for ln in chunk.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    cleaned = []
    blank = False
    for ln in lines:
        if ln.strip():
            cleaned.append(ln)
            blank = False
        else:
            if not blank:
                cleaned.append("")
            blank = True
    about_text = "\n".join(cleaned).strip()

    return {"about_property": about_text} if about_text else {}


# --------- Main extraction ---------


def extract_from_html(html: str, visible_text: Optional[str] = None) -> Dict[str, Any]:
    """
    Consolidated field extractor for Zoopla listings.
    Uses Zoopla's embedded JSON where possible and enriches from visible text.
    Returns a flat dict. (Postcode intentionally not extracted.)
    """
    out: Dict[str, Any] = {}

    # 1) Base visible text
    txt = (
        visible_text
        if isinstance(visible_text, str) and visible_text.strip()
        else _textify(html)
    )

    # 2) Embedded Zoopla ad targeting JSON
    zad = ZAD_PATTERN.search(html or "")
    if zad:
        try:
            zad_json = json.loads(zad.group("json"))
            out.update(
                {
                    "listing_id": str(zad_json.get("listing_id") or ""),
                    "price": str(
                        zad_json.get("price_actual") or zad_json.get("price") or ""
                    ),
                    "property_type": (zad_json.get("property_type") or "").strip(),
                    "tenure": (zad_json.get("tenure") or "").strip().lower(),
                    "bedrooms": str(zad_json.get("num_beds") or ""),
                    "bathrooms": str(zad_json.get("num_baths") or ""),
                    "receptions": str(zad_json.get("num_recepts") or ""),
                    "has_epc": (
                        str(zad_json.get("has_epc")).capitalize()
                        if "has_epc" in zad_json
                        else ""
                    ),
                    "has_floorplan": (
                        str(zad_json.get("has_floorplan")).capitalize()
                        if "has_floorplan" in zad_json
                        else ""
                    ),
                    "size_sq_feet": str(zad_json.get("size_sq_feet") or ""),
                    "display_address": zad_json.get("display_address") or "",
                    "outcode": zad_json.get("outcode") or "",
                    "agent": zad_json.get("branch_name")
                    or zad_json.get("brand_name")
                    or "",
                    "chain_free": (
                        str(zad_json.get("chain_free")).capitalize()
                        if "chain_free" in zad_json
                        else ""
                    ),
                }
            )
        except Exception:
            pass

    # 3) LD+JSON (schema.org) block for offers/title
    ld = LD_JSON_PATTERN.search(html or "")
    if ld:
        try:
            data = json.loads(ld.group("json"))
            if isinstance(data, dict):
                if isinstance(data.get("offers"), dict) and data["offers"].get("price"):
                    out["price"] = str(data["offers"]["price"])
                if data.get("name"):
                    out["title"] = data["name"]
        except Exception:
            pass

    # 4) Enrich from visible text
    status = _extract_status(txt)
    if status:
        out["status"] = status

    out.update(_extract_photos_and_floorplans(txt))

    epc = _extract_epc_rating(txt)
    if epc:
        out["epc_rating"] = epc
        out.setdefault("has_epc", "True")

    addr = _extract_address(txt)
    if addr:
        out["address"] = addr

    out.update(_extract_bed_bath_recepts(txt))

    fa = _extract_floor_area(txt)
    if fa:
        out["size_sq_feet"] = str(fa)

    ppsf = _extract_price_per_sqft(txt)
    if ppsf is not None:
        out["price_per_sqft"] = str(ppsf)

    ten = _extract_tenure(txt)
    if ten:
        out["tenure"] = ten

    ag = _extract_agent(txt)
    if ag:
        out["agent"] = ag

    out.update(_extract_council_and_ground(txt))
    out.update(_extract_rooms(txt))
    out.update(_extract_nearest_stations(html))  # Pass HTML for JSON extraction
    out.update(_extract_schools(html))  # Pass HTML for JSON extraction
    out.update(_extract_timeline(txt))
    out.update(_extract_about_property(txt))

    # Final cleanup/normalisation
    if "price" in out:
        out["price"] = _norm_money(out["price"]) or out["price"]
    if "size_sq_feet" in out and isinstance(out["size_sq_feet"], str):
        out["size_sq_feet"] = out["size_sq_feet"].replace(",", "")

    # Prefer display_address for address when address missing
    if "address" not in out and out.get("display_address"):
        out["address"] = out["display_address"]

    # Remove empties
    return {k: v for k, v in out.items() if v not in (None, "", [], {})}


# --------- GraphQL API Functions for Points of Interest ---------


def fetch_points_of_interest_graphql(
    longitude: float, latitude: float, limit: int = 8
) -> Optional[Dict[str, Any]]:
    """
    Fetch points of interest from Zoopla GraphQL API using curl_cffi

    Args:
        longitude (float): Longitude coordinate
        latitude (float): Latitude coordinate
        limit (int): Maximum number of results to return

    Returns:
        dict: JSON response from the API or None if failed
    """

    url = "https://api-graphql-lambda.prod.zoopla.co.uk/graphql"

    headers = {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.9",
        "authorization": "Bearer eyJhbGciOiJQUzI1NiJ9.eyJzdWIiOiIwMTk4YmM5NWIyNTc3MWZhODg1NTBmZTI1NWRkNDU2YyIsInR5cGUiOiJhbm9uIiwicGxhdGZvcm0iOiJ3ZWIiLCJhbm9uX2lkIjoiZmRiYWRkYzU5Mjk3NDkyOWE5MmVlNmI4YWVlZjNlYjQiLCJhdWQiOlsid3d3Lnpvb3BsYS5jby51ayIsImdyYXBocWwuem9vcGxhLmNvLnVrIl0sImlzcyI6Ind3dy56b29wbGEuY28udWsiLCJpYXQiOjE3NTU1MTA1ODMsImV4cCI6MTc1NTUxMjM4M30.BOZUCquYb08xon5mkpYKMHriG-7Ke9GFNUc6on6O75y6TQlujspTNr14JDmV-5BdFnhaq3-tKRVUXph1T2gYqmMqM2_VJ5uFSL8LojVwpHXNE5-jTzMrlzuILPCZ3HM-waPub5o4cSYruLNPz0PF8NfEXMqHjcHNVuSuQyw4vc9dMaHEFLWFfRp6YiLeXbTZyVs6xkXd4ptamKKdmXWBlPfvRsXoFmCk_gnUjKJ4BTiFscGu13U1abCaDx9c2Oplxqdk2cYSyLEkGeN0tRrf65pbJGQFqD3jCnf0FB9KSl7LEokds0XOuHXRrWZoBejLaXh_BchYVdkmfaaAFdKXXg",
        "content-type": "application/json",
        "priority": "u=1, i",
        "sec-ch-ua": '"Chromium";v="139", "Not;A=Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "x-api-key": "public-1dH5DwBExsUKpdQGs6koWePJO7zeHyDb",
        "cookie": "zooplapsid=07e3e40059be43e6b0de6314b598a007; ajs_anonymous_id=fdbaddc592974929a92ee6b8aeef3eb4; active_session=anon; zooplasid=0198bc95b25771fa88550fe255dd456c; *cfuvid=IeF15KqJP4myWEH0YHHEyHdFkVw594DA8wvMCPXeXSE-1755510584048-0.0.1.1-604800000; *_cf_bm=1Am8B_J1uqLHB51WMc44WdyA8V.ThrwicAOh..f_xFc-1755511591-1.0.1.1-RgPhtk5MXU_1Hfxg3o92Q3DcJu3omKxnMnds.VNG.jkmS4dLB2sHDAPElaM5X9GjgF7NWIT302ceYKlHaj7kCJSDHn.ls_25tRgIIFuq25U; cf_clearance=hl8dm4HnDlAs4pchStohiTVXtD2j1C27g55xv7Oj4iU-1755511915-1.2.1.1-NpJOu5kXahdRujKujgg5MTptS8ej5_AqgTxa2kYnLbfCHsuxQZBVzEy1WwB_bgfozN0paLV4knHLfJMV_9qd38TmvopA9Ul948K3UmZAEmqMLtM39FHM0xNKeZhTbjiR3HsdX6oJAal3OGwOwpV7dhaZT0ALx4dAFCsi.G7rOa_YwIeFF5VHl.y_a3mvSTiJs85xU4RtLXbQ0.nBbXa1jYwp95skP8Q8oqDACrM19as",
        "Referer": "https://www.zoopla.co.uk/",
    }

    # GraphQL query payload
    payload = {
        "operationName": "pointsOfInterest",
        "variables": {"longitude": longitude, "latitude": latitude, "limit": limit},
        "query": """query pointsOfInterest($longitude:Float!$latitude:Float!$limit:Int) {
            pointsOfInterestV2(longitude:$longitude latitude:$latitude limit:$limit){
                ...schools 
                ...transports
            }
        }
        fragment schools on SchoolPointOfInterest{
            __typename 
            name 
            distanceMiles 
            ageLow 
            ageHigh 
            ofstedLastInspectionDate 
            ofstedRating
        }
        fragment transports on TransportPointOfInterest{
            __typename 
            distanceMiles 
            latitude 
            longitude 
            name 
            tubeLines 
            type 
            zone
        }""",
    }

    try:
        # Using curl_cffi with Chrome browser impersonation
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            impersonate="chrome120",  # Impersonate Chrome 120
            timeout=30,
        )
        response.raise_for_status()

        return response.json()

    except Exception as e:
        print(f"Error making GraphQL request: {e}")
        return None


def extract_stations_schools_from_graphql(
    graphql_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Extract stations and schools data from GraphQL API response

    Args:
        graphql_data (dict): Response from fetch_points_of_interest_graphql

    Returns:
        dict: Extracted stations and schools data
    """
    if not graphql_data or "data" not in graphql_data:
        return {}

    points = graphql_data["data"].get("pointsOfInterestV2", [])

    # Extract schools
    schools = [p for p in points if p.get("__typename") == "SchoolPointOfInterest"]
    school_names = []
    for school in schools:
        name = school.get("name", "")
        distance = school.get("distanceMiles", "")
        rating = school.get("ofstedRating", "")

        school_info = name
        if distance:
            # Format distance to one decimal place
            try:
                distance_float = float(distance)
                school_info += f" ({distance_float:.1f} miles)"
            except ValueError:
                school_info += f" ({distance} miles)"
        if rating:
            school_info += f" - {rating}"

        school_names.append(school_info)

    # Extract transport stations
    transports = [
        p for p in points if p.get("__typename") == "TransportPointOfInterest"
    ]
    station_names = []
    for transport in transports:
        name = transport.get("name", "")
        distance = transport.get("distanceMiles", "")
        transport_type = transport.get("type", "")

        station_info = name
        if transport_type:
            station_info += f" ({transport_type})"
        if distance:
            # Format distance to one decimal place
            try:
                distance_float = float(distance)
                station_info += f" ({distance_float:.1f} miles)"
            except ValueError:
                station_info += f" ({distance} miles)"

        station_names.append(station_info)

    result = {}

    if school_names:
        result["nearest_schools"] = ", ".join(school_names)

    if station_names:
        result["nearest_stations"] = ", ".join(station_names)

    return result
