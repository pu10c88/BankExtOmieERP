#!/usr/bin/env python3
"""
Generate separate CSV files for each credit card and a summary report.
"""

import pandas as pd
from BankOmieApp import BankStatementExtractor
import os

def generate_card_reports():
    """Generate separate reports for each card."""
    
    # Create extractor and process files
    extractor = BankStatementExtractor("InterStatements", "output")
    transactions = extractor.process_all_files()
    
    if not transactions:
        print("No transactions found!")
        return
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame([{
        'date': t.date,
        'description': t.description,
        'amount': t.amount,
        'transaction_type': t.transaction_type,
        'card_number': t.card_number or 'Unknown',
        'reference': t.reference
    } for t in transactions])
    
    # Get summary
    summary = extractor.get_summary()
    
    # Create output directory for card reports
    card_reports_dir = "output/card_reports"
    os.makedirs(card_reports_dir, exist_ok=True)
    
    print(f"\n{'='*80}")
    print("GENERATING CARD REPORTS")
    print(f"{'='*80}")
    
    # Generate separate CSV for each card
    for card, card_data in summary['cards'].items():
        card_df = df[df['card_number'] == card].copy()
        
        # Sort by date
        card_df = card_df.sort_values('date')
        
        # Generate filename
        card_clean = card.replace('*', 'X').replace('/', '_')
        filename = f"{card_reports_dir}/transactions_{card_clean}.csv"
        
        # Save CSV
        card_df.to_csv(filename, index=False)
        
        print(f"\n💳 {card}:")
        print(f"   📄 File: {filename}")
        print(f"   📊 Transactions: {card_data['transactions']}")
        print(f"   💸 Debits: R$ {card_data['debits']:.2f}")
        print(f"   💰 Credits: R$ {card_data['credits']:.2f}")
        print(f"   📈 Net: R$ {card_data['net_amount']:.2f}")
    
    # Generate summary report
    summary_filename = f"{card_reports_dir}/summary_report.txt"
    with open(summary_filename, 'w', encoding='utf-8') as f:
        f.write("BANK STATEMENT SUMMARY REPORT\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"Total Transactions: {summary['total_transactions']}\n")
        f.write(f"Total Debits: R$ {summary['total_debits']:.2f}\n")
        f.write(f"Total Credits: R$ {summary['total_credits']:.2f}\n")
        f.write(f"Net Amount: R$ {summary['net_amount']:.2f}\n")
        
        if summary['date_range']['earliest']:
            f.write(f"Date Range: {summary['date_range']['earliest']} to {summary['date_range']['latest']}\n")
        
        f.write("\n" + "=" * 50 + "\n")
        f.write("BREAKDOWN BY CARD\n")
        f.write("=" * 50 + "\n\n")
        
        for card, card_data in summary['cards'].items():
            f.write(f"Card: {card}\n")
            f.write(f"  Transactions: {card_data['transactions']}\n")
            f.write(f"  Debits: R$ {card_data['debits']:.2f}\n")
            f.write(f"  Credits: R$ {card_data['credits']:.2f}\n")
            f.write(f"  Net: R$ {card_data['net_amount']:.2f}\n\n")
        
        # Add supplier analysis
        if 'suppliers' in summary and summary['suppliers']:
            f.write("\n" + "=" * 50 + "\n")
            f.write("TOP SUPPLIERS/VENDORS\n")
            f.write("=" * 50 + "\n\n")
            
            for i, (supplier, supplier_data) in enumerate(list(summary['suppliers'].items())[:15], 1):
                f.write(f"{i:2d}. {supplier}\n")
                f.write(f"    Transactions: {supplier_data['transactions']}\n")
                f.write(f"    Total Amount: R$ {supplier_data['total_amount']:.2f}\n")
                if supplier_data['debits'] > 0:
                    f.write(f"    Debits: R$ {supplier_data['debits']:.2f}\n")
                if supplier_data['credits'] > 0:
                    f.write(f"    Credits: R$ {supplier_data['credits']:.2f}\n")
                f.write("\n")
    
    # Generate suppliers CSV (overall)
    suppliers_filename = f"{card_reports_dir}/suppliers_analysis.csv"
    suppliers_data = []
    for supplier, data in summary['suppliers'].items():
        suppliers_data.append({
            'supplier': supplier,
            'transactions': data['transactions'],
            'total_amount': data['total_amount'],
            'debits': data['debits'],
            'credits': data['credits']
        })
    
    suppliers_df = pd.DataFrame(suppliers_data)
    suppliers_df.to_csv(suppliers_filename, index=False)
    
    # Generate suppliers per card CSV
    card_suppliers_filename = f"{card_reports_dir}/suppliers_by_card.csv"
    card_suppliers_data = []
    for card, card_data in summary['cards'].items():
        for supplier, supplier_data in card_data['suppliers'].items():
            card_suppliers_data.append({
                'card_number': card,
                'supplier': supplier,
                'transactions': supplier_data['transactions'],
                'total_amount': supplier_data['total_amount'],
                'debits': supplier_data['debits'],
                'credits': supplier_data['credits']
            })
    
    card_suppliers_df = pd.DataFrame(card_suppliers_data)
    card_suppliers_df.to_csv(card_suppliers_filename, index=False)
    
    print(f"\n📋 Summary report: {summary_filename}")
    print(f"📊 Suppliers analysis (overall): {suppliers_filename}")
    print(f"📊 Suppliers by card: {card_suppliers_filename}")
    print(f"\n✅ All reports generated in '{card_reports_dir}' folder")
    print(f"{'='*80}")

if __name__ == "__main__":
    generate_card_reports() 