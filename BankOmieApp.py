#!/usr/bin/env python3
"""
Bank Statement Extractor
A modular tool to parse bank statements from PDF files and extract transactions to CSV format.
Supports Inter and Itaú bank statements.
"""

import os
import re
import csv
import logging
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import asdict
import argparse

# Import PDF libraries
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

# Import our specialized extractors
from inter_extractor import InterExtractor, Transaction
from itau_extractor import ItauExtractor


# Transaction class imported from extractors


class BankStatementExtractor:
    """Main class for extracting transactions from bank statements."""
    
    def __init__(self, statement_folder: str = "InterStatements", output_folder: str = "output", bank_type: str = "inter"):
        """
        Initialize the extractor.
        
        Args:
            statement_folder: Folder containing bank statement PDFs
            output_folder: Folder to save CSV output files
            bank_type: Type of bank statements ("inter" or "itau")
        """
        self.statement_folder = statement_folder
        self.output_folder = output_folder
        self.bank_type = bank_type.lower()
        self.transactions: List[Transaction] = []
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Initialize the appropriate extractor
        if self.bank_type == "inter":
            self.extractor = InterExtractor()
        elif self.bank_type == "itau":
            self.extractor = ItauExtractor()
        else:
            raise ValueError(f"Unsupported bank type: {bank_type}. Supported types: 'inter', 'itau'")
        
        self.logger.info(f"Initialized {bank_type.upper()} bank statement extractor")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF file using available libraries.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as string
        """
        text = ""
        
        # Try pdfplumber first (generally better for tables)
        if pdfplumber:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                self.logger.info(f"Successfully extracted text using pdfplumber from {pdf_path}")
                return text
            except Exception as e:
                self.logger.warning(f"pdfplumber failed for {pdf_path}: {e}")
        
        # Fallback to PyPDF2
        if PyPDF2:
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                self.logger.info(f"Successfully extracted text using PyPDF2 from {pdf_path}")
                return text
            except Exception as e:
                self.logger.error(f"PyPDF2 failed for {pdf_path}: {e}")
        
        if not pdfplumber and not PyPDF2:
            self.logger.error("No PDF libraries available. Please install pdfplumber or PyPDF2")
            
        return text
    

    
    def process_single_file(self, file_path: str) -> List[Transaction]:
        """
        Process a single PDF file and extract transactions.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of transactions extracted from the file
        """
        self.logger.info(f"Processing file: {file_path}")
        
        # Extract text from PDF
        text = self.extract_text_from_pdf(file_path)
        
        if not text.strip():
            self.logger.warning(f"No text extracted from {file_path}")
            return []
        
        # Use the appropriate extractor
        filename = os.path.basename(file_path)
        transactions = self.extractor.extract_transactions_from_text(text, filename)
        
        self.logger.info(f"Extracted {len(transactions)} transactions from {file_path}")
        return transactions
    
    def process_all_files(self) -> List[Transaction]:
        """
        Process all PDF files in the statement folder.
        
        Returns:
            List of all transactions extracted from all files
        """
        self.transactions = []
        
        if not os.path.exists(self.statement_folder):
            self.logger.error(f"Statement folder not found: {self.statement_folder}")
            return []
        
        pdf_files = [f for f in os.listdir(self.statement_folder) if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            self.logger.warning(f"No PDF files found in {self.statement_folder}")
            return []
        
        self.logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        for pdf_file in pdf_files:
            file_path = os.path.join(self.statement_folder, pdf_file)
            file_transactions = self.process_single_file(file_path)
            self.transactions.extend(file_transactions)
        
        self.logger.info(f"Total transactions extracted: {len(self.transactions)}")
        return self.transactions
    
    def export_to_csv(self, filename: str = None) -> str:
        """
        Export extracted transactions to CSV file.
        
        Args:
            filename: Optional custom filename for the CSV file
            
        Returns:
            Path to the created CSV file
        """
        if not self.transactions:
            self.logger.warning("No transactions to export")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bank_transactions_{timestamp}.csv"
        
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        csv_path = os.path.join(self.output_folder, filename)
        
        # Write to CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['date', 'description', 'amount', 'transaction_type', 'card_number', 'balance', 'reference', 'category']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write transactions
            for transaction in self.transactions:
                writer.writerow(asdict(transaction))
        
        self.logger.info(f"Exported {len(self.transactions)} transactions to {csv_path}")
        return csv_path
    
    def export_to_omie_csv(self, invoice_date: str, filename: str = None) -> str:
        """
        Export extracted transactions to CSV file formatted for Omie ERP integration.
        Only includes debit transactions (expenses).
        
        Args:
            invoice_date: Invoice date in DD/MM/YYYY format (same for all transactions)
            filename: Optional custom filename for the CSV file
            
        Returns:
            Path to the created CSV file
        """
        # Filter only debit transactions (expenses)
        debit_transactions = [t for t in self.transactions if t.transaction_type == 'debit']
        
        if not debit_transactions:
            self.logger.warning("No debit transactions to export for Omie ERP")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"omie_transactions_{timestamp}.csv"
        
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        csv_path = os.path.join(self.output_folder, filename)
        
        # Write to CSV with Omie ERP format
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'cNomeFornecedor',      # Supplier name
                'nValorTitulo',         # Transaction amount
                'cNumeroCartao',        # Card number
                'cNumeroParcelas',      # Installment info
                'cObservacao',          # Observation
                'dEmissao',             # Invoice date
                'dVencimento'           # Due date (same as invoice date)
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write transactions
            for transaction in debit_transactions:
                supplier_name = self.extract_supplier_name(transaction.description)
                installment_info = self.extract_installment_info(transaction.description)
                
                # Build observation
                observation = "Fatura do Banco Inter"
                if installment_info:
                    observation += f" - Parcela {installment_info}"
                
                row = {
                    'cNomeFornecedor': supplier_name,
                    'nValorTitulo': f"{transaction.amount:.2f}",
                    'cNumeroCartao': transaction.card_number or "",
                    'cNumeroParcelas': installment_info,
                    'cObservacao': observation,
                    'dEmissao': transaction.date,  # Data da compra (transação individual)
                    'dVencimento': invoice_date    # Data de vencimento da fatura
                }
                
                writer.writerow(row)
        
        self.logger.info(f"Exported {len(debit_transactions)} debit transactions to Omie CSV: {csv_path}")
        return csv_path
    
    def export_by_card_csv(self, filename: str = None) -> str:
        """
        Export transactions grouped by card number.
        
        Args:
            filename: Optional custom filename for the CSV file
            
        Returns:
            Path to the created CSV file
        """
        if not self.transactions:
            self.logger.warning("No transactions to export")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transactions_by_card_{timestamp}.csv"
        
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        csv_path = os.path.join(self.output_folder, filename)
        
        # Group transactions by card
        summary = self.get_summary()
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['card_number', 'total_transactions', 'total_debits', 'total_credits', 'net_amount']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for card, data in summary['cards'].items():
                writer.writerow({
                    'card_number': card,
                    'total_transactions': data['transactions'],
                    'total_debits': f"{data['debits']:.2f}",
                    'total_credits': f"{data['credits']:.2f}",
                    'net_amount': f"{data['net_amount']:.2f}"
                })
        
        self.logger.info(f"Exported card summary to {csv_path}")
        return csv_path
    
    def export_by_vendor_csv(self, filename: str = None) -> str:
        """
        Export transactions grouped by vendor/supplier.
        
        Args:
            filename: Optional custom filename for the CSV file
            
        Returns:
            Path to the created CSV file
        """
        if not self.transactions:
            self.logger.warning("No transactions to export")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transactions_by_vendor_{timestamp}.csv"
        
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        csv_path = os.path.join(self.output_folder, filename)
        
        summary = self.get_summary()
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['vendor_name', 'total_transactions', 'total_debits', 'total_credits', 'net_amount']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for vendor, data in summary['suppliers'].items():
                writer.writerow({
                    'vendor_name': vendor,
                    'total_transactions': data['transactions'],
                    'total_debits': f"{data['debits']:.2f}",
                    'total_credits': f"{data['credits']:.2f}",
                    'net_amount': f"{data['debits'] - data['credits']:.2f}"
                })
        
        self.logger.info(f"Exported vendor summary to {csv_path}")
        return csv_path
    
    def export_by_month_csv(self, filename: str = None) -> str:
        """
        Export transactions grouped by month.
        
        Args:
            filename: Optional custom filename for the CSV file
            
        Returns:
            Path to the created CSV file
        """
        if not self.transactions:
            self.logger.warning("No transactions to export")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transactions_by_month_{timestamp}.csv"
        
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        csv_path = os.path.join(self.output_folder, filename)
        
        # Group by month
        monthly_data = {}
        for transaction in self.transactions:
            try:
                # Parse date (DD/MM/YYYY format)
                date_parts = transaction.date.split('/')
                if len(date_parts) == 3:
                    month_key = f"{date_parts[1]}/{date_parts[2]}"  # MM/YYYY
                else:
                    month_key = "Unknown"
                
                if month_key not in monthly_data:
                    monthly_data[month_key] = {
                        'transactions': 0,
                        'debits': 0.0,
                        'credits': 0.0
                    }
                
                monthly_data[month_key]['transactions'] += 1
                if transaction.transaction_type == 'debit':
                    monthly_data[month_key]['debits'] += transaction.amount
                else:
                    monthly_data[month_key]['credits'] += transaction.amount
                    
            except Exception as e:
                self.logger.debug(f"Error parsing date '{transaction.date}': {e}")
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['month', 'total_transactions', 'total_debits', 'total_credits', 'net_amount']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            # Sort by month/year
            for month, data in sorted(monthly_data.items()):
                net_amount = data['credits'] - data['debits']
                writer.writerow({
                    'month': month,
                    'total_transactions': data['transactions'],
                    'total_debits': f"{data['debits']:.2f}",
                    'total_credits': f"{data['credits']:.2f}",
                    'net_amount': f"{net_amount:.2f}"
                })
        
        self.logger.info(f"Exported monthly summary to {csv_path}")
        return csv_path
    
    def export_summary_csv(self, filename: str = None) -> str:
        """
        Export a general summary report.
        
        Args:
            filename: Optional custom filename for the CSV file
            
        Returns:
            Path to the created CSV file
        """
        if not self.transactions:
            self.logger.warning("No transactions to export")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"summary_report_{timestamp}.csv"
        
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        csv_path = os.path.join(self.output_folder, filename)
        
        summary = self.get_summary()
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['metric', 'value']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            writer.writerow({'metric': 'Total Transactions', 'value': summary['total_transactions']})
            writer.writerow({'metric': 'Total Debits', 'value': f"${summary['total_debits']:.2f}"})
            writer.writerow({'metric': 'Total Credits', 'value': f"${summary['total_credits']:.2f}"})
            writer.writerow({'metric': 'Net Amount', 'value': f"${summary['net_amount']:.2f}"})
            writer.writerow({'metric': 'Date Range Start', 'value': summary['date_range']['earliest']})
            writer.writerow({'metric': 'Date Range End', 'value': summary['date_range']['latest']})
            writer.writerow({'metric': 'Number of Cards', 'value': len(summary['cards'])})
            writer.writerow({'metric': 'Number of Vendors', 'value': len(summary['vendors'])})
        
        self.logger.info(f"Exported summary report to {csv_path}")
        return csv_path
    
    def extract_supplier_name(self, description: str) -> str:
        """
        Extract supplier/vendor name from transaction description.
        
        Args:
            description: Transaction description
            
        Returns:
            Cleaned supplier name
        """
        # Remove common patterns
        desc = description.upper()
        
        # Remove parcela information
        desc = re.sub(r'\(PARCELA \d+ DE \d+\)', '', desc).strip()
        
        # Handle specific patterns
        if '*' in desc:
            # For descriptions like "MERCADOLIVRE*TROPICAL", "INSIDER COME*InsiderSt"
            desc = desc.split('*')[0].strip()
        
        # Remove common payment-related words
        payment_words = ['PAGAMENTO', 'DEB AUT', 'IOF', 'JUROS', 'ENCARGOS', 'MULTA']
        for word in payment_words:
            if word in desc:
                return word
        
        # Clean up and return first meaningful part
        desc = desc.strip()
        if len(desc) > 30:  # If too long, try to get main part
            parts = desc.split()
            if len(parts) >= 2:
                desc = ' '.join(parts[:2])
        
        return desc if desc else "OTHER"

    def extract_installment_info(self, description: str) -> str:
        """
        Extract installment information from transaction description.
        
        Args:
            description: Transaction description
            
        Returns:
            Installment info like "4/10" if present, otherwise empty string
        """
        # Look for patterns like "(PARCELA 4 DE 10)" or "PARCELA 4/10"
        parcela_patterns = [
            r'\(PARCELA (\d+) DE (\d+)\)',
            r'PARCELA (\d+) DE (\d+)',
            r'PARCELA (\d+)/(\d+)',
            r'(\d+)/(\d+) PARCELA'
        ]
        
        description_upper = description.upper()
        
        for pattern in parcela_patterns:
            match = re.search(pattern, description_upper)
            if match:
                current_installment, total_installments = match.groups()
                return f"{current_installment}/{total_installments}"
        
        return ""

    def get_summary(self) -> Dict:
        """
        Get a summary of extracted transactions with per-card and per-supplier breakdown.
        
        Returns:
            Dictionary with transaction summary
        """
        if not self.transactions:
            return {"total_transactions": 0}
        
        # Overall totals
        total_debits = sum(t.amount for t in self.transactions if t.transaction_type == 'debit')
        total_credits = sum(t.amount for t in self.transactions if t.transaction_type == 'credit')
        
        # Group transactions by card
        cards = {}
        for transaction in self.transactions:
            card = transaction.card_number or "Unknown Card"
            if card not in cards:
                cards[card] = {
                    "transactions": 0,
                    "debits": 0.0,
                    "credits": 0.0,
                    "net_amount": 0.0,
                    "suppliers": {}
                }
            
            cards[card]["transactions"] += 1
            if transaction.transaction_type == 'debit':
                cards[card]["debits"] += transaction.amount
            else:
                cards[card]["credits"] += transaction.amount
            
            cards[card]["net_amount"] = cards[card]["credits"] - cards[card]["debits"]
            
            # Track suppliers per card
            supplier = self.extract_supplier_name(transaction.description)
            if supplier not in cards[card]["suppliers"]:
                cards[card]["suppliers"][supplier] = {
                    "transactions": 0,
                    "total_amount": 0.0,
                    "debits": 0.0,
                    "credits": 0.0
                }
            
            cards[card]["suppliers"][supplier]["transactions"] += 1
            cards[card]["suppliers"][supplier]["total_amount"] += transaction.amount
            
            if transaction.transaction_type == 'debit':
                cards[card]["suppliers"][supplier]["debits"] += transaction.amount
            else:
                cards[card]["suppliers"][supplier]["credits"] += transaction.amount
        
        # Group transactions by supplier (separate vendors from payments/credits)
        suppliers = {}  # All suppliers including payments
        vendors = {}    # Only expense vendors (debits)
        payments = {}   # Only credits/payments
        
        for transaction in self.transactions:
            supplier = self.extract_supplier_name(transaction.description)
            
            # Add to overall suppliers
            if supplier not in suppliers:
                suppliers[supplier] = {
                    "transactions": 0,
                    "total_amount": 0.0,
                    "debits": 0.0,
                    "credits": 0.0
                }
            
            suppliers[supplier]["transactions"] += 1
            suppliers[supplier]["total_amount"] += transaction.amount
            
            if transaction.transaction_type == 'debit':
                suppliers[supplier]["debits"] += transaction.amount
                
                # Add to vendors (expenses only)
                if supplier not in vendors:
                    vendors[supplier] = {
                        "transactions": 0,
                        "total_amount": 0.0,
                        "debits": 0.0,
                        "credits": 0.0
                    }
                vendors[supplier]["transactions"] += 1
                vendors[supplier]["total_amount"] += transaction.amount
                vendors[supplier]["debits"] += transaction.amount
            else:
                suppliers[supplier]["credits"] += transaction.amount
                
                # Add to payments (credits only)
                if supplier not in payments:
                    payments[supplier] = {
                        "transactions": 0,
                        "total_amount": 0.0,
                        "debits": 0.0,
                        "credits": 0.0
                    }
                payments[supplier]["transactions"] += 1
                payments[supplier]["total_amount"] += transaction.amount
                payments[supplier]["credits"] += transaction.amount
        
        # Sort all categories by total amount (descending)
        suppliers = dict(sorted(suppliers.items(), key=lambda x: x[1]["total_amount"], reverse=True))
        vendors = dict(sorted(vendors.items(), key=lambda x: x[1]["total_amount"], reverse=True))
        payments = dict(sorted(payments.items(), key=lambda x: x[1]["total_amount"], reverse=True))
        
        # Sort suppliers within each card
        for card in cards:
            cards[card]["suppliers"] = dict(sorted(
                cards[card]["suppliers"].items(), 
                key=lambda x: x[1]["total_amount"], 
                reverse=True
            ))
        
        return {
            "total_transactions": len(self.transactions),
            "total_debits": total_debits,
            "total_credits": total_credits,
            "net_amount": total_credits - total_debits,
            "date_range": {
                "earliest": min(t.date for t in self.transactions) if self.transactions else None,
                "latest": max(t.date for t in self.transactions) if self.transactions else None
            },
            "cards": cards,
            "suppliers": suppliers,
            "vendors": vendors,
            "payments": payments
        }


def main():
    """Main function to run the bank statement extractor."""
    parser = argparse.ArgumentParser(description='Extract transactions from bank statement PDFs')
    parser.add_argument('--input', '-i', 
                       help='Input folder containing PDF statements')
    parser.add_argument('--output', '-o', default='output', 
                       help='Output folder for CSV files (default: output)')
    parser.add_argument('--filename', '-f', 
                       help='Custom filename for the output CSV')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    parser.add_argument('--omie', action='store_true',
                       help='Export in Omie ERP format (debit transactions only)')
    parser.add_argument('--invoice-date', 
                       help='Invoice date for Omie export (DD/MM/YYYY format)')
    parser.add_argument('--report-type', '-r', 
                       choices=['standard', 'omie', 'by-card', 'by-vendor', 'by-month', 'summary'],
                       help='Type of CSV report to generate')
    
    # Bank type selection (mutually exclusive)
    bank_group = parser.add_mutually_exclusive_group(required=True)
    bank_group.add_argument('--inter', action='store_true',
                           help='Process Inter bank statements')
    bank_group.add_argument('--itau', action='store_true',
                           help='Process Itaú credit card statements')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Determine bank type and default input folder
    if args.inter:
        bank_type = "inter"
        default_input = "InterStatements"
    elif args.itau:
        bank_type = "itau"
        default_input = "ItauStataments"
    else:
        # This shouldn't happen due to mutually_exclusive_group(required=True)
        parser.error("Must specify either --inter or --itau")
    
    # Use provided input folder or default
    input_folder = args.input if args.input else default_input
    
    # Create extractor instance
    extractor = BankStatementExtractor(input_folder, args.output, bank_type)
    
    # Process all files
    transactions = extractor.process_all_files()
    
    if transactions:
        # Handle different report types
        csv_path = None
        omie_csv_path = None
        
        # If report type is specified, generate that specific report
        if args.report_type:
            if args.report_type == 'standard':
                csv_path = extractor.export_to_csv(args.filename)
            elif args.report_type == 'omie':
                # Force omie export
                args.omie = True
            elif args.report_type == 'by-card':
                csv_path = extractor.export_by_card_csv(args.filename)
            elif args.report_type == 'by-vendor':
                csv_path = extractor.export_by_vendor_csv(args.filename)
            elif args.report_type == 'by-month':
                csv_path = extractor.export_by_month_csv(args.filename)
            elif args.report_type == 'summary':
                csv_path = extractor.export_summary_csv(args.filename)
        else:
            # Default behavior: export standard CSV
            csv_path = extractor.export_to_csv(args.filename)
        
        # Handle Omie export if requested (either via --omie flag or --report-type omie)
        if args.omie or args.report_type == 'omie':
            invoice_date = args.invoice_date
            
            # If invoice date not provided via command line, ask user
            if not invoice_date:
                while True:
                    invoice_date = input("\nEnter invoice date for Omie export (DD/MM/YYYY): ").strip()
                    
                    # Validate date format
                    try:
                        datetime.strptime(invoice_date, "%d/%m/%Y")
                        break
                    except ValueError:
                        print("Invalid date format. Please use DD/MM/YYYY format (e.g., 15/12/2024)")
            
            # Export to Omie format
            if args.filename:
                # If user specified a filename, create Omie version with _omie suffix
                if args.filename.endswith('.csv'):
                    omie_filename = args.filename.replace('.csv', '_omie.csv')
                else:
                    omie_filename = args.filename + '_omie.csv'
            else:
                # Use default naming with timestamp
                omie_filename = None
            omie_csv_path = extractor.export_to_omie_csv(invoice_date, omie_filename)
        
        # Print summary
        summary = extractor.get_summary()
        print(f"\n{'='*70}")
        print("EXTRACTION SUMMARY")
        print(f"{'='*70}")
        print(f"Total transactions extracted: {summary['total_transactions']}")
        print(f"Total debits: ${summary['total_debits']:.2f}")
        print(f"Total credits: ${summary['total_credits']:.2f}")
        print(f"Net amount: ${summary['net_amount']:.2f}")
        if summary['date_range']['earliest']:
            print(f"Date range: {summary['date_range']['earliest']} to {summary['date_range']['latest']}")
        
        # Print per-card breakdown
        if 'cards' in summary and summary['cards']:
            print(f"\n{'='*70}")
            print("BREAKDOWN BY CARD")
            print(f"{'='*70}")
            for card, card_data in summary['cards'].items():
                print(f"\n📱 {card}:")
                print(f"   Transactions: {card_data['transactions']}")
                print(f"   Debits: ${card_data['debits']:.2f}")
                print(f"   Credits: ${card_data['credits']:.2f}")
                print(f"   Net: ${card_data['net_amount']:.2f}")
        
        # Print payments/credits received
        if 'payments' in summary and summary['payments']:
            print(f"\n{'='*70}")
            print("PAYMENTS/CREDITS RECEIVED")
            print(f"{'='*70}")
            for i, (payment, payment_data) in enumerate(summary['payments'].items(), 1):
                print(f"\n{i:2d}. 💰 {payment}:")
                print(f"    Transactions: {payment_data['transactions']}")
                print(f"    Total Credits: ${payment_data['total_amount']:.2f}")
        
        # Print ALL vendor expenses (not just top 10)
        if 'vendors' in summary and summary['vendors']:
            print(f"\n{'='*70}")
            print(f"ALL VENDOR EXPENSES ({len(summary['vendors'])} unique vendors)")
            print(f"{'='*70}")
            for i, (vendor, vendor_data) in enumerate(summary['vendors'].items(), 1):
                print(f"\n{i:2d}. 🏪 {vendor}:")
                print(f"    Transactions: {vendor_data['transactions']}")
                print(f"    Total Spent: ${vendor_data['total_amount']:.2f}")
        
        # Print suppliers per card (only debit expenses, top 5 per card)
        if 'cards' in summary and summary['cards']:
            print(f"\n{'='*70}")
            print("TOP VENDOR EXPENSES PER CREDIT CARD")
            print(f"{'='*70}")
            for card, card_data in summary['cards'].items():
                if card_data['suppliers']:
                    # Filter only debit expenses (not credits)
                    vendor_expenses = {k: v for k, v in card_data['suppliers'].items() if v['debits'] > 0}
                    if vendor_expenses:
                        print(f"\n📱 {card} - Top Vendor Expenses:")
                        for i, (supplier, supplier_data) in enumerate(list(vendor_expenses.items())[:10], 1):
                            print(f"   {i}. {supplier}: ${supplier_data['debits']:.2f} ({supplier_data['transactions']} transactions)")
        
        # Show generated files
        if csv_path:
            report_type_name = args.report_type.capitalize() if args.report_type else "Standard"
            print(f"\n💾 {report_type_name} CSV file saved: {csv_path}")
        
        if omie_csv_path:
            print(f"💾 Omie ERP CSV file saved: {omie_csv_path}")
            
        print(f"{'='*70}")
    else:
        print("No transactions were extracted. Please check your PDF files and try again.")


if __name__ == "__main__":
    main() 