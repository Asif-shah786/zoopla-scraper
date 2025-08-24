## Real Estate Data Pipeline for Zoopla (Scrape → Crime → Clean)

A production-friendly data pipeline that scrapes properties from Zoopla, enriches them with UK Police crime data, and outputs a clean, RAG-ready dataset.

### What this pipeline does
- Scrapes Zoopla properties with rich details (price, beds, EPC, description, agent, transport, etc.)
- Fetches 6-month crime data around each property coordinate (UK Police API)
- Embeds a human-readable crime summary and raw crime aggregates
- Cleans and normalizes fields for downstream AI/RAG applications
- Stores all artifacts, logs, and summaries in uniquely numbered run folders

---

## Quick start

### 1) Install

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure
Edit `config.py` to control scraping behavior:

- **MAX_PROPERTIES**: number of properties to process per run
- **PAGES_TO_SCRAPE**: how many search result pages to scan
- **REQUEST_DELAY**: seconds between fetches
- **SEARCH_LOCATION**: e.g., "greater-manchester"
- **EXPORT_TO_JSON/CSV**: output formats

Example snippet:
```python
MAX_PROPERTIES = 5
PAGES_TO_SCRAPE = 1
REQUEST_DELAY = 2
SEARCH_LOCATION = "greater-manchester"
EXPORT_TO_JSON = True
EXPORT_TO_CSV = False
```

### 3) Run the complete pipeline

```bash
python real_estate_data_pipeline.py
```

- Creates a new run folder: `runs/run_X/`
- Steps: scraping → crime data → preprocessing
- Produces final file: `runs/run_X/run_ready.json`

You can run it again any time. Each run is isolated and doesn’t overwrite previous runs.

---

## Project layout (key files)

- `real_estate_data_pipeline.py`: Orchestrates the pipeline end-to-end
- `zoopla_bulk_scraper.py`: Bulk Zoopla scraper (generates raw JSON)
- `uk_police_api.py`: Crime aggregation and summary builder
- `data_preprocessing.py`: Cleans, maps, and normalizes the combined data
- `config.py`: Scraper configuration
- `runs/`: All run artifacts live here (per-run folders)

---

## How the pipeline works

### Step 1: Scrape
- Executes `zoopla_bulk_scraper.py`
- Produces a timestamped JSON file in project root (the most recent `*.json` is assumed to be the scrape output)
- The pipeline copies that file to the run folder as `scraped_data.json`

Typical scraped fields include:
- Core: `property_id`, `property_url`, `price`, `property_type`, `tenure`, `bedrooms`, `bathrooms`, `receptions`, `status`, `chain_free`, `has_epc`
- Location: `address`, `outcode` (postcode outward code)
- Extras: `epc_rating`, `nearest_stations`, `nearest_schools`, `agent`
- Coordinates: `latitude`, `longitude`
- Description: `about_property`

### Step 2: Crime data
- Dynamically loads `uk_police_api.py`
- Temporarily overrides `load_properties()` so it reads from the run’s `scraped_data.json`
- Calls `run_property_crime_summaries(max_items=...)`
- Writes crime summaries to `property_crime_summaries.json` (project root)
- Merges crime data back into `scraped_data.json` → saves as `runs/run_X/properties_with_crime.json`

Crime data added per property:
- `crime_summary`: human-readable summary (traffic-light level)
- `crime_data`: raw aggregates with keys like `total`, `by_category`, `top_streets`, `outcomes`, `monthly_counts`, `trend`

Console output is intentionally minimal during crime ingestion:
- Example: `✅ Ingested crime data for property 3`

### Step 3: Preprocess
- Loads `runs/run_X/properties_with_crime.json`
- Selects/masks columns, maps names, handles types, cleans text
- Writes cleaned outputs into the run folder:
  - `properties_with_crime_cleaned.json`
  - `properties_with_crime_cleaned.csv`
  - Also copies the JSON as `run_ready.json` (canonical output)

---

## Run folder contents

Each run folder contains:

- `scraped_data.json`: raw scraped properties
- `properties_with_crime.json`: scraped data enriched with crime fields
- `properties_with_crime_cleaned.json`: preprocessed data
- `properties_with_crime_cleaned.csv`: CSV variant
- `run_ready.json`: the final RAG-ready JSON
- `run_log.txt`: step-by-step logs with timestamps
- `run_summary.json`: overall timing and statuses

Example:
```text
runs/
  run_4/
    scraped_data.json
    properties_with_crime.json
    properties_with_crime_cleaned.json
    properties_with_crime_cleaned.csv
    run_ready.json
    run_log.txt
    run_summary.json
```

---

## Output schemas

### A) Raw scraped (`scraped_data.json`)
- Provided by `zoopla_bulk_scraper.py`
- Common keys:
  - `property_id` (str)
  - `property_url` (str)
  - `price` (str)
  - `property_type` (str)
  - `tenure` (str)
  - `bedrooms`, `bathrooms`, `receptions` (str)
  - `status`, `chain_free`, `has_epc` (str)
  - `address` (str), `outcode` (str)
  - `epc_rating` (str|null)
  - `nearest_stations`, `nearest_schools` (str)
  - `agent` (str)
  - `latitude` (float), `longitude` (float)
  - `about_property` (str)

