#!/usr/bin/env python3
"""
Example usage of the Bank Statement Extractor
"""

from BankOmieApp import BankStatementExtractor

def main():
    """Example of how to use the bank statement extractor."""
    
    print("Bank Statement Extractor - Example Usage")
    print("=" * 50)
    
    # Create an instance of the extractor
    # It will look for PDF files in 'InterStatements' folder by default
    extractor = BankStatementExtractor(
        statement_folder="InterStatements",
        output_folder="output"
    )
    
    # Process all PDF files in the folder
    print("Processing bank statement PDFs...")
    transactions = extractor.process_all_files()
    
    if transactions:
        print(f"Successfully extracted {len(transactions)} transactions!")
        
        # Export to CSV
        csv_file = extractor.export_to_csv("my_transactions.csv")
        print(f"Transactions saved to: {csv_file}")
        
        # Get and display summary
        summary = extractor.get_summary()
        print("\nTransaction Summary:")
        print(f"- Total transactions: {summary['total_transactions']}")
        print(f"- Total debits: ${summary['total_debits']:.2f}")
        print(f"- Total credits: ${summary['total_credits']:.2f}")
        print(f"- Net amount: ${summary['net_amount']:.2f}")
        
        if summary['date_range']['earliest']:
            print(f"- Date range: {summary['date_range']['earliest']} to {summary['date_range']['latest']}")
        
        # Show first few transactions
        print(f"\nFirst 5 transactions:")
        for i, transaction in enumerate(transactions[:5]):
            print(f"{i+1}. {transaction.date} | {transaction.description[:50]}... | ${transaction.amount:.2f} ({transaction.transaction_type})")
            
    else:
        print("No transactions were extracted.")
        print("Please check:")
        print("1. PDF files exist in the 'InterStatements' folder")
        print("2. PDF files contain readable transaction data")
        print("3. Required dependencies are installed (run: pip install -r requirements.txt)")

if __name__ == "__main__":
    main() 