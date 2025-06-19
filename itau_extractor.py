#!/usr/bin/env python3
"""
Itaú Bank Statement Extractor Module
Extracts transactions specifically from Itaú credit card statements.
"""

import re
from typing import List, Tuple, Dict, Any
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
        self.document_year = None  # Will be extracted from document
        
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
    
    def parse_itau_date(self, date_str: str, year: str = None, statement_date: str = None, description: str = None, installments_info: Dict[str, Any] = None) -> str:
        """
        Parse Itaú date format by calculating year from statement due date.
        Rule: For transactions DD/MM, calculate year = (due_date - 30 days).year
        Special rule: For installments, use the due date instead of original transaction date
        
        Args:
            date_str: Date string in Itaú format (e.g., "26/11")
            year: Year to append (optional, calculated if not provided)
            statement_date: Statement due date for calculation (e.g., "17/02/2025")
            description: Transaction description to detect installments
            installments_info: Data from installments section for enhanced detection
            
        Returns:
            Standardized date string (DD/MM/YYYY)
        """
        try:
            if '/' in date_str and len(date_str.split('/')) == 2:
                day, month = date_str.split('/')
                
                # Check if this is an installment transaction
                is_installment = self.is_installment_transaction(description or "", date_str, statement_date, installments_info)
                
                if is_installment and statement_date:
                    # For installments, use the due date instead of original transaction date
                    due_day, due_month, due_year = statement_date.split('/')
                    self.logger.info(f"💳 Installment detected: {date_str} → {due_day.zfill(2)}/{due_month.zfill(2)}/{due_year} (using due date {statement_date})")
                    return f"{due_day.zfill(2)}/{due_month.zfill(2)}/{due_year}"
                
                # Calculate year from statement due date (30 days back) for regular transactions
                if statement_date and '/' in statement_date:
                    billing_month, billing_year = self.calculate_billing_period(statement_date)
                    if billing_year:
                        use_year = billing_year
                        self.logger.info(f"✅ Transaction {date_str} → {day.zfill(2)}/{month.zfill(2)}/{use_year} (calculated from due date {statement_date})")
                        return f"{day.zfill(2)}/{month.zfill(2)}/{use_year}"
                
                # Use provided year as fallback
                if year:
                    use_year = int(year)
                    self.logger.debug(f"✅ Transaction {date_str} using provided year: {use_year}")
                    return f"{day.zfill(2)}/{month.zfill(2)}/{use_year}"
                
                # Final fallback
                elif self.document_year:
                    use_year = int(self.document_year)
                    self.logger.warning(f"⚠️ Transaction {date_str} using fallback document year: {use_year}")
                else:
                    from datetime import datetime
                    use_year = datetime.now().year
                    self.logger.warning(f"⚠️ Transaction {date_str} using fallback current year: {use_year}")
                
                return f"{day.zfill(2)}/{month.zfill(2)}/{use_year}"
                
        except Exception as e:
            self.logger.debug(f"Error parsing Itaú date '{date_str}': {e}")
        
        return date_str
    
    def is_installment_transaction(self, description: str, date_str: str = None, statement_date: str = None, installments_info: Dict[str, Any] = None) -> bool:
        """
        Detect if a transaction is an installment based on its description, context, and installments section data.
        
        Args:
            description: Transaction description
            date_str: Transaction date (DD/MM format)
            statement_date: Statement due date for context
            installments_info: Data from installments section (if available)
            
        Returns:
            True if this appears to be an installment transaction
        """
        if not description:
            return False
        
        # PRIORITY 1: Check if we have installments section data and this transaction matches known future installments
        if installments_info and installments_info.get('total_future_installments', 0) > 0:
            # If we have a significant amount of future installments, be more aggressive in detection
            # This indicates this statement has many installments
            future_total = installments_info.get('total_future_installments', 0)
            if future_total > 1000:  # Significant installment activity
                self.logger.debug(f"🎯 High installment activity detected (${future_total:.2f} future), using enhanced detection")
        
        # PRIORITY 2: Look for explicit installment patterns like "06/06", "04/21", "12/24", etc.
        installment_patterns = [
            r'\b\d{2}/\d{2}\b',  # XX/YY pattern (e.g., "06/06", "04/21")
        ]
        
        for pattern in installment_patterns:
            if re.search(pattern, description):
                return True
        
        # PRIORITY 3: If transaction date is significantly older than statement period, 
        # it's likely an installment (e.g., transaction from September appearing in February statement)
        if date_str and statement_date:
            try:
                from datetime import datetime
                
                # Parse transaction date
                trans_day, trans_month = date_str.split('/')
                trans_month = int(trans_month)
                
                # Parse statement date  
                due_day, due_month, due_year = statement_date.split('/')
                due_month = int(due_month)
                
                # Calculate billing period (30 days back from due date)
                from datetime import timedelta
                billing_date = datetime(int(due_year), int(due_month), int(due_day)) - timedelta(days=30)
                billing_month = billing_date.month
                
                # If transaction month is more than 2 months before billing period, likely installment
                # Handle year wrap-around (e.g., Nov 2024 transaction in Feb 2025 statement)
                if billing_month >= trans_month:
                    month_diff = billing_month - trans_month
                else:
                    # For wrap-around cases (e.g., Nov->Feb), calculate properly
                    month_diff = billing_month + (12 - trans_month)
                
                # Enhanced logic: if we have high installment activity, be more sensitive
                threshold = 2  # Default threshold
                if installments_info and installments_info.get('total_future_installments', 0) > 5000:
                    threshold = 1  # More sensitive for high-installment statements
                
                if month_diff >= threshold:
                    return True
                    
            except (ValueError, IndexError):
                pass
        
        return False
    
    def extract_year_from_text(self, text: str, filename: str) -> str:
        """
        Extract year for transactions from statement text or filename.
        Priority: filename > transaction context > document headers
        
        Args:
            text: Raw text from PDF
            filename: Name of the source file
            
        Returns:
            Year as string for transactions
        """
        # PRIORITY 1: Extract year from filename (most reliable for transaction year)
        filename_year = None
        
        # Pattern like "FATURA_17_11_24.pdf" -> 2024
        filename_match = re.search(r'_(\d{2})\.pdf$', filename)
        if filename_match:
            year_suffix = filename_match.group(1)
            if int(year_suffix) >= 20 and int(year_suffix) <= 30:
                filename_year = f"20{year_suffix}"
                self.logger.info(f"Using transaction year from filename: {filename_year}")
                return filename_year
        
        # Pattern like "2024_fatura.pdf"
        filename_match = re.search(r'(20[2-3]\d)', filename)
        if filename_match:
            filename_year = filename_match.group(1)
            self.logger.info(f"Using transaction year from filename: {filename_year}")
            return filename_year
        
        # PRIORITY 2: Look for transaction context years (not document headers)
        years_found = []
        
        # Look for years in transaction context (avoid headers)
        transaction_year_patterns = [
            # Avoid header patterns like "Vencimento:", "Emissão:", "Postagem:"
            r'(?<!Vencimento:\s)\d{2}/\d{2}/(\d{4})',  # Avoid after "Vencimento:"
            r'(?<!Emissão:\s)\d{2}/\d{2}/(\d{4})',     # Avoid after "Emissão:"
            r'(?<!Postagem:\s)\d{2}/\d{2}/(\d{4})',    # Avoid after "Postagem:"
        ]
        
        for pattern in transaction_year_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                valid_years = [y for y in matches if 2020 <= int(y) <= 2030]
                years_found.extend(valid_years)
        
        # PRIORITY 3: Use document headers as last resort
        if not years_found:
            header_patterns = [
                r'Vencimento:\s*\d{2}/\d{2}/(\d{4})',
                r'Emissão:\s*\d{2}/\d{2}/(\d{4})',
                r'Data\s+de\s+vencimento:\s*\d{2}/\d{2}/(\d{4})',
            ]
            
            for pattern in header_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    valid_years = [y for y in matches if 2020 <= int(y) <= 2030]
                    years_found.extend(valid_years)
                    break  # Use first header found
        
        # If we found years in content, use them
        if years_found:
            # For transaction years, prefer the EARLIER year (transactions are usually from previous months)
            unique_years = list(set(years_found))
            if len(unique_years) > 1:
                # If we have multiple years, prefer the earlier one for transactions
                transaction_year = str(min(int(y) for y in unique_years))
                self.logger.info(f"Multiple years found {unique_years}, using earlier year for transactions: {transaction_year}")
                return transaction_year
            else:
                transaction_year = unique_years[0]
                self.logger.info(f"Using transaction year from content: {transaction_year}")
                return transaction_year
        
        # Ultimate fallback: current year - 1 (transactions are usually from previous periods)
        from datetime import datetime
        current_year = datetime.now().year
        fallback_year = str(current_year - 1)
        self.logger.warning(f"Could not determine transaction year, using previous year: {fallback_year}")
        return fallback_year
    
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
    
    def extract_statement_date(self, text: str) -> str:
        """
        Extract statement/billing date from text and calculate billing period.
        
        Args:
            text: Raw text from PDF
            
        Returns:
            Statement date string or None
        """
        # Look for common statement date patterns
        date_patterns = [
            r'Com\s+vencimento\s+em:\s*(\d{2}/\d{2}/\d{4})',  # "Com vencimento em: 17/02/2025"
            r'Vencimento:\s*(\d{2}/\d{2}/\d{4})',
            r'Data\s+de\s+vencimento:\s*(\d{2}/\d{2}/\d{4})',
            r'Emissão:\s*(\d{2}/\d{2}/\d{4})',
            r'(\d{2}/\d{2}/\d{4})\s+Flexível',  # From the pattern we saw
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date = match.group(1)
                self.logger.debug(f"Found statement date: {date}")
                return date
        
        self.logger.debug("No statement date found in text")
        return None
    
    def calculate_billing_period(self, due_date: str) -> tuple:
        """
        Calculate the billing period based on due date.
        Itaú billing period is 30 days before the due date.
        
        Args:
            due_date: Due date string (DD/MM/YYYY)
            
        Returns:
            Tuple of (billing_month, billing_year)
        """
        try:
            from datetime import datetime, timedelta
            
            day, month, year = due_date.split('/')
            due_date_obj = datetime(int(year), int(month), int(day))
            
            # Calculate 30 days before due date
            billing_date = due_date_obj - timedelta(days=30)
            billing_month = billing_date.month
            billing_year = billing_date.year
            
            self.logger.debug(f"Due date: {due_date} → 30 days back: {billing_date.strftime('%d/%m/%Y')} → Billing period: {billing_month:02d}/{billing_year}")
            return billing_month, billing_year
            
        except (ValueError, IndexError) as e:
            self.logger.warning(f"Could not parse due date: {due_date} - {e}")
            return None, None
    
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
        Itaú organizes transactions by card sections.
        
        Args:
            text: Raw text from PDF
            filename: Name of the source file
            
        Returns:
            List of Transaction objects
        """
        transactions = []
        lines = text.split('\n')
        
        # Extract document year first and store it
        self.document_year = self.extract_year_from_text(text, filename)
        year = self.document_year
        
        # Extract statement date for context and calculate the year for ALL transactions in this document
        statement_date = self.extract_statement_date(text)
        document_transaction_year = None
        
        if statement_date:
            self.logger.info(f"📅 Statement due date detected: {statement_date}")
            billing_month, billing_year = self.calculate_billing_period(statement_date)
            if billing_month and billing_year:
                document_transaction_year = billing_year  # All transactions in this document use this year
                self.logger.info(f"📊 Billing period calculated: {billing_month:02d}/{billing_year}")
                self.logger.info(f"🎯 ALL transactions in this document will use year: {document_transaction_year}")
        
        # Extract installments section for additional context
        installments_info = self.extract_installments_section(text)
        # Store statement date in installments info for validation
        if statement_date:
            installments_info['statement_date'] = statement_date
        
        # Track current card number and transactions section
        current_card_number = None
        in_transactions_section = False
        current_transaction_data = None
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Check for card section headers
            card_section_match = re.search(r'Cartão\s+(\d{4}\.XXXX\.XXXX\.\d{4})', line, re.IGNORECASE)
            if card_section_match:
                current_card_number = f"Itau-{card_section_match.group(1)}"
                self.logger.debug(f"Found card section: {current_card_number}")
                i += 1
                continue
            
            # Check for card references in transaction sections
            card_ref_match = re.search(r'Lançamentos.*final\s+(\d{4})', line, re.IGNORECASE)
            if card_ref_match:
                current_card_number = f"Itau-XXXX.XXXX.XXXX.{card_ref_match.group(1)}"
                self.logger.debug(f"Found card reference: {current_card_number}")
                i += 1
                continue
            
            # Check for person name with card reference
            person_card_match = re.search(r'([A-Z\s]+)\(final\s+(\d{4})\)', line, re.IGNORECASE)
            if person_card_match:
                card_final = person_card_match.group(2)
                current_card_number = f"Itau-XXXX.XXXX.XXXX.{card_final}"
                self.logger.debug(f"Found person card reference: {current_card_number}")
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
                        # Parse date using statement due date to calculate year
                        parsed_date = self.parse_itau_date(date_str, None, statement_date, description, installments_info)
                        
                        # Use current card number or fallback to generic extraction
                        card_number = current_card_number or self.extract_card_number(text, filename)
                        
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
                                    parsed_date = self.parse_itau_date(date_str, None, statement_date, description, installments_info)
                                    
                                    # Use current card number or fallback to generic extraction
                                    card_number = current_card_number or self.extract_card_number(text, filename)
                                    
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
                                        parsed_date = self.parse_itau_date(date_str, None, statement_date, description, installments_info)
                                        
                                        # Use current card number or fallback to generic extraction
                                        card_number = current_card_number or self.extract_card_number(text, filename)
                                        
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
        
        # Validate installment detection using installments section data
        self.validate_installment_detection(transactions, installments_info)
        
        self.logger.info(f"Extracted {len(transactions)} transactions from Itaú statement: {filename}")
        return transactions
    
    def extract_installments_section(self, text: str) -> Dict[str, Any]:
        """
        Extract installment information from the dedicated installments section.
        This provides additional context for installment detection.
        
        Args:
            text: Raw text from PDF
            
        Returns:
            Dictionary with installment information
        """
        installments_info = {
            'installments_found': [],
            'next_invoice_total': 0.0,
            'future_invoices_total': 0.0,
            'total_future_installments': 0.0
        }
        
        lines = text.split('\n')
        in_installments_section = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for the installments section marker
            if 'Comprasparceladas-próximasfaturas' in line:
                in_installments_section = True
                self.logger.info(f"📋 Found installments section: {line}")
                continue
            
            if in_installments_section:
                # Look for summary totals
                if 'Próximafatura' in line:
                    # Extract next invoice total
                    amount_match = re.search(r'([\d.,]+)', line)
                    if amount_match:
                        try:
                            amount = float(amount_match.group(1).replace('.', '').replace(',', '.'))
                            installments_info['next_invoice_total'] = amount
                            self.logger.info(f"💰 Next invoice installments: ${amount:.2f}")
                        except ValueError:
                            pass
                
                elif 'Demaisfaturas' in line:
                    # Extract future invoices total
                    amount_match = re.search(r'([\d.,]+)', line)
                    if amount_match:
                        try:
                            amount = float(amount_match.group(1).replace('.', '').replace(',', '.'))
                            installments_info['future_invoices_total'] = amount
                            self.logger.info(f"💰 Future invoices installments: ${amount:.2f}")
                        except ValueError:
                            pass
                
                elif 'Totalparapróximasfaturas' in line:
                    # Extract total future installments
                    amount_match = re.search(r'([\d.,]+)', line)
                    if amount_match:
                        try:
                            amount = float(amount_match.group(1).replace('.', '').replace(',', '.'))
                            installments_info['total_future_installments'] = amount
                            self.logger.info(f"💰 Total future installments: ${amount:.2f}")
                        except ValueError:
                            pass
                    # End of installments section
                    break
                
                # Look for individual installment entries (before the section header)
                elif re.search(r'\d{2}/\d{2}.*\d+,\d{2}.*Comprasparceladas', line):
                    # This is an installment transaction that leads to the section
                    installment_match = re.match(r'(\d{2}/\d{2})\s+(.+?)\s+([\d.,]+)', line)
                    if installment_match:
                        date_str = installment_match.group(1)
                        description = installment_match.group(2).replace('Comprasparceladas-próximasfaturas', '').strip()
                        amount_str = installment_match.group(3)
                        
                        try:
                            amount = float(amount_str.replace('.', '').replace(',', '.'))
                            installments_info['installments_found'].append({
                                'date': date_str,
                                'description': description,
                                'amount': amount
                            })
                            self.logger.info(f"📦 Individual installment: {date_str} {description} ${amount:.2f}")
                        except ValueError:
                            pass
        
        if installments_info['installments_found'] or installments_info['total_future_installments'] > 0:
            self.logger.info(f"✅ Installments section analysis complete:")
            self.logger.info(f"   - Individual installments found: {len(installments_info['installments_found'])}")
            self.logger.info(f"   - Total future installments: ${installments_info['total_future_installments']:.2f}")
        
        return installments_info
    
    def validate_installment_detection(self, transactions: List[Transaction], installments_info: Dict[str, Any]) -> None:
        """
        Validate our installment detection against the installments section data.
        This helps ensure our logic is working correctly.
        
        Args:
            transactions: List of extracted transactions
            installments_info: Data from installments section
        """
        if not installments_info or installments_info.get('total_future_installments', 0) == 0:
            return
        
        # Count detected installments
        installment_count = 0
        installment_total = 0.0
        regular_count = 0
        regular_total = 0.0
        
        for transaction in transactions:
            # Check if this transaction was marked as installment (using due date)
            if transaction.date and len(transaction.date.split('/')) == 3:
                trans_date = transaction.date.split('/')
                # If transaction date matches due date, it was treated as installment
                due_parts = installments_info.get('statement_date', '').split('/')
                if len(due_parts) == 3 and trans_date[0] == due_parts[0] and trans_date[1] == due_parts[1]:
                    installment_count += 1
                    installment_total += transaction.amount
                else:
                    regular_count += 1
                    regular_total += transaction.amount
        
        future_total = installments_info.get('total_future_installments', 0)
        
        self.logger.info(f"🔍 INSTALLMENT VALIDATION:")
        self.logger.info(f"   📦 Detected installments: {installment_count} transactions (${installment_total:.2f})")
        self.logger.info(f"   ✅ Regular transactions: {regular_count} transactions (${regular_total:.2f})")
        self.logger.info(f"   📊 Future installments from section: ${future_total:.2f}")
        
        # Calculate ratio for validation
        if future_total > 0:
            current_ratio = (installment_total / future_total) * 100 if future_total > 0 else 0
            self.logger.info(f"   📈 Current vs Future ratio: {current_ratio:.1f}%")
            
            if current_ratio > 50:
                self.logger.info(f"   ⚠️  High current installment ratio - many installments in this period")
            elif current_ratio < 10:
                self.logger.info(f"   ✅ Low current installment ratio - mostly regular transactions") 