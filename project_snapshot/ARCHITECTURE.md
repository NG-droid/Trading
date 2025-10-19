# Architecture de l'Application Portfolio Manager

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                    MAIN.PY (Point d'entrée)                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      UI (CustomTkinter)                     │
├─────────────────────────────────────────────────────────────┤
│  • main_window.py      (Fenêtre principale + navigation)    │
│  • dashboard.py        (KPIs, graphiques, résumé)          │
│  • transactions.py     (CRUD transactions)                  │
│  • dividends_view.py   (Calendrier, historique)            │
│  • tax_view.py         (Fiscalité, comparateur)            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    CORE (Logique métier)                    │
├─────────────────────────────────────────────────────────────┤
│  • portfolio.py        (Gestion du portefeuille)            │
│  • calculator.py       (Calculs financiers - PRU, PV, ROI)  │
│  • tax_calculator.py   (Calculs fiscaux - PFU, Barème)      │
└─────────────────────────────────────────────────────────────┘
                     │                    │
                     ▼                    ▼
┌──────────────────────────┐    ┌────────────────────────────┐
│   API (Données marché)   │    │    DATABASE (SQLite)       │
├──────────────────────────┤    ├────────────────────────────┤
│ • market_data.py         │    │ • db_manager.py (CRUD)     │
│   (yfinance wrapper)     │    │ • models.py (Schémas)      │
│                          │    │                            │
│ • dividends.py           │    │ Tables:                    │
│   (Calendrier dividendes)│    │   - transactions           │
└──────────────────────────┘    │   - dividends              │
                                │   - market_cache           │
                                │   - price_history          │
                                └────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    UTILS (Utilitaires)                      │
├─────────────────────────────────────────────────────────────┤
│  • export.py           (Export Excel multi-onglets)         │
│  • validators.py       (Validation données)                 │
│  • formatters.py       (Formatage €, dates, %)             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    CONFIG.PY (Configuration)                │
│   • Frais, taux fiscaux, paramètres, CAC 40, messages     │
└─────────────────────────────────────────────────────────────┘
```

## Flux de données

### 1. Ajout d'une transaction

```
Utilisateur (UI)
    │
    ▼ Saisie formulaire (ticker, quantité, prix, date)
transactions.py
    │
    ▼ Validation
validators.py
    │
    ▼ Création objet Transaction
models.py
    │
    ▼ Insertion base de données
db_manager.py → SQLite
    │
    ▼ Mise à jour affichage
dashboard.py (refresh KPIs)
```

### 2. Calcul de performance

```
dashboard.py
    │
    ▼ Récupération positions
db_manager.get_current_positions()
    │
    ▼ Récupération prix actuels
market_data.get_current_prices() → yfinance API
    │
    ▼ Mise en cache
db_manager.upsert_market_cache()
    │
    ▼ Calculs financiers
calculator.calculate_unrealized_pnl()
calculator.calculate_portfolio_performance()
    │
    ▼ Formatage pour affichage
formatters.format_currency()
formatters.format_percentage()
    │
    ▼ Affichage
dashboard.py (cartes KPI + graphiques)
```

### 3. Suivi des dividendes

```
dividends_view.py
    │
    ▼ Récupération positions
db_manager.get_current_positions()
    │
    ▼ Récupération calendrier dividendes
dividends.py → yfinance API
    │
    ▼ Calcul montants (brut, net après PFU)
tax_calculator.calculate_dividend_tax()
    │
    ▼ Stockage en base
db_manager.add_dividend()
    │
    ▼ Affichage calendrier
dividends_view.py (timeline + tableau)
```

### 4. Déclaration fiscale

```
tax_view.py
    │
    ▼ Sélection année fiscale
    │
    ▼ Récupération données année
db_manager.get_transactions_by_date_range()
db_manager.get_dividends_by_year()
    │
    ▼ Calcul PV réalisées (FIFO)
calculator.calculate_all_realized_pv()
    │
    ▼ Calcul impôts PFU vs Barème
tax_calculator.calculate_pfu()
tax_calculator.calculate_progressive_tax()
    │
    ▼ Génération export Excel
export.py → Excel multi-onglets
```

## Modèles de données

### Transaction
```python
{
    id: int
    ticker: str           # Ex: "AI.PA"
    company_name: str     # Ex: "Air Liquide"
    transaction_type: str # "ACHAT" ou "VENTE"
    quantity: float
    price_per_share: float
    transaction_date: str # "JJ/MM/AAAA"
    total_cost: float     # (prix × qty) ± frais
    fees: float           # 1€ (Trade Republic)
    notes: str (optional)
}
```

### Dividend
```python
{
    id: int
    ticker: str
    company_name: str
    amount_per_share: float
    ex_dividend_date: str
    payment_date: str
    quantity_owned: float
    gross_amount: float      # Montant brut
    tax_amount: float        # PFU 30%
    net_amount: float        # Net reçu
    status: str              # "PRÉVU" ou "REÇU"
    received_date: str (optional)
}
```

### Position
```python
{
    ticker: str
    company_name: str
    quantity: float
    average_buy_price: float      # PRU
    total_invested: float         # Montant investi (frais inclus)
    current_price: float
    current_value: float
    unrealized_pnl: float         # PV latente
    unrealized_pnl_percent: float
}
```

### MarketData (Cache)
```python
{
    ticker: str
    current_price: float
    previous_close: float
    change_percent: float
    volume: int
    market_cap: float
    last_updated: str  # ISO datetime
}
```

## Calculs financiers clés

### Prix de Revient Unitaire (PRU)
```
PRU = Σ(coût_achat_i) / Σ(quantité_i)

où coût_achat_i = (prix_i × qty_i) + frais_i
```

### Plus-value latente
```
PV_latente = (Prix_actuel - PRU) × Quantité_détenue
PV_latente_% = ((Prix_actuel / PRU) - 1) × 100
```

### Plus-value réalisée (FIFO)
```
1. Prendre les achats dans l'ordre chronologique
2. Pour chaque vente, "consommer" les achats les plus anciens
3. PV = Prix_vente - Prix_achat_moyen_FIFO - Frais
```

### Performance globale
```
Performance_% = ((Valeur_actuelle + Dividendes - Capital_investi) / Capital_investi) × 100
```

### Dividend Yield
```
Yield = (Dividende_annuel_par_action / Prix_actuel) × 100
```

### Fiscalité - PFU (Flat Tax)
```
Impôt_dividende = Dividende_brut × 30%
  dont:
  - Impôt sur le revenu: 12,8%
  - Prélèvements sociaux: 17,2%

Impôt_PV = Plus_value_réalisée × 30%

CSG_déductible = Impôt × 6,8%
```

## Technologies utilisées

### Backend
- **Python 3.10+** - Langage principal
- **SQLite** - Base de données locale
- **yfinance** - API données boursières (gratuit)
- **pandas** - Manipulation de données
- **dataclasses** - Modèles de données

### Frontend
- **CustomTkinter** - Interface moderne
- **Plotly** - Graphiques interactifs
- **matplotlib** - Graphiques statiques

### Utilitaires
- **openpyxl** - Export Excel
- **python-dateutil** - Gestion dates
- **PyInstaller** - Build exécutable

## Patterns de conception

### 1. Repository Pattern
`db_manager.py` agit comme un repository, abstrayant l'accès aux données.

### 2. Data Transfer Objects (DTO)
Les dataclasses (`Transaction`, `Dividend`, etc.) servent de DTOs.

### 3. Service Layer
`core/` contient la logique métier, séparée de l'UI et de la DB.

### 4. Factory Pattern
Fonctions `dict_to_*` pour créer des objets depuis les résultats SQL.

### 5. Context Manager
`db_manager.get_connection()` pour gérer les connexions SQLite.

## Sécurité et bonnes pratiques

### Base de données
- ✅ Requêtes préparées (protection SQL injection)
- ✅ Transactions atomiques
- ✅ Contraintes CHECK au niveau SQL
- ✅ Index pour performance
- ✅ Backup automatique

### Validation
- ✅ Validation des types (dataclasses)
- ✅ Validation métier (quantité > 0, date valide, etc.)
- ✅ Gestion des erreurs avec try/catch
- ✅ Messages d'erreur explicites

### Configuration
- ✅ Constantes centralisées dans config.py
- ✅ Séparation config dev/prod
- ✅ Pas de credentials en dur

### Code
- ✅ Type hints partout
- ✅ Docstrings en français
- ✅ Noms explicites
- ✅ Fonctions courtes et focalisées
- ✅ Encodage UTF-8 explicite

## Performance

### Optimisations
- **Cache** : Données de marché cachées 5 min
- **Index** : Sur ticker, date, type pour requêtes rapides
- **Batch loading** : Chargement groupé des tickers
- **Async** : Chargement asynchrone des données (UI responsive)

### Limites
- Pas de contrainte de scalabilité (usage personnel)
- SQLite suffisant (< 100 000 transactions)
- yfinance gratuit (15 min de délai)

## Évolutivité future

### Extensions possibles
- 🔮 Support d'autres brokers (Degiro, Interactive Brokers)
- 🔮 Support ETFs et cryptos
- 🔮 Import CSV automatique
- 🔮 Synchronisation cloud (Firebase, AWS)
- 🔮 Application mobile (React Native)
- 🔮 Alertes par email/SMS
- 🔮 IA pour suggestions d'investissement
- 🔮 Backtesting de stratégies

### Scalabilité
Si besoin de scale :
- SQLite → PostgreSQL
- Monolithe → Microservices
- Local → Cloud (API REST)

---

*Document d'architecture - Version 1.0*
*Correspond à l'état après l'Étape 1*
