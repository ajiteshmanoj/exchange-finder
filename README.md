# NTU Exchange University Scraper

A Python web scraper to find suitable exchange universities for DSAI Y3 Semester 1 (AY2025-26) based on module mappings and availability.

## Features

- **PDF Extraction**: Automatically extracts university data from NTU GEM Explorer vacancy list
- **Module Mapping Search**: Scrapes NTU INSTEP system for approved module mappings
- **Smart Filtering**: Filters universities by country, college acceptance, and semester availability
- **Automatic Grouping**: Combines university variations (multiple campuses) automatically
- **Comprehensive Analysis**: Ranks universities by multiple criteria
- **Dual Output**: Generates both CSV and Markdown reports

## Project Structure

```
Exchange_Scraper/
├── config/
│   ├── config.yaml              # Main configuration
│   ├── credentials.enc          # Encrypted credentials (auto-generated)
│   └── .key                     # Encryption key (auto-generated)
├── scrapers/
│   ├── pdf_extractor.py         # PDF parsing logic
│   ├── ntu_mapper.py            # Module mapping scraper
│   └── session_manager.py       # NTU SSO authentication
├── processors/
│   ├── data_cleaner.py          # Data normalization
│   ├── matcher.py               # Combine data sources
│   ├── ranker.py                # Ranking logic
│   └── output_generator.py      # CSV and Markdown generation
├── utils/
│   └── crypto.py                # Credential encryption
├── outputs/                      # Generated reports (auto-created)
├── main.py                       # Main orchestrator
└── requirements.txt              # Python dependencies
```

## Installation

### 1. Clone or navigate to the project directory

```bash
cd /Users/ajitesh/Desktop/My_Projects/Exchange_Scraper
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### Target Settings

Edit `config/config.yaml` to customize:

- **Target Countries**: Countries to search for universities
- **Target Modules**: Module codes to search for mappings
- **Minimum Mappable Modules**: Minimum number of modules that must have mappings (default: 2)
- **Rate Limiting**: Delay between web requests (default: 2-3 seconds)

Current configuration:
- **Countries**: Australia, Denmark, Finland, Ireland, Netherlands, Norway, Sweden
- **Modules**: SC4001, SC4002, SC4062, SC4021, SC4023, SC4003
- **College**: CCDS
- **Semester**: Sem 1 (AY 25/26)

## Usage

### First Time Setup

Run credential setup to store your NTU login credentials securely:

```bash
python main.py --setup
```

You'll be prompted to enter:
- Network Username (e.g., AJITESH001)
- Password
- Domain (e.g., Student)

Credentials are encrypted using Fernet symmetric encryption and stored in `config/credentials.enc`.

### Run the Scraper

```bash
python main.py
```

The scraper will:
1. ✅ Extract universities from PDF (~ 1-2 minutes)
2. ✅ Login to NTU module mapping system
3. ✅ Search module mappings for all universities (~ 10-20 minutes)
4. ✅ Process and rank results
5. ✅ Generate CSV and Markdown reports

### Command Line Options

```bash
# Use default configuration
python main.py

# Specify custom config file
python main.py --config path/to/config.yaml

