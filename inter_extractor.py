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
        self.document_year = None  # Will be extracted from document
        
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
                
                # If year is present in the date string, use it
                if len(parts) > 3:
                    year = parts[3]
                else:
                    # Use the document year if available, otherwise fallback to current year
                    if self.document_year:
                        year = self.document_year
                    else:
                        from datetime import datetime
                        year = str(datetime.now().year)
                        self.logger.warning(f"No document year available, using current year {year} for date '{date_str}'")
                
                if month_abbr in months:
                    month = months[month_abbr]
                    return f"{day}/{month}/{year}"
        except Exception as e:
            self.logger.debug(f"Error parsing Brazilian date '{date_str}': {e}")
        
        # If parsing fails, return original
        return date_str
    
    def extract_document_year(self, text: str, filename: str) -> str:
        """
        Extract the transaction year from text or filename.
        Priority: filename > transaction dates > document headers
        
        Args:
            text: Raw text from PDF
            filename: Name of the source file
            
        Returns:
            Transaction year as string
        """
        # PRIORITY 1: Extract year from filename (most reliable)
        filename_year = None
        filename_match = re.search(r'(\d{2})\.(\d{2})\.pdf', filename)
        if filename_match:
            month, year_suffix = filename_match.groups()
            # Assume 20XX format
            if int(year_suffix) >= 20 and int(year_suffix) <= 30:
                filename_year = f"20{year_suffix}"
                self.logger.info(f"Using transaction year from filename: {filename_year}")
                return filename_year
        
        # Another filename pattern like "2024_statement.pdf"
        filename_match = re.search(r'(20[2-3]\d)', filename)
        if filename_match:
            filename_year = filename_match.group(1)
            self.logger.info(f"Using transaction year from filename: {filename_year}")
            return filename_year
        
        # PRIORITY 2: Look for years in transaction lines (with dates)
        years_found = []
        
        # Look for years in transaction context (lines with "de MMM. YYYY")
        transaction_lines = text.split('\n')
        for line in transaction_lines:
            # Look for transaction patterns with years
            if re.search(r'\d{2}\s+de\s+\w+\.?\s+\d{4}', line):
                year_matches = re.findall(r'\d{2}\s+de\s+\w+\.?\s+(\d{4})', line)
                valid_years = [y for y in year_matches if 2020 <= int(y) <= 2030]
                years_found.extend(valid_years)
        
        # PRIORITY 3: Look for years in date patterns (avoid headers like "Vencimento")
        if not years_found:
            # Avoid header patterns
            date_pattern = r'(?<!Vencimento.*)\d{1,2}[/.-]\d{1,2}[/.-](20[2-3]\d)'
            date_matches = re.findall(date_pattern, text)
            valid_years = [y for y in date_matches if 2020 <= int(y) <= 2030]
            years_found.extend(valid_years)
        
        # PRIORITY 4: General year patterns as last resort
        if not years_found:
            year_pattern = r'\b(20[2-3]\d)\b'
            year_matches = re.findall(year_pattern, text)
            valid_years = [y for y in year_matches if 2020 <= int(y) <= 2030]
            years_found.extend(valid_years)
        
        # Process found years
        if years_found:
            # For transaction years, if we have mixed years, prefer the one that appears in transaction contexts
            year_count = {}
            for year in years_found:
                year_count[year] = year_count.get(year, 0) + 1
            
            # If we have multiple years with similar frequency, prefer the earlier one for transactions
            if len(year_count) > 1:
                # Check if we have a clear transaction year vs header year pattern
                max_count = max(year_count.values())
                frequent_years = [year for year, count in year_count.items() if count >= max_count * 0.8]
                
                if len(frequent_years) > 1:
                    transaction_year = str(min(int(y) for y in frequent_years))
                    self.logger.info(f"Multiple frequent years {year_count}, using earlier for transactions: {transaction_year}")
                    return transaction_year
            
            most_common_year = max(year_count, key=year_count.get)
            self.logger.info(f"Detected transaction year: {most_common_year} (found {year_count})")
            return most_common_year
        
        # Ultimate fallback: current year - 1 (transactions usually from previous periods)
        from datetime import datetime
        current_year = datetime.now().year
        fallback_year = str(current_year - 1)
        self.logger.warning(f"Could not determine transaction year, using previous year: {fallback_year}")
        return fallback_year

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
        Inter organizes transactions by card sections.
        
        Args:
            text: Raw text from PDF
            filename: Name of the source file
            
        Returns:
            List of Transaction objects
        """
        transactions = []
        lines = text.split('\n')
        
        # Extract document year first
        self.document_year = self.extract_document_year(text, filename)
        
        # Track current card number as we parse through sections
        current_card_number = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check if this line indicates a new card section
            card_section_match = re.search(r'CARTÃO\s+(\d{4}\*{4}\d{4})', line, re.IGNORECASE)
            if card_section_match:
                current_card_number = card_section_match.group(1)
                self.logger.debug(f"Found card section: {current_card_number}")
                continue
            
            # Also check for card numbers at the beginning of lines (summary sections)
            card_line_match = re.search(r'^(\d{4}\*{4}\d{4})\s+', line)
            if card_line_match:
                current_card_number = card_line_match.group(1)
                self.logger.debug(f"Found card in line: {current_card_number}")
                # Don't continue here as this line might also contain transaction data
            
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
                    
                    # Use current card number or fallback to generic extraction
                    card_number = current_card_number or self.extract_card_number(text, filename)
                    
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
                    self.logger.debug(f"Extracted transaction: {transaction} (Card: {card_number})")
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
        # Try to find card number patterns in text (Inter format: XXXX****XXXX)
        card_patterns = [
            r'(\d{4}\*{4}\d{4})',  # Inter specific format
            r'(\d{4}\s*\*{4}\s*\*{4}\s*\d{4})',
            r'(\d{4}\s*\d{4}\s*\d{4}\s*\d{4})',
            r'Cart[ãa]o.*?(\d{4}\s*\*+\s*\d{4})',
        ]
        
        for pattern in card_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).replace(' ', '')
        
        # Extract year from filename to create a more meaningful default
        year_match = re.search(r'(\d{2})\.(\d{2})\.pdf', filename)
        if year_match:
            month, year = year_match.groups()
            return f"2025307793960001"  # Use a consistent format
        
        # Extract from filename if available
        filename_match = re.search(r'(\d{4})', filename)
        if filename_match:
            return f"2025{filename_match.group(1)}960001"
        
        return "2025307793960001"  # Consistent default 