# Bank Statement Extractor - Modular Edition

🇧🇷 **Extrator Modular de Extratos Bancários com Suporte Multi-Bancos**

Uma aplicação Python modular especializada para extrair transações de extratos bancários em PDF do **Banco Inter** e **cartões de crédito Itaú**, com integração ao sistema Omie ERP e múltiplos formatos de relatórios.

---

## ⚠️ **PROJETO PRIVADO**

**🔒 Propriedade Intelectual:**  
Este projeto é de **propriedade exclusiva** e **autoria de Paulo Loureiro**.

**📝 Licença:**  
- ❌ **Uso comercial proibido** sem autorização expressa
- ❌ **Redistribuição proibida** sem permissão do autor
- ❌ **Modificação e derivação proibida** para uso comercial
- ✅ **Uso pessoal** permitido apenas para o autor

**📧 Contato do Autor:**  
**Paulo Loureiro** - Desenvolvedor e Proprietário  
*Para licenciamento comercial ou dúvidas sobre uso, entre em contato.*

---

## 🎯 **Principais Funcionalidades**

### 🏦 **Suporte Multi-Bancos**
- **🟠 Banco Inter**: Extração otimizada para extratos bancários
- **🔵 Itaú**: Extração especializada para faturas de cartão de crédito
- **🔧 Arquitetura Modular**: Fácil adição de novos bancos
- **⚡ Processamento Inteligente**: Padrões específicos para cada banco

### 🔗 **Integração Omie ERP**
- **Formato Nativo Omie**: Exportação direta no formato CSV do Omie ERP
- **Mapeamento de Campos**: Conversão automática para campos Omie:
  - `cNomeFornecedor` → Nome do fornecedor (extraído da descrição)
  - `nValorTitulo` → Valor da transação (apenas débitos)
  - `cNumeroCartao` → Número do cartão (quando disponível)
  - `cNumeroParcelas` → Informações de parcelamento
  - `cObservacao` → Detalhes de parcelas e referências
  - `dEmissao` → Data da compra (transação individual)
  - `dVencimento` → Data de vencimento da fatura

### 📊 **Tipos de Relatórios**
- **`standard`** - Relatório completo com todas as transações
- **`omie`** - Formato específico para Omie ERP 
- **`by-card`** - Agrupado por cartão de crédito
- **`by-vendor`** - Agrupado por fornecedor/vendedor
- **`by-month`** - Agrupado por mês
- **`summary`** - Resumo executivo

## 🚀 **Instalação**

### 1. **Clone o repositório**
```bash
git clone https://github.com/pu10c88/BankExtOmieERP.git
cd BankExtOmieERP
```

### 2. **Instale as dependências**
```bash
pip install -r requirements.txt
```

### 3. **Estrutura de pastas**
```
BankExtOmieERP/
├── 📁 InterStatements/        # PDFs do Banco Inter
├── 📁 ItauStataments/         # PDFs do cartão Itaú
├── 📁 output/                 # Arquivos CSV gerados
├── 🐍 BankOmieApp.py          # Aplicação principal
├── 🐍 inter_extractor.py      # Módulo específico do Inter
├── 🐍 itau_extractor.py       # Módulo específico do Itaú
└── 📄 requirements.txt        # Dependências
```

## 💻 **Como Usar**

### **🔥 NOVO: Seleção de Banco (Obrigatório)**

Agora você deve especificar qual banco usar com as flags `--inter` ou `--itau`:

```bash
# Processar extratos do Banco Inter
python3 BankOmieApp.py --inter

# Processar faturas do cartão Itaú
python3 BankOmieApp.py --itau
```

### **🎯 Integração Omie ERP**

```bash
# Omie com Banco Inter
python3 BankOmieApp.py --inter --report-type omie --invoice-date "31/12/2024"

# Omie com cartão Itaú
python3 BankOmieApp.py --itau --report-type omie --invoice-date "31/01/2025"

# Modo interativo (pergunta a data da fatura)
python3 BankOmieApp.py --inter --report-type omie
python3 BankOmieApp.py --itau --report-type omie
```

