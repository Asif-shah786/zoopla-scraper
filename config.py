"""
Configuration settings for Zoopla Scraper
==========================================

Modify these settings to customize the scraping behavior.
"""

# ===== SCRAPING LIMITS =====
MAX_PROPERTIES = 2  # Maximum number of properties to scrape (set to 2 for testing)
PAGES_TO_SCRAPE = 1  # Number of search result pages to process
REQUEST_DELAY = 5  # Seconds to wait between property requests (be respectful!)

# ===== SEARCH CONFIGURATION =====
SEARCH_LOCATION = "greater-manchester"  # Location to search for properties
SEARCH_BASE_URL = "https://www.zoopla.co.uk/for-sale/property/greater-manchester/"

# ===== TIMEOUTS =====
REQUEST_TIMEOUT = 20  # Seconds to wait for HTTP requests
PAGE_LOAD_TIMEOUT = 45  # Seconds to wait for page loading

# ===== OUTPUT SETTINGS =====
OUTPUT_FILE_PREFIX = "zoopla_bulk_properties"  # Prefix for output JSON files
SAVE_HTML_FILES = False  # Set to True to save raw HTML files for debugging
OUTPUT_DIRECTORY = "."  # Directory to save output files

# ===== DEBUGGING =====
VERBOSE_LOGGING = True  # Set to False to reduce console output
SHOW_PROGRESS = True  # Show detailed progress information
DEBUG_MODE = False  # Enable additional debugging features

# ===== BROWSER SIMULATION =====
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
IMPERSONATE_BROWSER = "chrome"  # Browser to impersonate for requests

# ===== RETRY SETTINGS =====
MAX_RETRIES = 3  # Maximum number of retry attempts for failed requests
RETRY_DELAY = 10  # Seconds to wait between retry attempts

# ===== FIELD EXTRACTION =====
EXTRACT_STATIONS = True  # Extract nearest train stations
EXTRACT_SCHOOLS = True  # Extract nearest schools
EXTRACT_ROOM_DIMENSIONS = True  # Extract detailed room measurements
EXTRACT_PROPERTY_DESCRIPTION = True  # Extract full property descriptions

# ===== RATE LIMITING =====
RESPECT_ROBOTS_TXT = True  # Respect website's robots.txt (recommended)
CONCURRENT_REQUESTS = 1  # Number of simultaneous requests (keep at 1 to be respectful)

# ===== DATA VALIDATION =====
VALIDATE_PROPERTY_IDS = True  # Validate property ID format
SKIP_DUPLICATE_PROPERTIES = True  # Skip properties already processed
MINIMUM_REQUIRED_FIELDS = ["property_id", "property_url", "price"]  # Required fields for valid properties

# ===== ADVANCED SETTINGS =====
# Note: Modify these only if you know what you're doing
ENABLE_LEGACY_EXTRACTION = True  # Use legacy patterns for stations/schools (recommended)
USE_WORKING_HEADERS = True  # Use authenticated headers for better data access (recommended)
EXTRACT_ADDITIONAL_METADATA = True  # Extract extra fields like timestamps, source info

# ===== EXPORT FORMATS =====
EXPORT_TO_JSON = True  # Export results to JSON format
EXPORT_TO_CSV = False  # Export results to CSV format (future feature)
PRETTY_PRINT_JSON = True  # Format JSON output for readability