### B) Enriched (`properties_with_crime.json`)
- Same as raw, plus:
  - `crime_summary` (str)
  - `crime_data` (object)

`crime_data` structure example:
```json
{
  "total": 9,
  "by_category": {"violent-crime": 7, "other-theft": 1, "theft-from-the-person": 1},
  "top_streets": {"On or near Wood Street": 3, "On or near Southall Street": 1},
  "outcomes": {"Under investigation": 6, "Investigation complete; no suspect identified": 3},
  "monthly_counts": {"2025-08": 0, "2025-07": 0, "2025-06": 2, "2025-05": 4, "2025-04": 1, "2025-03": 2},
  "trend": "falling"
}
```

### C) Final (`run_ready.json`)
- Cleaned, mapped, and typed fields for RAG. Includes, for example:
  - `title` (from scraped `title`)
  - `address` (from scraped `address`)
  - `postcode` (mapped from `outcode`)
  - `lat` (from `latitude`)
  - `lng` (from `longitude`)
  - `price` (numeric)
  - `property_type`, `tenure`
  - `bedrooms`, `bathrooms`, `receptions` (ints)
  - `property_id` (int), `property_url`
  - `council_tax_band`, `epc_rating`
  - `nearest_stations`, `nearest_schools`
  - `agent_name` (mapped from `agent`)
  - `chain_free`, `status`
  - `number_of_photos`, `number_of_floorplans`
  - `ground_rent`
  - `description` (mapped from `about_property`)
  - Helper numerics: `bedrooms_int`, `bathrooms_int`, `receptions_int`, `price_num`
  - Crime fields: `crime_summary`, `crime_data`

Note on `size_sqft`: this field may not be present in scraped data for many listings, so it may be `null` or omitted depending on availability.

---

## Field mapping and cleaning

The preprocessing step (`data_preprocessing.py`) performs the following:

- Column selection (keeps only relevant fields for RAG)
- Name mapping:
  - `outcode` → `postcode`
  - `latitude` → `lat`
  - `longitude` → `lng`
  - `agent` → `agent_name`
  - `about_property` → `description`
- Text cleaning on human-readable fields: `description`, `address`, `title`, `agent_name`, `nearest_stations`, `nearest_schools`, `epc_rating`, `council_tax_band`
- Numeric coercion: `bedrooms`, `bathrooms`, `price`, `receptions`, `size_sqft` (if present)
- Helper numeric columns: `bedrooms_int`, `bathrooms_int`, `receptions_int`, `price_num`
- URLs like `property_url` are left untouched

---

## Logs and summaries

- Console logs mirror to `runs/run_X/run_log.txt`
- Summary saved to `runs/run_X/run_summary.json` with per-step status and timings

Example summary:
```json
{
  "run_number": 4,
  "start_time": "2025-08-18T19:46:57.123Z",
  "end_time": "2025-08-18T19:47:30.456Z",
  "total_duration_seconds": 33.3,
  "run_directory": "runs/run_4",
  "steps": {
    "scraping": {"status": "completed", "start": "...", "end": "...", "error": null},
    "crime_data": {"status": "completed", "start": "...", "end": "...", "error": null},
    "preprocessing": {"status": "completed", "start": "...", "end": "...", "error": null}
  },
  "overall_status": "completed"
}
```

---

## Troubleshooting

- **Pipeline fails at crime step: "Crime summaries file not generated"**
  - Ensure `uk_police_api.py` writes `property_crime_summaries.json` to the project root (the pipeline now expects it there)
  - Network issues can cause UK Police API to return no data; re-run

- **Preprocessing error: indentation**
  - If you modified `data_preprocessing.py`, ensure consistent spaces indentation

- **Missing fields in `run_ready.json`**
  - Scraped data varies by listing. Some fields (e.g., `size_sqft`) may be unavailable
  - Ensure the field is included in the `columns_to_keep` list and mapped if needed
  - We already map `agent` → `agent_name` and `about_property` → `description`

- **Wrong file detected as scraper output**
  - The pipeline copies the most recent `*.json` in project root after scraping. Avoid leaving unrelated JSONs in the root during a run

- **Rate limiting or slow runs**
  - Increase `REQUEST_DELAY` in `config.py`

---

## Customization tips

- Limit total properties via `config.MAX_PROPERTIES`
- Change search scope via `config.SEARCH_LOCATION`
- Adjust crime lookback (months) in `uk_police_api.py` by changing `generate_recent_months(6)`
- To silence console output further, reduce prints in modules; the pipeline logs key milestones already

---

## Legal and usage notes

- Respect Zoopla’s terms of service and robots.txt
- UK Police API is public, but please use responsibly
- This project is for educational/research purposes

---

## License

Open source. Use responsibly.
