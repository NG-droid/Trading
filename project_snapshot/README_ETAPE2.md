# Portfolio Manager - Étape 2 COMPLÉTÉE ✅

## Vue d'ensemble

Application Python de gestion de portefeuille Trade Republic avec support complet de la fiscalité française.

**Statut Étape 2** : ✅ **100% COMPLÉTÉE**

---

## Architecture Complète

```
portfolio_manager/
├── config.py                      # Configuration centralisée (CAC 40, taux, etc.)
├── database/
│   ├── __init__.py
│   ├── models.py                  # Modèles de données (Transaction, Dividend, Position)
│   └── db_manager.py              # Gestionnaire SQLite avec CRUD complet
├── api/
│   ├── __init__.py
│   ├── market_data.py             # Wrapper yfinance avec cache intelligent
│   └── dividends.py               # Gestion des dividendes et estimations
├── core/
│   ├── __init__.py
│   ├── calculator.py              # Calculs FIFO pour plus-values
│   ├── tax_calculator.py          # Calculs fiscaux (PFU vs Barème)
│   └── portfolio.py               # Classe Portfolio principale (orchestration)
└── utils/
    ├── __init__.py
    ├── validators.py              # Validation des entrées utilisateur
    └── formatters.py              # Formatage français (€, %, dates)
```

---

## Fonctionnalités Implémentées

### 1. **Base de Données SQLite** ✅

- ✅ Table `transactions` (achats/ventes avec frais Trade Republic 1€)
- ✅ Table `dividends` (prévus et reçus avec calcul fiscal)
- ✅ Table `market_cache` (cache 5 minutes pour prix)
- ✅ Table `price_history` (historique pour graphiques)
- ✅ CRUD complet avec context managers
- ✅ Backup/restore automatique

**Test** : `portfolio_manager/main.py`

### 2. **API Market Data (yfinance)** ✅

- ✅ Récupération prix en temps réel (Euronext Paris .PA)
- ✅ Cache intelligent (5 minutes)
- ✅ Batch loading pour optimisation
- ✅ Historique des prix (1j à 10 ans)
- ✅ Informations entreprises (secteur, industrie)
- ✅ Validation des tickers

**Fichier** : `portfolio_manager/api/market_data.py` (415 lignes)

### 3. **API Dividendes** ✅

- ✅ Récupération historique dividendes (yfinance)
- ✅ Estimation prochains dividendes (fréquence automatique)
- ✅ Calcul dividend yield
- ✅ Synchronisation automatique par position
- ✅ Calendrier des dividendes (30/60/90 jours)
- ✅ Résumés annuels et mensuels

**Fichier** : `portfolio_manager/api/dividends.py` (441 lignes)

### 4. **Calculs Fiscaux Français** ✅

#### PFU (Prélèvement Forfaitaire Unique - Flat Tax 30%)
- ✅ Impôt sur le revenu : 12,8%
- ✅ Prélèvements sociaux : 17,2%
- ✅ CSG déductible : 6,8%

#### Barème Progressif
- ✅ Abattement 40% sur dividendes
- ✅ Tranches 2024 : 0%, 11%, 30%, 41%, 45%
- ✅ Comparaison PFU vs Barème
- ✅ Calcul automatique du TMI

#### IFU (Imprimé Fiscal Unique)
- ✅ Case 2DC (dividendes FR)
- ✅ Case 2AB (dividendes étrangers)
- ✅ Case 2CG (plus-values)
- ✅ Case 2BH (PV nettes après imputation)
- ✅ Case 6DE (CSG déductible)

**Fichier** : `portfolio_manager/core/tax_calculator.py` (354 lignes)

### 5. **Calculs FIFO (Plus-Values)** ✅

- ✅ Méthode FIFO obligatoire (France)
- ✅ Calcul automatique du PRU (Prix de Revient Unitaire)
- ✅ Tracking des transactions utilisées
- ✅ Gestion des moins-values
- ✅ ROI et performances

**Fichier** : `portfolio_manager/core/calculator.py` (424 lignes)

### 6. **Classe Portfolio (Orchestration)** ✅