# Update stored credentials
python main.py --setup
```

## Output

### CSV Report: `outputs/exchange_universities_analysis.csv`

Contains all universities with detailed module mapping information:
- Rank
- University Name, Country, Code
- Sem 1 Spots, Min CGPA
- Mappable Modules Count, Coverage %
- Individual module mappings (SC4001, SC4002, etc.)
- Unmappable modules
- Remarks

### Markdown Report: `outputs/exchange_universities_report.md`

Comprehensive report with:
- Summary statistics
- Breakdown by country
- Top 15 universities overall
- Detailed results grouped by country
- Module mapping details for each university

## Understanding the Results

### Ranking Criteria

Universities are ranked by (in order):
1. **Country** (alphabetical)
2. **Mappable Modules** (descending - more is better)
3. **Sem 1 Spots** (descending - more is better)
4. **Min CGPA** (ascending - lower requirement is better)

### Filtering

Only universities that meet ALL criteria are included:
- ✅ Located in target countries
- ✅ Accept CCDS students
- ✅ Have Sem 1 spots available (> 0)
- ✅ Have at least 2 mappable modules (configurable)

### Module Mappings

For each module:
- **✅ Can Map**: Shows approved partner modules with codes and names
- **❌ Cannot Map**: No approved mapping found for 2024/2025

## Expected Results

Based on test run:
- **Total universities found**: 45 (from 405 in PDF)
- **Countries**: 7
- **Breakdown**:
  - Australia: 16 universities
  - Sweden: 12 universities
  - Netherlands: 5 universities
  - Ireland: 4 universities
  - Denmark: 3 universities
  - Finland: 3 universities
  - Norway: 2 universities

## Runtime

- **PDF Extraction**: ~ 1-2 minutes
- **Module Mapping Scraping**: ~ 10-20 minutes (45 universities × 6 modules × 2.5s delay)
- **Processing**: < 1 minute
- **Total**: ~ 15-25 minutes

## Rate Limiting

The scraper implements respectful rate limiting:
- Random delay between 2-3 seconds between requests
- Prevents overwhelming NTU servers
- Reduces risk of being blocked

## Troubleshooting

### Login Failed

If login fails:
1. Check your credentials are correct
2. Verify you can login manually to NTU SSO
3. Delete `config/credentials.enc` and run `python main.py --setup` again

### PDF Parsing Errors

If PDF extraction fails:
1. Verify PDF file exists: `210125_GEM_Explorer_Vacancy_List_for_AY2526_Full_Year_Recruitment.pdf`
2. Check PDF path in `config/config.yaml`
3. Ensure PDF is not corrupted

### Module Not Found Errors

If you get import errors:
1. Ensure you've installed dependencies: `pip install -r requirements.txt`
2. Run from project root directory
3. Check Python version (requires Python 3.7+)

### No Universities Found

If no universities match criteria:
1. Check target countries in `config/config.yaml`
2. Lower `min_mappable_modules` (try 1 instead of 2)
3. Verify PDF has data for target countries

## Security Notes

- Credentials are encrypted using Fernet (symmetric encryption)
- Encryption key stored separately in `config/.key`
- Both files have restricted permissions (0o600)
- **Never commit** `.key` or `credentials.enc` to version control

Add to `.gitignore`:
```
config/credentials.enc
config/.key
outputs/
```

## Customization

### Change Target Countries

Edit `config/config.yaml`:
```yaml
target_countries:
  - United States
  - United Kingdom
  - Canada
```

### Change Target Modules

Edit `config/config.yaml`:
```yaml
target_modules:
  - SC4001
  - SC4002
  - SC4020
```

### Adjust Rate Limiting

Edit `config/config.yaml`:
```yaml
rate_limiting:
  delay_min: 3.0  # Increase for slower scraping
  delay_max: 5.0
```

## Technical Details

### Dependencies

- **pdfplumber**: PDF table extraction
- **requests + BeautifulSoup**: Web scraping
- **pandas**: Data processing
- **cryptography**: Credential encryption
- **tqdm**: Progress bars
- **PyYAML**: Configuration management

### Authentication Flow

1. Load encrypted credentials from `config/credentials.enc`
2. Connect to NTU SSO login page
3. Extract hidden form fields
4. Submit credentials with form data
5. Verify successful authentication
6. Maintain session for subsequent requests

### Data Processing Pipeline

```
PDF → Extract → Filter → Clean → Normalize
                                    ↓
Module Scraper → Rate Limited Search → Parse Results
                                    ↓
                        Match & Combine Data
                                    ↓
                        Filter & Rank
                                    ↓
                    Generate CSV + Markdown
```

## License

This project is for personal educational use.

## Author

Ajitesh (DSAI Y3)

## Disclaimer

This tool is designed for legitimate academic planning purposes. Use responsibly and in accordance with NTU's acceptable use policies.
