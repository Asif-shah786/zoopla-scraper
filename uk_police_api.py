import requests
import datetime
import time
from collections import Counter


def generate_recent_months(num_months: int) -> list[str]:
    months: list[str] = []
    today = datetime.date.today().replace(day=1)
    for i in range(num_months):
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1
        months.append(f"{year:04d}-{month:02d}")
    return months


def fetch_month_crimes(lat: float, lng: float, year_month: str) -> list[dict]:
    url = f"https://data.police.uk/api/crimes-street/all-crime?lat={lat}&lng={lng}&date={year_month}"
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return resp.json() or []
    except Exception:
        return []


def aggregate_6month_crime(lat: float, lng: float) -> dict:
    months = generate_recent_months(6)
    all_crimes: list[dict] = []
    monthly_counts: dict[str, int] = {}
    for ym in months:
        crimes = fetch_month_crimes(lat, lng, ym)
        monthly_counts[ym] = len(crimes)
        all_crimes.extend(crimes)
        time.sleep(0.25)

    category_counts: Counter[str] = Counter(
        c.get("category", "unknown") for c in all_crimes
    )
    street_names = [
        (c.get("location", {}) or {}).get("street", {}).get("name", "Unknown")
        for c in all_crimes
    ]
    street_counts: Counter[str] = Counter(street_names)
    outcomes = [
        (c.get("outcome_status") or {}).get("category", "Not provided")
        for c in all_crimes
    ]
    outcome_counts: Counter[str] = Counter(outcomes)

    sorted_months = sorted(monthly_counts.keys())
    last3 = (
        sum(monthly_counts[m] for m in sorted_months[-3:])
        if len(sorted_months) >= 3
        else 0
    )
    prev3 = (
        sum(monthly_counts[m] for m in sorted_months[-6:-3])
        if len(sorted_months) >= 6
        else 0
    )
    trend = "stable"
    if prev3 > 0:
        change = (last3 - prev3) / prev3
        if change > 0.15:
            trend = "rising"
        elif change < -0.15:
            trend = "falling"

    return {
        "total": len(all_crimes),
        "by_category": dict(category_counts.most_common()),
        "top_streets": dict(street_counts.most_common(3)),
        "outcomes": dict(outcome_counts.most_common()),
        "monthly_counts": monthly_counts,
        "trend": trend,
    }


def prettify_category(cat: str) -> str:
    return cat.replace("-", " ").title()


def build_accurate_summary(
    address: str, postcode: str | None, agg: dict, radius_km: float = 1.0
) -> str:
    total = agg.get("total", 0)
    trend = agg.get("trend", "stable")
    cats = list(agg.get("by_category", {}).keys())
    top_two = (
        ", ".join(prettify_category(c) for c in cats[:2])
        if cats
        else "No major categories"
    )
    pc = f" ({postcode})" if postcode else ""

    # Get actual crime locations for context
    top_streets = list(agg.get("top_streets", {}).keys())[:2]
    if top_streets and total > 0:
        street_context = f" (near {', '.join(top_streets)})"
    else:
        street_context = ""

    # Traffic light system for quick understanding
    if total == 0:
        return f"🟢 {address}{pc}: Safe area - no crimes reported within {radius_km}km radius in past 6 months"
    elif total <= 5:
        return f"🟢 {address}{pc}: Low crime - {total} incidents within {radius_km}km radius{street_context}, mainly {top_two} ({trend} trend)"
    elif total <= 20:
        return f"🟡 {address}{pc}: Moderate crime - {total} incidents within {radius_km}km radius{street_context}, mainly {top_two} ({trend} trend)"
    else:
        return f"🔴 {address}{pc}: High crime area - {total} incidents within {radius_km}km radius{street_context}, mainly {top_two} ({trend} trend)"


def load_properties(max_items: int = 10) -> list[dict]:
    props: list[dict] = []
    try:
        import json

        # Use the new JSON file
        path = "18-august-12pm_page1-ALL_property1-10_cleaned.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Extract only essential fields needed for crime data lookup
        for p in data[:max_items]:
            lat = p.get("lat")
            lng = p.get("lon")

            # Skip properties with missing coordinates
            if lat is None or lng is None or lat == 0 or lng == 0:
                continue

            props.append(
                {
                    "title": p.get("listing_title") or "",
                    "address": p.get("address_full") or "",
                    "postcode": p.get("outcode"),
                    "lat": float(lat) if lat is not None else 0.0,
                    "lng": float(lng) if lng is not None else 0.0,
                }
            )
        return props
    except Exception as e:
        print(f"Error loading properties: {e}")
        # Fallback to previously generated sample JSON
        try:
            with open("data/simple_properties_sample.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            for p in data.get("properties", [])[:max_items]:
                loc = p.get("location") or {}
                lat = loc.get("latitude")
                lng = loc.get("longitude")

                # Skip properties with missing coordinates
                if lat is None or lng is None:
                    continue

                props.append(
                    {
                        "title": p.get("title") or "",
                        "address": p.get("address") or "",
                        "postcode": loc.get("postcode"),
                        "lat": float(lat),
                        "lng": float(lng),
                    }
                )
            return props
        except Exception as fallback_error:
            print(f"Fallback also failed: {fallback_error}")
            return []


def run_property_crime_summaries(max_items: int = 10) -> None:
    properties = load_properties(max_items=max_items)
    print(f"Generating 6-month crime summaries for {len(properties)} properties...\n")

    results: list[dict] = []
    for idx, prop in enumerate(properties, start=1):
        lat = prop.get("lat")
        lng = prop.get("lng")
        address = prop.get("address") or prop.get("title") or "This property"
        postcode = prop.get("postcode")

        if lat is None or lng is None:
            print(f"{idx}. Skipping (no coordinates): {address}")
            continue

        print(f"{idx}. Processing: {address}")
        agg = aggregate_6month_crime(lat, lng)
        summary = build_accurate_summary(address, postcode, agg)

        # Just show simple progress - no crime details
        print(f"   ✅ Ingested crime data for property {idx}")

        # Create enhanced property object with crime data
        enhanced_property = {
            # Original property data
            **prop,
            # Crime data
            "crime_summary": summary,
            "crime_data": agg,
        }

        results.append(enhanced_property)

    # Save enhanced properties with crime data
    try:
        import json

        # Save crime summaries for quick reference - use current directory
        crime_summaries_path = "property_crime_summaries.json"
        crime_summaries = [
            {
                "address": r.get("address"),
                "postcode": r.get("postcode"),
                "lat": r.get("lat"),
                "lng": r.get("lng"),
                "summary": r.get("crime_summary"),
                "aggregate": r.get("crime_data"),
            }
            for r in results
        ]

        with open(crime_summaries_path, "w", encoding="utf-8") as f:
            json.dump(crime_summaries, f, indent=2, ensure_ascii=False)
        print(f"Saved crime summaries to: {crime_summaries_path}")

    except Exception as e:
        print(f"Error saving files: {e}")


if __name__ == "__main__":
    run_property_crime_summaries(max_items=10)
