# Bank Statement Extractor

A Python module for extracting transactions from bank statement PDF files and exporting them to CSV format.

## Features

- **PDF Text Extraction**: Supports both `pdfplumber` and `PyPDF2` libraries for robust PDF text extraction
- **Pattern Recognition**: Uses regular expressions to identify transaction patterns
- **Transaction Classification**: Automatically classifies transactions as debit or credit
- **CSV Export**: Exports all extracted transactions to a structured CSV file
- **Batch Processing**: Processes multiple PDF files at once
- **Summary Reports**: Provides detailed summaries of extracted data
- **Flexible Configuration**: Customizable input/output folders and file naming

## Installation

1. **Clone or download the files** to your project directory

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Command Line Interface

The simplest way to use the extractor is through the command line:

```bash
# Basic usage (processes PDFs in 'InterStatements' folder)
python BankOmieApp.py

# Specify custom input and output folders
python BankOmieApp.py --input /path/to/statements --output /path/to/output

# Custom output filename
python BankOmieApp.py --filename my_transactions.csv

# Verbose logging
python BankOmieApp.py --verbose
```

### Python API

You can also use the extractor programmatically:

```python
from BankOmieApp import BankStatementExtractor

# Create extractor instance
extractor = BankStatementExtractor(
    statement_folder="InterStatements",
    output_folder="output"
)

# Process all PDFs and extract transactions
transactions = extractor.process_all_files()

# Export to CSV
csv_file = extractor.export_to_csv("transactions.csv")

# Get summary
summary = extractor.get_summary()
print(f"Extracted {summary['total_transactions']} transactions")
```

### Example Usage

Run the example script to see the extractor in action:

```bash
python example_usage.py
```

## File Structure

```
your_project/
├── BankOmieApp.py                 # Main extractor module
├── example_usage.py               # Example usage script
├── requirements.txt               # Dependencies
├── README.md                      # This file
├── InterStatements/               # Input folder for PDF statements
│   └── MERAKI_FATURA_05.25.pdf   # Your bank statement PDFs
└── output/                        # Output folder (created automatically)
    └── bank_transactions_*.csv    # Generated CSV files
```

## Output Format

The extracted transactions are saved in CSV format with the following columns:

| Column | Description |
|--------|-------------|
| `date` | Transaction date |
| `description` | Transaction description/memo |
| `amount` | Transaction amount (positive number) |
| `transaction_type` | Either 'debit' or 'credit' |
| `balance` | Account balance (if available) |
| `reference` | Source file reference |
| `category` | Transaction category (if available) |

## Supported PDF Formats

The extractor works with various bank statement formats and uses pattern matching to identify:

- **Date formats**: MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD, MM/DD
- **Amount formats**: 123.45, 123,45, (123.45), -123.45
- **Transaction types**: Automatic detection based on amount signs and keywords

## Customization

### Adding New Transaction Patterns

You can extend the extractor to support additional bank formats by modifying the `transaction_patterns` list in the `BankStatementExtractor` class:

```python
self.transaction_patterns = [
    r'(\d{2}[/-]\d{2}[/-]\d{4})\s+(.+?)\s+([-+]?\d+[.,]\d{2})',
    # Add your custom patterns here
    r'your_custom_pattern_here',
]
```

### Adding Transaction Type Keywords

Customize transaction type detection by modifying the keyword lists:

```python
self.debit_keywords = ['DEBIT', 'WITHDRAWAL', 'PAYMENT', 'YOUR_BANK_DEBIT_TERM']
self.credit_keywords = ['CREDIT', 'DEPOSIT', 'TRANSFER IN', 'YOUR_BANK_CREDIT_TERM']
```

## Troubleshooting

### No transactions extracted
1. Ensure PDF files are in the correct folder (`InterStatements` by default)
2. Check that PDFs contain machine-readable text (not scanned images)
3. Verify the transaction patterns match your bank's statement format
4. Run with `--verbose` flag to see detailed processing logs

### Installation issues
1. Make sure you have Python 3.7+ installed
2. Install dependencies: `pip install -r requirements.txt`
3. If PDF libraries fail to install, try: `pip install --upgrade pip setuptools wheel`

### Custom bank formats
1. Examine your PDF's text structure by extracting text manually
2. Create custom regex patterns to match your bank's format
3. Test patterns with a small sample before processing all files

## Dependencies

- **pdfplumber**: For advanced PDF text extraction
- **PyPDF2**: Fallback PDF text extraction
- **pandas**: Data manipulation (optional, for advanced features)

## Contributing

Feel free to extend this extractor for additional bank formats or features. The modular design makes it easy to add support for new statement formats.

## License

This project is open source. Feel free to modify and distribute as needed. 