```python
from portfolio_manager.core.portfolio import Portfolio

portfolio = Portfolio()

# Ajouter une transaction
tx_id = portfolio.add_transaction(
    ticker="AI.PA",
    company_name="Air Liquide",
    transaction_type="ACHAT",
    quantity=10,
    price_per_share=170.50,
    transaction_date="2024-01-15"
)

# Récupérer positions avec prix temps réel
positions = portfolio.get_current_positions()

# Snapshot complet du portefeuille
snapshot = portfolio.get_portfolio_snapshot()
print(f"Valeur : {snapshot.current_value}€")
print(f"P&L : {snapshot.total_gain_loss}€ ({snapshot.total_gain_loss_percent}%)")

# Rapport fiscal annuel
tax_report = portfolio.get_annual_tax_report(2024, marginal_tax_rate=30)

# Données IFU pour déclaration
ifu_data = portfolio.get_ifu_data(2024)
```

**Fichier** : `portfolio_manager/core/portfolio.py` (547 lignes)

### 7. **Validateurs** ✅

- ✅ Validation tickers (.PA obligatoire)
- ✅ Validation quantités (min/max)
- ✅ Validation prix (min/max)
- ✅ Validation dates (formats multiples)
- ✅ Validation complète transactions
- ✅ Sanitization des chaînes

**Fichier** : `portfolio_manager/utils/validators.py` (328 lignes)

### 8. **Formatters Français** ✅

```python
format_currency(1234.56)      # "1 234,56€"
format_percentage(5.23)       # "+5,23%"
format_date("2024-01-15")     # "15/01/2024"
format_gain_loss(125.50)      # "+125,50€"
```

**Fichier** : `portfolio_manager/utils/formatters.py` (290 lignes)

---

## Tests Validés ✅

### Script de test offline
```bash
python3 test_etape2_offline.py
```

**Résultats** :
- ✅ **9/9 tests passés** avec succès
- ✅ Base de données SQLite
- ✅ Validateurs (tickers, prix, quantités, dates)
- ✅ Formatters (devise, pourcentages, dates)
- ✅ Calculateur FIFO (plus-values)
- ✅ Calculateur fiscal (PFU vs Barème)
- ✅ Tranches d'imposition 2024
- ✅ Résumé fiscal annuel
- ✅ Données IFU pour déclaration
- ✅ Requêtes et statistiques

---

## Configuration (config.py)

### Trade Republic
- Frais par ordre : **1€** (achat et vente)
- Pas de frais de garde
- CAC 40 uniquement (38 tickers disponibles)

### Fiscalité Française
```python
FLAT_TAX_RATE = 0.30           # PFU 30%
INCOME_TAX_RATE = 0.128        # Impôt sur le revenu
SOCIAL_TAX_RATE = 0.172        # Prélèvements sociaux
CSG_DEDUCTIBLE_RATE = 0.068    # CSG déductible
DIVIDEND_ALLOWANCE_RATE = 0.40 # Abattement dividendes
```

### Cache & API
- Cache durée : **5 minutes**
- API timeout : **10 secondes**
- Source données : **yfinance** (gratuit)

---

## Dépendances

```bash
pip install yfinance pandas
```

**Fichier complet** : `portfolio_manager/requirements.txt`

---

## Exemples d'Utilisation

### 1. Créer un portefeuille et ajouter des transactions

```python
from portfolio_manager.core.portfolio import Portfolio

portfolio = Portfolio("mon_portfolio.db")

# Acheter des actions
portfolio.add_transaction(
    ticker="AI.PA",
    company_name="Air Liquide",
    transaction_type="ACHAT",
    quantity=10,
    price_per_share=170.50,
    transaction_date="2024-01-15"
)

portfolio.add_transaction(
    ticker="MC.PA",
    company_name="LVMH",
    transaction_type="ACHAT",
    quantity=5,
    price_per_share=850.00,
    transaction_date="2024-02-01"
)
```

### 2. Consulter ses positions

```python
positions = portfolio.get_current_positions()

for pos in positions:
    print(f"{pos.company_name} ({pos.ticker})")
    print(f"  Quantité: {pos.quantity}")
    print(f"  PRU: {pos.pru}€")
    print(f"  Prix actuel: {pos.current_price}€")
    print(f"  Valeur: {pos.current_value}€")
    print(f"  P&L: {pos.unrealized_gain_loss}€ ({pos.unrealized_gain_loss_percent}%)")
```

### 3. Gérer les dividendes

```python
# Synchroniser tous les dividendes
portfolio.sync_all_dividends()

# Dividendes à venir
upcoming = portfolio.get_upcoming_dividends(days_ahead=30)

for div in upcoming:
    print(f"{div.company_name}: {div.gross_amount}€ brut le {div.ex_dividend_date}")

# Résumé annuel
summary = portfolio.get_dividend_summary(2024)
print(f"Total net: {summary['total_net']}€")
```

