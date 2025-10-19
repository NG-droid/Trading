# Portfolio Manager - Trade Republic

Application Python moderne pour gérer votre portefeuille d'actions Trade Republic avec focus sur le CAC 40 et le suivi des dividendes.

## Fonctionnalités

### Gestion de Portefeuille
- Suivi des transactions (achats/ventes)
- Calcul automatique du Prix de Revient Unitaire (PRU)
- Plus-values latentes et réalisées (méthode FIFO)
- Frais Trade Republic inclus (1€ par ordre)

### Dividendes
- Calendrier des dividendes
- Historique et prévisions
- Calcul du dividend yield
- Montants bruts et nets

### Fiscalité Française
- Prélèvement Forfaitaire Unique (PFU / Flat Tax 30%)
- Comparateur PFU vs Barème progressif
- Export pour déclaration fiscale
- Suivi de la CSG déductible

### Interface Moderne
- Interface CustomTkinter (mode clair/sombre)
- Dashboard avec KPIs
- Graphiques interactifs (Plotly)
- Export Excel professionnel

## Installation

### Prérequis
- Python 3.10 ou supérieur
- pip

### Installation des dépendances

```bash
cd portfolio_manager
pip install -r requirements.txt
```

## Utilisation

### Lancer l'application

```bash
python portfolio_manager/main.py
```

### Structure du projet

```
portfolio_manager/
├── main.py                 # Point d'entrée
├── config.py              # Configuration
├── requirements.txt
├── database/              # Base de données SQLite
│   ├── db_manager.py      # Gestionnaire CRUD
│   └── models.py          # Schémas et requêtes
├── api/                   # API données de marché
│   ├── market_data.py     # yfinance wrapper
│   └── dividends.py
├── core/                  # Logique métier
│   ├── portfolio.py
│   ├── calculator.py      # Calculs financiers
│   └── tax_calculator.py
├── ui/                    # Interface CustomTkinter
│   ├── main_window.py
│   ├── dashboard.py
│   ├── transactions.py
│   └── dividends_view.py
└── utils/                 # Utilitaires
    ├── export.py          # Export Excel
    ├── validators.py
    └── formatters.py
```

## Fonctionnement

### Ajouter une transaction

1. Cliquez sur "Nouvelle transaction"
2. Sélectionnez le type (Achat/Vente)
3. Entrez le ticker (ex: AI.PA pour Air Liquide)
4. Quantité et prix par action
5. Les frais (1€) sont ajoutés automatiquement

### Comprendre les calculs

#### Prix de Revient Unitaire (PRU)
```
PRU = (Somme des achats avec frais) / Nombre d'actions
```

#### Plus-value latente
```
PV latente = (Prix actuel - PRU) × Quantité détenue
```

#### Plus-value réalisée (FIFO)
Les premières actions achetées sont les premières vendues (obligatoire en France).

### Fiscalité

#### Flat Tax (PFU) - 30%
- Impôt sur le revenu : 12,8%
- Prélèvements sociaux : 17,2%

Appliqué sur :
- Les dividendes
- Les plus-values réalisées

#### Option barème progressif
Possible à la place du PFU avec :
- Abattement de 40% sur les dividendes
- Imposition selon votre tranche marginale

Le choix se fait lors de la déclaration annuelle.

## Base de données

### Tables

**transactions**
- Achats et ventes d'actions
- Calcul automatique avec frais

**dividends**
- Dividendes prévus et reçus
- Montants bruts et nets

**market_cache**
- Cache des prix actuels
- Rafraîchi toutes les 5 minutes

**price_history**
- Historique des cours
- Pour graphiques

## Export Excel

L'export génère un fichier avec plusieurs onglets :
- Résumé : Vue d'ensemble
- Transactions : Historique complet
- Dividendes : Tous les versements
- Positions : État actuel
- Fiscalité : Données pour déclaration

## Configuration

Modifiez `config.py` pour personnaliser :
- Frais de transaction
- Taux de fiscalité
- Durée du cache
- Couleurs de l'interface

## Développement

### État actuel
✅ Étape 1 - Structure et base de données : COMPLÈTE
- Configuration
- Modèles de données
- Gestionnaire de base de données
- Calculateur financier

🔄 Étape 2 - API et données de marché : EN COURS

⏳ Étape 3 - Interface utilisateur : À VENIR

### Tests

```bash
pytest
```

### Build .exe (Windows)

```bash
python build_exe.py
```

## Actions CAC 40 supportées

L'application supporte toutes les actions du CAC 40 :
- Air Liquide (AI.PA)
- Airbus (AIR.PA)
- BNP Paribas (BNP.PA)
- LVMH (MC.PA)
- L'Oréal (OR.PA)
- Sanofi (SAN.PA)
- TotalEnergies (TTE.PA)
- Et 33 autres...

Format des tickers : `[CODE].PA` pour Euronext Paris

## FAQ

### Comment importer mes transactions Trade Republic ?
Actuellement, saisie manuelle. Import CSV prévu dans une future version.

### Les données de marché sont-elles en temps réel ?
Données avec 15 minutes de délai (gratuit via yfinance). Rafraîchissement automatique toutes les 5 minutes.

### Mes données sont-elles sauvegardées ?
Oui, dans une base SQLite locale (`data/portfolio.db`). Backups automatiques disponibles.

### Puis-je utiliser d'autres actions que le CAC 40 ?
Oui, tout ticker Euronext Paris fonctionne (format XX.PA).

## Licence

Ce projet est à usage personnel. Non affilié à Trade Republic.

## Support

Pour toute question ou bug, consultez la documentation dans le dossier `docs/`.

---

**Note importante** : Cette application est un outil de suivi. Vérifiez toujours vos calculs fiscaux avec un expert-comptable ou le site officiel des impôts.
