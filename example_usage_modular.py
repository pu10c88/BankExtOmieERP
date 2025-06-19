#!/usr/bin/env python3
"""
Example usage of the modular Bank Statement Extractor
Demonstrates how to use both Inter and Itaú extractors.
"""

from BankOmieApp import BankStatementExtractor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def extract_inter_statements():
    """Example of extracting Inter bank statements."""
    print("="*60)
    print("EXTRACTING INTER BANK STATEMENTS")
    print("="*60)
    
    # Create Inter extractor
    inter_extractor = BankStatementExtractor(
        statement_folder="InterStatements",
        output_folder="output/inter",
        bank_type="inter"
    )
    
    # Process all files
    transactions = inter_extractor.process_all_files()
    
    if transactions:
        # Export various reports
        print(f"\n✅ Extracted {len(transactions)} Inter transactions")
        
        # Standard CSV export
        csv_path = inter_extractor.export_to_csv("inter_transactions.csv")
        print(f"📄 Standard CSV: {csv_path}")
        
        # By vendor report
        vendor_csv = inter_extractor.export_by_vendor_csv("inter_by_vendor.csv")
        print(f"📊 By vendor CSV: {vendor_csv}")
        
        # Summary report
        summary_csv = inter_extractor.export_summary_csv("inter_summary.csv")
        print(f"📋 Summary CSV: {summary_csv}")
        
        # Print summary
        summary = inter_extractor.get_summary()
        print(f"\n💰 Total debits: ${summary['total_debits']:.2f}")
        print(f"💳 Total credits: ${summary['total_credits']:.2f}")
        print(f"📈 Net amount: ${summary['net_amount']:.2f}")
    else:
        print("❌ No Inter transactions found")

def extract_itau_statements():
    """Example of extracting Itaú credit card statements."""
    print("\n" + "="*60)
    print("EXTRACTING ITAÚ CREDIT CARD STATEMENTS")
    print("="*60)
    
    # Create Itaú extractor
    itau_extractor = BankStatementExtractor(
        statement_folder="ItauStataments",
        output_folder="output/itau",
        bank_type="itau"
    )
    
    # Process all files
    transactions = itau_extractor.process_all_files()
    
    if transactions:
        # Export various reports
        print(f"\n✅ Extracted {len(transactions)} Itaú transactions")
        
        # Standard CSV export
        csv_path = itau_extractor.export_to_csv("itau_transactions.csv")
        print(f"📄 Standard CSV: {csv_path}")
        
        # By vendor report
        vendor_csv = itau_extractor.export_by_vendor_csv("itau_by_vendor.csv")
        print(f"📊 By vendor CSV: {vendor_csv}")
        
        # By month report
        month_csv = itau_extractor.export_by_month_csv("itau_by_month.csv")
        print(f"📅 By month CSV: {month_csv}")
        
        # Print summary
        summary = itau_extractor.get_summary()
        print(f"\n💰 Total debits: ${summary['total_debits']:.2f}")
        print(f"💳 Total credits: ${summary['total_credits']:.2f}")
        print(f"📈 Net amount: ${summary['net_amount']:.2f}")
        
        # Show top vendors
        if 'vendors' in summary and summary['vendors']:
            print(f"\n🏪 Top 5 vendors:")
            for i, (vendor, data) in enumerate(list(summary['vendors'].items())[:5], 1):
                print(f"   {i}. {vendor}: ${data['total_amount']:.2f} ({data['transactions']} transactions)")
    else:
        print("❌ No Itaú transactions found")

def compare_banks():
    """Compare transactions between banks."""
    print("\n" + "="*60)
    print("COMPARISON BETWEEN BANKS")
    print("="*60)
    
    try:
        # Inter data
        inter_extractor = BankStatementExtractor("InterStatements", "output", "inter")
        inter_transactions = inter_extractor.process_all_files()
        inter_summary = inter_extractor.get_summary() if inter_transactions else {}
        
        # Itaú data
        itau_extractor = BankStatementExtractor("ItauStataments", "output", "itau")
        itau_transactions = itau_extractor.process_all_files()
        itau_summary = itau_extractor.get_summary() if itau_transactions else {}
        
        print(f"\n📊 COMPARISON SUMMARY:")
        print(f"   Inter Bank:")
        print(f"     - Transactions: {len(inter_transactions)}")
        print(f"     - Total debits: ${inter_summary.get('total_debits', 0):.2f}")
        print(f"     - Total credits: ${inter_summary.get('total_credits', 0):.2f}")
        print(f"     - Net amount: ${inter_summary.get('net_amount', 0):.2f}")
        
        print(f"\n   Itaú Credit Card:")
        print(f"     - Transactions: {len(itau_transactions)}")
        print(f"     - Total debits: ${itau_summary.get('total_debits', 0):.2f}")
        print(f"     - Total credits: ${itau_summary.get('total_credits', 0):.2f}")
        print(f"     - Net amount: ${itau_summary.get('net_amount', 0):.2f}")
        
        # Combined totals
        total_debits = inter_summary.get('total_debits', 0) + itau_summary.get('total_debits', 0)
        total_credits = inter_summary.get('total_credits', 0) + itau_summary.get('total_credits', 0)
        
        print(f"\n   📈 COMBINED TOTALS:")
        print(f"     - Total transactions: {len(inter_transactions) + len(itau_transactions)}")
        print(f"     - Combined debits: ${total_debits:.2f}")
        print(f"     - Combined credits: ${total_credits:.2f}")
        print(f"     - Overall net: ${total_credits - total_debits:.2f}")
        
    except Exception as e:
        print(f"❌ Error in comparison: {e}")

def main():
    """Main function demonstrating usage."""
    print("🏦 MODULAR BANK STATEMENT EXTRACTOR DEMO")
    print("This example shows how to use both Inter and Itaú extractors")
    
    # Extract from each bank
    extract_inter_statements()
    extract_itau_statements()
    
    # Compare results
    compare_banks()
    
    print(f"\n" + "="*60)
    print("✅ DEMO COMPLETED")
    print("="*60)
    print("\nUsage examples:")
    print("• Command line Inter:  python3 BankOmieApp.py --inter")
    print("• Command line Itaú:   python3 BankOmieApp.py --itau")
    print("• Vendor report Inter: python3 BankOmieApp.py --inter --report-type by-vendor")
    print("• Summary report Itaú: python3 BankOmieApp.py --itau --report-type summary")
    print("• Custom input folder: python3 BankOmieApp.py --itau --input /path/to/pdfs")

if __name__ == "__main__":
    main() 