# Data Understanding, Analysis & Preprocessing

## Data Source and Collection

The real estate data pipeline was designed to collect comprehensive property information from Zoopla, a leading UK property portal. The data collection process involves web scraping of property listings, followed by integration with UK Police API for crime data enrichment. This multi-source approach ensures the RAG system has access to both property characteristics and contextual neighborhood safety information.

## Data Quality Assessment and Challenges

Initial data analysis revealed several quality issues that required systematic preprocessing:

1. **Missing Values**: Properties often had incomplete information, with critical fields like address, price, or description being null
2. **Data Type Inconsistencies**: Numeric fields appeared as both floats and integers across different scraping runs
3. **HTML Encoding**: Property descriptions contained HTML entities and formatting artifacts
4. **Coordinate Precision**: Latitude/longitude coordinates varied in precision and occasionally contained invalid values

## Preprocessing Pipeline Design

The preprocessing pipeline was designed with a systematic approach to address these challenges:

### Step 1: Data Loading and Column Selection
- Implemented intelligent column filtering to retain only relevant fields for RAG applications
- Applied field mapping for consistency (e.g., `outcode` → `postcode`, `latitude` → `lat`)

### Step 2: Missing Value Handling
- Applied mode-based imputation for categorical variables (property_type, council_tax_band, tenure)
- Preserved null values for optional fields while ensuring essential data completeness

### Step 3: Data Type Standardization
- Converted numeric fields to appropriate types (Int64 for discrete values, float64 for continuous)
- Created integer helper columns (`bedrooms_int`, `bathrooms_int`, `receptions_int`) for efficient vector DB filtering

### Step 4: Text Data Cleaning
- Implemented regex-based cleaning for HTML entities and excessive whitespace
- Applied consistent text normalization across all string fields

### Step 5: Price Data Consolidation
- Consolidated multiple price representations into a single `price_int` field
- Ensured integer-only pricing for efficient range queries in vector databases
- Removed redundant price columns to maintain data consistency

### Step 6: Quality Filtering
- Implemented essential field validation to exclude incomplete properties
- Applied strict filtering criteria: properties missing address, price_int, or description were excluded
- This filtering step ensures only high-quality, complete property records reach the RAG system

## Integration with External Data Sources

The preprocessing pipeline is designed to accommodate enriched data from external APIs. After initial cleaning and quality filtering, the system integrates crime data from the UK Police API to provide neighborhood safety context. This enrichment step occurs after quality filtering, ensuring only complete properties receive additional contextual information.

**Note**: The detailed implementation of crime data integration is covered in Section 5 (Implementation/Modelling) as it represents a system enhancement rather than core data preprocessing.

## Data Validation and Quality Metrics

The preprocessing pipeline includes comprehensive validation:
- **Completeness Check**: Tracks and reports missing value percentages
- **Data Type Verification**: Ensures consistent typing across all fields
- **Filtering Statistics**: Reports the number of properties removed due to incompleteness
- **Output Validation**: Confirms final dataset meets quality thresholds

## Integration with RAG Pipeline

The cleaned data is structured to optimize RAG system performance:
- **Searchable Fields**: Address, description, and title are cleaned for optimal text embedding
- **Filterable Metadata**: Integer fields (price_int, bedrooms_int) enable efficient metadata filtering
- **Crime Context**: Integrated crime data provides neighborhood safety context for property recommendations

## Data Pipeline Reliability

The preprocessing pipeline demonstrates robustness through:
- **Error Handling**: Graceful handling of malformed data and API failures
- **Logging**: Comprehensive logging of all preprocessing steps and decisions
- **Reproducibility**: Consistent output across multiple pipeline runs
- **Scalability**: Designed to handle varying data volumes from different scraping sessions

## Diagram Prompts for ChatGPT Image Generator

### 1. Data Pipeline Flow Diagram
**Prompt**: "Create a professional flowchart diagram showing a real estate data pipeline with the following components connected by arrows: 1) Web Scraping (Zoopla) → 2) Crime Data Integration (UK Police API) → 3) Data Preprocessing (Cleaning & Validation) → 4) Quality Filtering → 5) RAG System Input. Use blue boxes for data sources, green boxes for processing steps, and orange boxes for output. Include small icons for each step and make it look like a technical architecture diagram."

### 2. Data Preprocessing Steps Diagram
**Prompt**: "Create a step-by-step diagram showing data preprocessing workflow: Step 1: Data Loading (file icon), Step 2: Column Selection (filter icon), Step 3: Missing Value Handling (question mark icon), Step 4: Data Type Conversion (gear icon), Step 5: Text Cleaning (brush icon), Step 6: Price Consolidation (money icon), Step 7: Quality Filtering (checkmark icon), Step 8: Save Output (save icon). Use numbered circles for steps, icons for each step, and arrows connecting them. Make it look like a professional technical workflow diagram with a clean, modern design."

### 3. Data Quality Metrics Dashboard
**Prompt**: "Create a dashboard-style diagram showing data quality metrics: Missing Values Chart (bar chart showing percentages), Data Type Distribution (pie chart), Filtering Results (before/after comparison), and Quality Score (gauge meter). Use a modern dashboard layout with charts, graphs, and metrics displayed in organized sections. Make it look like a professional analytics dashboard with clean typography and color-coded elements."

### 4. RAG System Integration Diagram
**Prompt**: "Create a system architecture diagram showing how the preprocessed real estate data flows into a RAG system: Data Input → Vector Database → Embedding Engine → Query Processing → Response Generation. Show the data structure with sample fields (address, price_int, description, crime_data) and how they're used in the RAG pipeline. Use a modern technical diagram style with clear components, data flow arrows, and sample data structures."

## Integration with Main Project Report

### **Section 4: Data Understanding, Analysis & Preprocessing** (10% weight)
Place this section after your Methodology section and before Implementation/Modelling. This positioning makes sense because:

1. **Logical Flow**: Methodology → Data Understanding → Implementation
2. **Foundation for Modelling**: The RAG system implementation builds directly on this preprocessed data
3. **Quality Assurance**: Demonstrates data quality before moving to system implementation

### **Cross-References in Other Sections:**
- **Introduction**: Mention the data pipeline as a key component
- **Methodology**: Reference the preprocessing approach
- **Implementation**: Show how clean data enables RAG system functionality
- **Results Analysis**: Demonstrate how data quality impacts system performance
- **Conclusions**: Reflect on data pipeline improvements

### **Integration Points:**
- **Abstract**: Brief mention of "comprehensive data preprocessing pipeline"
- **Objectives**: Include data quality goals
- **Background**: Reference real estate data challenges
- **Critical Evaluation**: Assess preprocessing effectiveness

This approach ensures your data pipeline work is properly recognized within the broader RAG system evaluation while maintaining the academic structure expected in your dissertation.