### **📊 Relatórios por Banco**

```bash
# Relatórios do Banco Inter
python3 BankOmieApp.py --inter --report-type by-vendor
python3 BankOmieApp.py --inter --report-type by-month
python3 BankOmieApp.py --inter --report-type summary

# Relatórios do cartão Itaú
python3 BankOmieApp.py --itau --report-type by-vendor
python3 BankOmieApp.py --itau --report-type by-card
python3 BankOmieApp.py --itau --report-type summary
```

### **⚙️ Opções Avançadas**

```bash
# Ver todas as opções
python3 BankOmieApp.py --help

# Modo verboso
python3 BankOmieApp.py --inter --verbose

# Pasta de entrada personalizada
python3 BankOmieApp.py --itau --input "MeusPDFs/Itau" --report-type summary

# Pasta de saída personalizada
python3 BankOmieApp.py --inter --output "Relatorios/Inter" --report-type by-vendor

# Nome de arquivo personalizado
python3 BankOmieApp.py --itau --filename "fatura_janeiro.csv"
```

## 🏗️ **Arquitetura Modular**

### **📦 Módulos Especializados**

- **`inter_extractor.py`**: Parser específico para extratos do Banco Inter
- **`itau_extractor.py`**: Parser específico para faturas do cartão Itaú
- **`BankOmieApp.py`**: Orquestrador principal com relatórios

### **🔧 Como Funciona**

```python
# Exemplo programático
from BankOmieApp import BankStatementExtractor

# Extrator do Inter
inter_extractor = BankStatementExtractor(
    statement_folder="InterStatements",
    output_folder="output",
    bank_type="inter"
)

# Extrator do Itaú
itau_extractor = BankStatementExtractor(
    statement_folder="ItauStataments", 
    output_folder="output",
    bank_type="itau"
)

# Processar arquivos
inter_transactions = inter_extractor.process_all_files()
itau_transactions = itau_extractor.process_all_files()
```

## 🏦 **Características por Banco**

### **🟠 Banco Inter**
- **Formato**: Extratos bancários em PDF
- **Padrões**: "DD de MMM. YYYY DESCRIÇÃO - R$ VALOR"
- **Tipos**: Débitos e créditos misturados
- **Cartões**: Múltiplos cartões no mesmo extrato
- **Exemplo**: `"03 de nov. 2024 MERCADOLIVRE - R$ 150,00"`

### **🔵 Itaú (Cartão de Crédito)**
- **Formato**: Faturas de cartão de crédito
- **Padrões**: "DD/MM ESTABELECIMENTO VALOR"
- **Tipos**: Principalmente débitos (compras)
- **Cartões**: Um cartão por fatura
- **Exemplo**: `"26/11 LEROY MERLIN 144,45"`

## 📋 **Formatos de Saída**

### **CSV Padrão**
```csv
date,description,amount,transaction_type,card_number,reference
03/11/2024,MERCADOLIVRE,150.00,debit,Inter-1234,Inter-extrato.pdf
26/11/2024,LEROY MERLIN,144.45,debit,Itau-0435,Itau-fatura.pdf
```

### **CSV Omie ERP**
```csv
cNomeFornecedor,nValorTitulo,cNumeroCartao,cNumeroParcelas,cObservacao,dEmissao,dVencimento
MERCADOLIVRE,150.00,1234,,Banco Inter,03/11/2024,31/12/2024
LEROY MERLIN,144.45,0435,,Cartão Itaú,26/11/2024,17/01/2025
```

## 📊 **Exemplos de Relatórios**

