# Zoopla Property Scraper

A comprehensive Python scraper for extracting property data from Zoopla.co.uk with support for both single property and bulk scraping.

## 🚀 Features

- **Single Property Scraping**: Extract detailed information from individual property URLs
- **Bulk Property Scraping**: Scrape multiple properties from search results
- **Comprehensive Data Extraction**: 39+ fields including price, bedrooms, bathrooms, room dimensions, EPC ratings, and more
- **Transport Data**: Extracts nearest train stations with distances
- **Configurable Settings**: Easy-to-modify configuration file
- **Clean Data Output**: Well-structured JSON output with all metadata

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Asif-shah786/zoopla-scraper.git
   cd zoopla-scraper
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## 🔧 Configuration

All scraping settings can be customized in `config.py`:

### Key Settings:
```python
MAX_PROPERTIES = 2         # Number of properties to scrape
PAGES_TO_SCRAPE = 1        # Search result pages to process
REQUEST_DELAY = 5          # Seconds between requests
SEARCH_LOCATION = "greater-manchester"  # Location to search
```

### Advanced Settings:
- **Timeouts**: Request and page load timeouts
- **Output**: File naming and directory settings
- **Export Formats**: Enable/disable JSON and CSV exports
- **Debugging**: Verbose logging and debug modes
- **Data Extraction**: Enable/disable specific fields
- **Rate Limiting**: Respectful scraping settings

## 🎯 Usage

### Bulk Scraping (Recommended)
```bash
python zoopla_bulk_scraper.py
```

**Features:**
- Scrapes multiple properties automatically
- Uses complete `zoopla.py` extraction + enhanced transport data
- Configurable via `config.py`
- Outputs timestamped JSON files

### Single Property Scraping
```bash
python zoopla.py --url "https://www.zoopla.co.uk/for-sale/details/PROPERTY_ID/" --out output.json
```

**Options:**
- `--url`: Property URL (required)
- `--property-id`: Property ID (optional)
- `--save-html`: Save raw HTML file (optional)
- `--out`: Output JSON file (optional, prints to stdout if omitted)

## 📊 Output Data

### Output Formats:
- **JSON**: Structured data with full field details (default)
- **CSV**: Spreadsheet-friendly format for analysis and reporting

### Extracted Fields:
- **Basic Info**: Price, property type, bedrooms, bathrooms, receptions
- **Location**: Address, postcode, council tax band
- **Property Details**: Size (sq ft), EPC rating, tenure, agent
- **Room Dimensions**: Detailed measurements for all rooms
- **Transport**: Nearest train stations with distances
- **Description**: Complete property description
- **Metadata**: Scraping timestamp, source URL, property ID

### Sample Output:
```json
{
  "property_id": "71073577",
  "price": "220000",
  "property_type": "terraced",
  "bedrooms": "3",
  "bathrooms": "1",
  "address": "New Barton Street, Salford M6",
  "size_sq_feet": "1044",
  "epc_rating": "D",
  "nearest_stations": "Eccles (Manchester), Swinton (Manchester), Clifton (Manchester)...",
  "nearest_stations_distances": "1.4, 1.5, 1.5, 1.8, 2, 2.2...",
  "room_lounge_m": "4.45m x 3.73m",
  "scraped_at": "2025-08-16T16:15:45.123456"
}
```

## ⚙️ How It Works

### Bulk Scraper Process:
1. **Search Results**: Extracts property URLs from Zoopla search pages
2. **Complete Extraction**: Uses `zoopla.py` for comprehensive property data
3. **Transport Data**: Uses specialized patterns with working headers for stations/schools
4. **Data Merge**: Combines both extractions for complete property records
5. **Output**: Saves all data to timestamped JSON file

### Key Components:
- **`zoopla_bulk_scraper.py`**: Main bulk scraping orchestrator
- **`zoopla.py`**: Single property scraper with clean extraction
- **`fields_extractor.py`**: Core field extraction logic
- **`config.py`**: Configuration settings

## 🛡️ Respectful Scraping

This scraper is designed to be respectful:
- **Rate limiting**: Configurable delays between requests
- **Single threading**: One request at a time
- **Proper headers**: Browser-like requests
- **Error handling**: Graceful failure handling
- **Configurable limits**: Easy to set reasonable limits

## 📁 Files

- `zoopla_bulk_scraper.py` - Bulk property scraper
- `zoopla.py` - Single property scraper
- `fields_extractor.py` - Field extraction logic
- `config.py` - Configuration settings
- `requirements.txt` - Python dependencies
- `.gitignore` - Git ignore rules

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the scraper.

## ⚠️ Legal Notice

This tool is for educational and research purposes. Please respect Zoopla's terms of service and robots.txt. Use responsibly and consider the website's resources.

## 📝 License

This project is open source. Please use responsibly.
