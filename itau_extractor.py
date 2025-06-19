#!/usr/bin/env python3
"""
Itaú Bank Statement Extractor Module
Extracts transactions specifically from Itaú credit card statements.
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


class ItauExtractor:
    """Extractor specific for Itaú credit card statements."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Itaú credit card statement patterns
        # Format: DD/MM ESTABLISHMENT VALUE
        self.transaction_patterns = [
            # Main pattern: "DD/MM ESTABLISHMENT VALUE"
            r'(\d{2}/\d{2})\s+(.+?)\s+([\d,]+)',
            # Alternative pattern with more context
            r'(\d{2}/\d{2})\s+(.+?)\s+(\d+,\d{2})',
            # Pattern for transactions spanning multiple lines
            r'(\d{2}/\d{2})\s+(.+?)$',
        ]
        
        # Categories found in Itaú statements
        self.categories = [
            'ALIMENTAÇÃO', 'EDUCAÇÃO', 'VESTUÁRIO', 'SAÚDE', 'TURISMO E ENTRETENIM',
            'DIVERSOS', 'HOBBY', 'TRANSPORTE'
        ]
        
        # Patterns to identify transaction types (most Itaú transactions are debits/expenses)
        self.debit_keywords = ['COMPRA', 'SAQUE', 'ANUIDADE', 'JUROS', 'MULTA', 'IOF', 'ENCARGO']
        self.credit_keywords = ['PAGAMENTO', 'CREDITO', 'ESTORNO', 'DEVOLUÇÃO']
    
    def parse_amount(self, amount_str: str) -> Tuple[float, str]:
        """
        Parse amount string for Itaú format.
        
        Args:
            amount_str: String representation of amount (Brazilian format with comma)
            
        Returns:
            Tuple of (amount as float, transaction_type)
        """
        original_amount = amount_str.strip()
        
        # Check for negative sign (indicating credit/refund)
        is_credit = False
        if original_amount.startswith('-'):
            is_credit = True
            amount_str = amount_str.replace('-', '').strip()
        
        # Handle Brazilian currency format
        # Example: "1.234,56" should become "1234.56"
        if ',' in amount_str:
            if '.' in amount_str:
                # Format like "1.234,56" - dot is thousands separator, comma is decimal
                amount_str = amount_str.replace('.', '').replace(',', '.')
            else:
                # Format like "1234,56" - comma is decimal separator
                amount_str = amount_str.replace(',', '.')
        
        try:
            amount = float(amount_str)
            # Most Itaú transactions are expenses (debits), credits are rare
            transaction_type = 'credit' if is_credit else 'debit'
            return amount, transaction_type
        except ValueError:
            self.logger.warning(f"Could not parse amount: {original_amount} -> {amount_str}")
            return 0.0, 'unknown'
    
    def parse_itau_date(self, date_str: str, year: str = "2025") -> str:
        """
        Parse Itaú date format to a standard format.
        
        Args:
            date_str: Date string in Itaú format (e.g., "26/11")
            year: Year to append (extracted from statement context)
            
        Returns:
            Standardized date string (DD/MM/YYYY)
        """
        try:
            if '/' in date_str and len(date_str.split('/')) == 2:
                day, month = date_str.split('/')
                return f"{day.zfill(2)}/{month.zfill(2)}/{year}"
        except Exception as e:
            self.logger.debug(f"Error parsing Itaú date '{date_str}': {e}")
        
        return date_str
    
    def extract_year_from_text(self, text: str) -> str:
        """
        Extract year from statement text.
        
        Args:
            text: Raw text from PDF
            
        Returns:
            Year as string
        """
        # Look for year patterns in typical Itaú statement contexts
        year_patterns = [
            r'Vencimento:\s*\d{2}/\d{2}/(\d{4})',
            r'Emissão:\s*\d{2}/\d{2}/(\d{4})',
            r'(\d{4})',  # Fallback to any 4-digit number
        ]
        
        for pattern in year_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Return the most recent year found
                years = [int(y) for y in matches if 2020 <= int(y) <= 2030]
                if years:
                    return str(max(years))
        
        return "2025"  # Default fallback
    
    def extract_card_number(self, text: str, filename: str) -> str:
        """
        Extract card number from Itaú statement.
        
        Args:
            text: Raw text from PDF
            filename: Name of the source file
            
        Returns:
            Card number or identifier
        """
        # Itaú card number patterns
        card_patterns = [
            r'Cartão\s+(\d{4}\.XXXX\.XXXX\.\d{4})',
            r'(\d{4}\.XXXX\.XXXX\.\d{4})',
            r'final\s+(\d{4})',
        ]
        
        for pattern in card_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"Itau-{match.group(1)}"
        
        # Extract from filename if available
        filename_match = re.search(r'(\d{4})', filename)
        if filename_match:
            return f"Itau-{filename_match.group(1)}"
        
        return "Itau-Default"
    
    def clean_description(self, description: str) -> str:
        """
        Clean and normalize transaction description.
        
        Args:
            description: Raw description
            
        Returns:
            Cleaned description
        """
        # Remove extra spaces and common patterns
        description = re.sub(r'\s+', ' ', description).strip()
        
        # Remove category suffixes if present
        for category in self.categories:
            if description.endswith(f' {category}'):
                description = description[:-len(f' {category}')].strip()
        
        # Remove location patterns like ".SAO PAULO"
        description = re.sub(r'\.[A-Z\s]+$', '', description).strip()
        
        # Remove card reference patterns
        description = re.sub(r'-CT\s+\w+', '', description).strip()
        description = re.sub(r'\s+\d{2}/\d{2}$', '', description).strip()
        
        return description
    
    def extract_transactions_from_text(self, text: str, filename: str) -> List[Transaction]:
        """
        Extract transactions from Itaú statement text.
        
        Args:
            text: Raw text from PDF
            filename: Name of the source file
            
        Returns:
            List of Transaction objects
        """
        transactions = []
        lines = text.split('\n')
        
        # Extract year and card number
        year = self.extract_year_from_text(text)
        card_number = self.extract_card_number(text, filename)
        
        # Track if we're in a transactions section
        in_transactions_section = False
        current_transaction_data = None
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Check if we're entering a transactions section
            if 'Lançamentos:' in line or 'DATA ESTABELECIMENTO VALOR' in line:
                in_transactions_section = True
                i += 1
                continue
            
            # Check if we're leaving transactions section
            if any(section in line for section in ['Limites de crédito', 'Encargos cobrados', 'Resumo da fatura']):
                in_transactions_section = False
                i += 1
                continue
            
            if in_transactions_section:
                # Try to match transaction patterns
                
                # Pattern 1: Full transaction on one line (DD/MM ESTABLISHMENT VALUE)
                match = re.match(r'(\d{2}/\d{2})\s+(.+?)\s+([\d.,]+)$', line)
                if match:
                    date_str = match.group(1)
                    description = match.group(2)
                    amount_str = match.group(3)
                    
                    # Clean description
                    description = self.clean_description(description)
                    
                    # Skip if description is too short or contains unwanted patterns
                    if len(description) < 3 or any(skip in description.upper() 
                                                  for skip in ['FINAL', 'CARTÃO', 'TOTAL', 'SALDO']):
                        i += 1
                        continue
                    
                    # Parse amount
                    amount, transaction_type = self.parse_amount(amount_str)
                    
                    if amount > 0:
                        # Parse date
                        parsed_date = self.parse_itau_date(date_str, year)
                        
                        # Create transaction
                        transaction = Transaction(
                            date=parsed_date,
                            description=description,
                            amount=amount,
                            transaction_type=transaction_type,
                            card_number=card_number,
                            reference=f"Itau-{filename}"
                        )
                        
                        transactions.append(transaction)
                        self.logger.debug(f"Extracted transaction: {transaction}")
                
                # Pattern 2: Transaction with possible continuation on next line
                elif re.match(r'(\d{2}/\d{2})\s+(.+)$', line):
                    match = re.match(r'(\d{2}/\d{2})\s+(.+)$', line)
                    date_str = match.group(1)
                    description_part = match.group(2)
                    
                    # Check if next line has amount or more description
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        
                        # Check if next line is just an amount
                        amount_match = re.match(r'^([\d.,]+)$', next_line)
                        if amount_match:
                            amount_str = amount_match.group(1)
                            description = self.clean_description(description_part)
                            
                            if len(description) >= 3:
                                amount, transaction_type = self.parse_amount(amount_str)
                                
                                if amount > 0:
                                    parsed_date = self.parse_itau_date(date_str, year)
                                    
                                    transaction = Transaction(
                                        date=parsed_date,
                                        description=description,
                                        amount=amount,
                                        transaction_type=transaction_type,
                                        card_number=card_number,
                                        reference=f"Itau-{filename}"
                                    )
                                    
                                    transactions.append(transaction)
                                    self.logger.debug(f"Extracted multi-line transaction: {transaction}")
                            
                            i += 1  # Skip next line as we processed it
                        
                        # Check if next line continues the description
                        elif not re.match(r'^\d{2}/\d{2}', next_line) and len(next_line) > 0:
                            # Look for amount in the continuation line
                            continued_line = description_part + " " + next_line
                            amount_in_continued = re.search(r'([\d.,]+)$', continued_line)
                            
                            if amount_in_continued:
                                amount_str = amount_in_continued.group(1)
                                description = continued_line[:amount_in_continued.start()].strip()
                                description = self.clean_description(description)
                                
                                if len(description) >= 3:
                                    amount, transaction_type = self.parse_amount(amount_str)
                                    
                                    if amount > 0:
                                        parsed_date = self.parse_itau_date(date_str, year)
                                        
                                        transaction = Transaction(
                                            date=parsed_date,
                                            description=description,
                                            amount=amount,
                                            transaction_type=transaction_type,
                                            card_number=card_number,
                                            reference=f"Itau-{filename}"
                                        )
                                        
                                        transactions.append(transaction)
                                        self.logger.debug(f"Extracted continued transaction: {transaction}")
                                
                                i += 1  # Skip next line as we processed it
            
            i += 1
        
        self.logger.info(f"Extracted {len(transactions)} transactions from Itaú statement: {filename}")
        return transactions 