### 4. Rapport fiscal annuel

```python
# Générer le rapport fiscal
tax_report = portfolio.get_annual_tax_report(
    year=2024,
    marginal_tax_rate=30  # TMI 30%
)

# Revenus
revenus = tax_report['tax_summary']['revenus']
print(f"Dividendes: {revenus['dividendes_bruts']}€")
print(f"Plus-values: {revenus['plus_values_nettes']}€")

# Impôts PFU
pfu = tax_report['tax_summary']['pfu']
print(f"Total impôt PFU: {pfu['total_impot']}€")
print(f"Total net: {pfu['total_net']}€")

# Données IFU
ifu = portfolio.get_ifu_data(2024)
print(f"Case 2DC (dividendes): {ifu['case_2DC']}€")
print(f"Case 2CG (PV): {ifu['case_2CG']}€")
```

### 5. Calculs fiscaux comparatifs

```python
from portfolio_manager.core.tax_calculator import TaxCalculator

gross_dividend = 5000

# PFU
pfu = TaxCalculator.calculate_pfu_dividend(gross_dividend)
print(f"PFU 30%: {pfu.net_amount}€ net (impôt {pfu.tax_amount}€)")

# Barème progressif (TMI 30%)
progressive = TaxCalculator.calculate_progressive_tax_dividend(gross_dividend, 30)
print(f"Barème: {progressive.net_amount}€ net (impôt {progressive.tax_amount}€)")

# Comparaison
comparison = TaxCalculator.compare_pfu_vs_progressive(gross_dividend, 30)
print(f"Meilleure option: {comparison['best_option']}")
print(f"Économie: {comparison['savings']}€")
```

---

## Statistiques du Projet

### Lignes de Code
- **Total : ~3 600 lignes** de code Python
- config.py : 203 lignes
- models.py : 460 lignes
- db_manager.py : 530 lignes
- calculator.py : 424 lignes
- market_data.py : 415 lignes
- dividends.py : 441 lignes
- tax_calculator.py : 354 lignes
- portfolio.py : 547 lignes
- validators.py : 328 lignes
- formatters.py : 290 lignes

### Fonctionnalités
- ✅ **8 modules** principaux
- ✅ **50+ fonctions** et méthodes
- ✅ **10 dataclasses** pour les modèles
- ✅ **4 tables** SQL avec indexes
- ✅ **38 tickers** CAC 40 pré-configurés
- ✅ **100% conforme** fiscalité française 2024

---

## Prochaines Étapes

### Étape 3 : Interface CustomTkinter (À venir)
- [ ] Interface graphique moderne (dark/light mode)
- [ ] Dashboard avec métriques temps réel
- [ ] Graphiques (Plotly/Matplotlib)
- [ ] Formulaires d'ajout de transactions
- [ ] Calendrier des dividendes visuel
- [ ] Export Excel pour déclarations
- [ ] Multi-onglets (Portfolio, Dividendes, Fiscal)

### Étape 4 : Tests et Packaging (À venir)
- [ ] Tests unitaires (pytest)
- [ ] Tests d'intégration
- [ ] Build .exe avec PyInstaller
- [ ] Documentation utilisateur
- [ ] Guide d'installation

---

## Support et Contribution

**Développé avec** :
- Python 3.10+
- yfinance (données de marché gratuites)
- SQLite (base de données locale)
- Dataclasses (modèles de données)

**Conforme à** :
- Fiscalité française 2024
- Réglementation CAC 40
- Normes Trade Republic

---

## Licence

Ce projet est un outil personnel de gestion de portefeuille.

**Note** : Les calculs fiscaux sont fournis à titre informatif. Consultez toujours un expert-comptable pour votre déclaration fiscale officielle.

---

## Changelog

### v0.2.0 - Étape 2 (2025-10-17)
- ✅ API yfinance wrapper complet
- ✅ Gestion des dividendes et estimations
- ✅ Calculs fiscaux (PFU vs Barème progressif)
- ✅ Classe Portfolio orchestration
- ✅ Validateurs et formatters
- ✅ Tests offline validés (9/9)

### v0.1.0 - Étape 1 (2025-10-17)
- ✅ Architecture de base
- ✅ Base de données SQLite
- ✅ Modèles de données
- ✅ Calculateur FIFO
- ✅ Configuration CAC 40

---

**Statut Global** : 🟢 Étape 2 complétée à 100%

**Prochaine étape** : Étape 3 - Interface utilisateur CustomTkinter
