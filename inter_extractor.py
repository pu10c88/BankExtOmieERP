#!/usr/bin/env python3
"""
Inter Bank Statement Extractor Module
Extracts transactions specifically from Inter bank statements.
"""

import re
from typing import List, Tuple
from dataclasses import dataclass
import logging


@dataclass
class Transaction:
    """Data class to represent a bank transaction."""
    date: str
    description: str
    amount: float
    transaction_type: str  # 'debit' or 'credit'
    card_number: str = None
    balance: float = None
    reference: str = None
    category: str = None


class InterExtractor:
    """Extractor specific for Inter bank statements."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Brazilian Inter bank statement table format patterns
        self.transaction_patterns = [
            # Main pattern: "DD de MMM. YYYY DESCRIPTION - R$ AMOUNT" or "DD de MMM. YYYY DESCRIPTION - + R$ AMOUNT"
            r'(\d{2}\s+de\s+\w+\.?\s+\d{4})\s+(.+?)\s+-\s+(?:\+\s+)?R\$\s+([\d.,]+)',
            # Pattern for lines with just the amount at the end: "DD de MMM. YYYY DESCRIPTION R$ AMOUNT"
            r'(\d{2}\s+de\s+\w+\.?\s+\d{4})\s+(.+?)\s+(?:\+\s+)?R\$\s+([\d.,]+)',
            # Backup patterns for other formats
            r'(\d{2}[/-]\d{2}[/-]\d{4})\s+(.+?)\s+([-+]?\d+[.,]\d{2})',
            r'(\d{4}-\d{2}-\d{2})\s+(.+?)\s+([-+]?\d+[.,]\d{2})',
        ]
        
        # Patterns to identify transaction types
        self.debit_keywords = ['DEBIT', 'WITHDRAWAL', 'TRANSFER OUT', 'FEE', 'CHARGE', 'MULTA', 'ENCARGOS', 'JUROS', 'IOF', 'TRANSFERENCIA']
        self.credit_keywords = ['CREDIT', 'DEPOSIT', 'TRANSFER IN', 'REFUND', 'INTEREST', 'PAGAMENTO', 'DEB AUT']
    
    def parse_amount(self, amount_str: str) -> Tuple[float, str]:
        """
        Parse amount string and determine transaction type.
        
        Args:
            amount_str: String representation of amount
            
        Returns:
            Tuple of (amount as float, transaction_type)
        """
        original_amount = amount_str.strip()
        
        # Check for negative sign or parentheses (indicating debit)
        is_debit = False
        if original_amount.startswith('-') or (original_amount.startswith('(') and original_amount.endswith(')')):
            is_debit = True
            amount_str = amount_str.replace('-', '').replace('(', '').replace(')', '').strip()
        
        # Handle Brazilian currency format (thousands separator)
        # Example: "1.234,56" should become "1234.56"
        if ',' in amount_str and '.' in amount_str:
            # Format like "1.234,56" - dot is thousands separator, comma is decimal
            amount_str = amount_str.replace('.', '').replace(',', '.')
        elif ',' in amount_str and '.' not in amount_str:
            # Format like "1234,56" - comma is decimal separator
            amount_str = amount_str.replace(',', '.')
        # If only dots, assume it's already in the correct format
        
        try:
            amount = float(amount_str)
            transaction_type = 'debit' if is_debit else 'credit'
            return amount, transaction_type
        except ValueError:
            self.logger.warning(f"Could not parse amount: {original_amount} -> {amount_str}")
            return 0.0, 'unknown'
    
    def parse_brazilian_date(self, date_str: str) -> str:
        """
        Parse Brazilian date format to a standard format.
        
        Args:
            date_str: Date string in Brazilian format (e.g., "03 de out. 2024")
            
        Returns:
            Standardized date string
        """
        # Mapping of Portuguese month abbreviations to numbers
        months = {
            'jan': '01', 'fev': '02', 'mar': '03', 'abr': '04',
            'mai': '05', 'jun': '06', 'jul': '07', 'ago': '08',
            'set': '09', 'out': '10', 'nov': '11', 'dez': '12'
        }
        
        try:
            # Handle format like "03 de out. 2024"
            parts = date_str.lower().split()
            if len(parts) >= 3 and 'de' in parts:
                day = parts[0].zfill(2)
                month_abbr = parts[2].replace('.', '')
                year = parts[3] if len(parts) > 3 else '2024'
                
                if month_abbr in months:
                    month = months[month_abbr]
                    return f"{day}/{month}/{year}"
        except Exception as e:
            self.logger.debug(f"Error parsing Brazilian date '{date_str}': {e}")
        
        # If parsing fails, return original
        return date_str

    def determine_transaction_type(self, description: str, amount: float, transaction_type: str) -> str:
        """
        Determine transaction type based on description and amount.
        
        Args:
            description: Transaction description
            amount: Transaction amount
            transaction_type: Initial transaction type
            
        Returns:
            Refined transaction type
        """
        description_upper = description.upper()
        
        # Check for credit indicators
        for keyword in self.credit_keywords:
            if keyword in description_upper:
                return 'credit'
        
        # Check for debit indicators
        for keyword in self.debit_keywords:
            if keyword in description_upper:
                return 'debit'
        
        # If amount is negative, it's likely a debit
        if amount < 0:
            return 'debit'
        
        # Default logic: typically expenses are debits, income is credit
        # This is Inter-specific logic - most transactions are expenses (debits)
        return transaction_type if transaction_type != 'unknown' else 'debit'
    
    def extract_transactions_from_text(self, text: str, filename: str) -> List[Transaction]:
        """
        Extract transactions from text using Inter-specific patterns.
        
        Args:
            text: Raw text from PDF
            filename: Name of the source file
            
        Returns:
            List of Transaction objects
        """
        transactions = []
        lines = text.split('\n')
        
        # Extract card number from filename or content
        card_number = self.extract_card_number(text, filename)
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try each transaction pattern
            for pattern in self.transaction_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    date_str = match.group(1)
                    description = match.group(2).strip()
                    amount_str = match.group(3)
                    
                    # Skip if description is too short or looks like a header
                    if len(description) < 3 or any(header in description.upper() 
                                                  for header in ['DATA', 'VALOR', 'DESCRIÇÃO', 'TOTAL']):
                        continue
                    
                    # Parse amount and determine transaction type
                    amount, initial_type = self.parse_amount(amount_str)
                    
                    if amount <= 0:
                        continue
                    
                    # Parse date
                    parsed_date = self.parse_brazilian_date(date_str)
                    
                    # Determine final transaction type
                    transaction_type = self.determine_transaction_type(description, amount, initial_type)
                    
                    # Create transaction
                    transaction = Transaction(
                        date=parsed_date,
                        description=description,
                        amount=amount,
                        transaction_type=transaction_type,
                        card_number=card_number,
                        reference=f"Inter-{filename}"
                    )
                    
                    transactions.append(transaction)
                    self.logger.debug(f"Extracted transaction: {transaction}")
                    break
        
        self.logger.info(f"Extracted {len(transactions)} transactions from Inter statement: {filename}")
        return transactions
    
    def extract_card_number(self, text: str, filename: str) -> str:
        """
        Extract card number from text or filename.
        
        Args:
            text: Raw text from PDF
            filename: Name of the source file
            
        Returns:
            Card number or default identifier
        """
        # Try to find card number patterns in text
        card_patterns = [
            r'(\d{4}\s*\*{4}\s*\*{4}\s*\d{4})',
            r'(\d{4}\s*\d{4}\s*\d{4}\s*\d{4})',
            r'Cart[ãa]o.*?(\d{4}\s*\*+\s*\d{4})',
        ]
        
        for pattern in card_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).replace(' ', '')
        
        # Extract from filename if available
        filename_match = re.search(r'(\d{4})', filename)
        if filename_match:
            return f"Inter-{filename_match.group(1)}"
        
        return "Inter-Default" 