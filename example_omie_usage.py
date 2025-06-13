#!/usr/bin/env python3
"""
Example script showing how to use the Omie ERP export functionality
"""

from BankOmieApp import BankStatementExtractor
from datetime import datetime

def main():
    """Example of how to use the Omie ERP export functionality."""
    
    # Initialize the extractor
    extractor = BankStatementExtractor(
        statement_folder="InterStatements",
        output_folder="output"
    )
    
    # Process all PDF files
    print("Processing bank statement PDFs...")
    transactions = extractor.process_all_files()
    
    if transactions:
        print(f"Extracted {len(transactions)} transactions")
        
        # Get user input for invoice date
        while True:
            invoice_date = input("\nEnter invoice date for Omie export (DD/MM/YYYY): ").strip()
            
            # Validate date format
            try:
                datetime.strptime(invoice_date, "%d/%m/%Y")
                break
            except ValueError:
                print("Invalid date format. Please use DD/MM/YYYY format (e.g., 15/12/2024)")
        
        # Export to standard CSV format
        print("\nExporting to standard CSV format...")
        csv_path = extractor.export_to_csv("standard_transactions.csv")
        print(f"Standard CSV saved: {csv_path}")
        
        # Export to Omie ERP format
        print("\nExporting to Omie ERP format...")
        omie_csv_path = extractor.export_to_omie_csv(invoice_date, "omie_transactions.csv")
        print(f"Omie CSV saved: {omie_csv_path}")
        
        # Show summary
        summary = extractor.get_summary()
        debit_count = len([t for t in transactions if t.transaction_type == 'debit'])
        
        print(f"\n📊 Summary:")
        print(f"   Total transactions: {len(transactions)}")
        print(f"   Debit transactions (exported to Omie): {debit_count}")
        print(f"   Total debits: ${summary['total_debits']:.2f}")
        
        # Show sample of what will be in Omie export
        print(f"\n📄 Sample Omie Export Data:")
        print(f"   Invoice Date: {invoice_date}")
        print(f"   Observation format: 'Fatura do Banco Inter' (+ installment info if present)")
        
        # Show top 5 suppliers that will be exported
        debit_transactions = [t for t in transactions if t.transaction_type == 'debit']
        if debit_transactions:
            suppliers = {}
            for transaction in debit_transactions:
                supplier = extractor.extract_supplier_name(transaction.description)
                if supplier not in suppliers:
                    suppliers[supplier] = 0
                suppliers[supplier] += transaction.amount
            
            top_suppliers = sorted(suppliers.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"\n🏪 Top 5 Suppliers in Omie Export:")
            for i, (supplier, amount) in enumerate(top_suppliers, 1):
                print(f"   {i}. {supplier}: ${amount:.2f}")
    
    else:
        print("No transactions were found. Check your PDF files.")

if __name__ == "__main__":
    main() 