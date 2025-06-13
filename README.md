# OmieERP Bank Statement BR

🇧🇷 **Extrator de Extratos Bancários com Integração Omie ERP**

Uma aplicação Python especializada para extrair transações de extratos bancários em PDF do Banco Inter e exportar diretamente para o sistema Omie ERP, além de outros formatos de relatórios.

## 🎯 **Principais Funcionalidades**

### 🏦 **Extração de Dados Bancários**
- **Suporte ao Banco Inter**: Extração otimizada para PDFs do Banco Inter
- **Processamento em Lote**: Processa múltiplos arquivos PDF simultaneamente
- **Reconhecimento Inteligente**: Identifica automaticamente padrões de transações
- **Classificação Automática**: Separa débitos e créditos automaticamente

### 🔗 **Integração Omie ERP**
- **Formato Nativo Omie**: Exportação direta no formato CSV do Omie ERP
- **Mapeamento de Campos**: Conversão automática para campos Omie:
  - `cNomeFornecedor` → Nome do fornecedor (extraído da descrição)
  - `nValorTitulo` → Valor da transação (apenas débitos)
  - `cNumeroCartao` → Número do cartão (quando disponível)
  - `cNumeroParcelas` → Informações de parcelamento
  - `cObservacao` → "Fatura do Banco Inter" + detalhes de parcelas
  - `dEmissao` → Data da compra (transação individual)
  - `dVencimento` → Data de vencimento da fatura
- **Detecção de Parcelas**: Identifica automaticamente informações de parcelamento
- **Extração de Fornecedores**: Limpa e padroniza nomes de fornecedores

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
├── 📁 InterStatements/     # Coloque seus PDFs do Banco Inter aqui
├── 📁 output/              # Arquivos CSV gerados
├── 🐍 BankOmieApp.py       # Aplicação principal
└── 📄 requirements.txt     # Dependências
```

## 💻 **Como Usar**

### **🎯 Integração Omie ERP (Recomendado)**

```bash
# Exportação direta para Omie ERP
python3 BankOmieApp.py --report-type omie --invoice-date "31/12/2024"

# Com nome de arquivo personalizado
python3 BankOmieApp.py --report-type omie --invoice-date "31/12/2024" --filename "fatura_dezembro.csv"

# Modo interativo (pergunta a data da fatura)
python3 BankOmieApp.py --report-type omie
```

### **📊 Outros Tipos de Relatório**

```bash
# Relatório por cartão
python3 BankOmieApp.py --report-type by-card

# Relatório por fornecedor
python3 BankOmieApp.py --report-type by-vendor

# Relatório por mês
python3 BankOmieApp.py --report-type by-month

# Resumo executivo
python3 BankOmieApp.py --report-type summary

# Relatório padrão (todas as transações)
python3 BankOmieApp.py --report-type standard
```

### **⚙️ Opções Avançadas**

```bash
# Ver todas as opções
python3 BankOmieApp.py --help

# Modo verboso (mais detalhes)
python3 BankOmieApp.py --report-type omie --invoice-date "31/12/2024" --verbose

# Pasta de entrada personalizada
python3 BankOmieApp.py --input "MinhasPastas/Extratos" --report-type omie --invoice-date "31/12/2024"

# Pasta de saída personalizada
python3 BankOmieApp.py --output "Relatorios" --report-type omie --invoice-date "31/12/2024"
```

## 📋 **Formato CSV Omie ERP**

O arquivo CSV gerado para o Omie ERP contém as seguintes colunas:

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| `cNomeFornecedor` | Nome do fornecedor | "MERCADOLIVRE" |
| `nValorTitulo` | Valor da transação | "150.00" |
| `cNumeroCartao` | Número do cartão | "1234" |
| `cNumeroParcelas` | Info de parcelas | "4/10" |
| `cObservacao` | Observações | "Fatura do Banco Inter - Parcela 4/10" |
| `dEmissao` | Data da compra | "15/12/2024" |
| `dVencimento` | Data de vencimento | "31/12/2024" |

## 🔧 **Dependências**

- **Python 3.7+**
- **pdfplumber** - Extração de texto de PDFs
- **PyPDF2** - Processamento alternativo de PDFs
- **pandas** - Manipulação de dados
- **re** - Expressões regulares (built-in)

## 📁 **Estrutura do Projeto**

```
BankExtOmieERP/
├── BankOmieApp.py              # 🎯 Aplicação principal
├── example_omie_usage.py       # 📖 Exemplo de uso Omie
├── example_usage.py            # 📖 Exemplo básico
├── generate_card_reports.py    # 📊 Relatórios por cartão
├── requirements.txt            # 📦 Dependências
├── README.md                   # 📚 Documentação
├── .gitignore                  # 🔒 Arquivos ignorados
├── InterStatements/            # 📁 PDFs do banco (não versionado)
└── output/                     # 📁 CSVs gerados (não versionado)
```

## 🔒 **Segurança e Privacidade**

- ✅ **PDFs não versionados**: Pasta `InterStatements/` excluída do Git
- ✅ **CSVs não versionados**: Pasta `output/` excluída do Git
- ✅ **Dados locais**: Todos os dados permanecem no seu computador
- ✅ **Sem conexão externa**: Processamento 100% offline

## 🤝 **Contribuição**

Este é um projeto privado. Para sugestões ou melhorias, entre em contato diretamente.

## 📄 **Licença**

Projeto privado - Todos os direitos reservados.

---

**🇧🇷 Desenvolvido no Brasil para o mercado brasileiro**  
**🏦 Especializado em Banco Inter + Omie ERP** 