### **Resumo Executivo**
```
EXTRACTION SUMMARY
======================================================================
Total transactions extracted: 171
Total debits: $13523.95
Total credits: $127813.02
Net amount: $114289.07

BREAKDOWN BY CARD
======================================================================
📱 Inter-1234: Net: $125394.90 (144 transactions)
📱 Itau-0435:  Net: $-11105.83 (27 transactions)

TOP VENDOR EXPENSES
======================================================================
1. 🏪 POLOARSTR: $3222.24 (1 transactions)
2. 🏪 KALUNGA: $2063.42 (4 transactions)
3. 🏪 ENCARGOS: $1378.00 (1 transactions)
```

## 🔧 **Dependências**

```txt
pdfplumber>=0.7.0
PyPDF2>=3.0.0
```

## 📁 **Estrutura Completa do Projeto**

```
BankExtOmieERP/
├── 🎯 BankOmieApp.py                  # Aplicação principal modular
├── 🟠 inter_extractor.py              # Módulo do Banco Inter
├── 🔵 itau_extractor.py               # Módulo do cartão Itaú
├── 📖 example_usage_modular.py        # Exemplo da nova estrutura
├── 📖 example_omie_usage.py           # Exemplo Omie (legacy)
├── 📖 example_usage.py                # Exemplo básico (legacy)
├── 📊 generate_card_reports.py        # Relatórios por cartão (legacy)
├── 📦 requirements.txt                # Dependências
├── 📚 README.md                       # Documentação
├── 🔒 .gitignore                      # Arquivos ignorados
├── 📁 InterStatements/                # PDFs do Inter (não versionado)
├── 📁 ItauStataments/                 # PDFs do Itaú (não versionado)
└── 📁 output/                         # CSVs gerados (não versionado)
```

## 🆕 **Novidades da Versão Modular**

### ✅ **Melhorias**
- **Arquitetura modular**: Fácil adição de novos bancos
- **Suporte ao Itaú**: Primeiro banco adicionado
- **Flags obrigatórias**: `--inter` ou `--itau` para evitar confusão
- **Parsers especializados**: Lógica específica por banco
- **Código organizado**: Separação clara de responsabilidades

### 🔄 **Migração do Código Antigo**

Se você usava o código antigo:

```bash
# ANTIGO (não funciona mais)
python3 BankOmieApp.py --report-type omie

# NOVO (obrigatório especificar banco)
python3 BankOmieApp.py --inter --report-type omie
```

## 🚀 **Próximos Bancos**

A arquitetura modular permite fácil adição de novos bancos:

- ✅ **Banco Inter** (pronto)
- ✅ **Itaú Cartão** (pronto)
- 🔄 **Nubank** (planejado)
- 🔄 **C6 Bank** (planejado)
- 🔄 **Bradesco** (planejado)

## 🔒 **Segurança e Privacidade**

- ✅ **PDFs não versionados**: Pastas `*Statements/` excluídas do Git
- ✅ **CSVs não versionados**: Pasta `output/` excluída do Git
- ✅ **Dados locais**: Todos os dados permanecem no seu computador
- ✅ **Sem conexão externa**: Processamento 100% offline

## 🤝 **Contribuição**

Para adicionar suporte a um novo banco:

1. Crie um novo arquivo `novo_banco_extractor.py`
2. Implemente a classe `NovoBancoExtractor` 
3. Adicione as flags no `BankOmieApp.py`
4. Teste com PDFs reais do banco

## 📄 **Licença**

**© 2025 Paulo Loureiro - Todos os direitos reservados**

🔒 **Projeto Privado** - Propriedade exclusiva do autor  
❌ **Uso comercial proibido** sem autorização expressa  
❌ **Redistribuição proibida** sem permissão prévia  
✅ **Uso pessoal** limitado ao proprietário

---

**🇧🇷 Desenvolvido no Brasil para o mercado brasileiro**  
**👨‍💻 Autor: Paulo Loureiro**  
**🏦 Suporte: Banco Inter + Itaú + Arquitetura para Novos Bancos** 