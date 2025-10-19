# État du Projet - Portfolio Manager

## Résumé

**Application de gestion de portefeuille Trade Republic** - Version 0.1 (Étape 1 complète)

25 fichiers Python créés - ~1700 lignes de code

## Étape 1 : Structure et Base de Données ✅ COMPLÈTE

### Fichiers créés

#### Configuration
- `config.py` - Toutes les constantes de l'application
  - Frais Trade Republic (1€ par ordre)
  - Fiscalité française (PFU 30%, CSG, etc.)
  - Paramètres API, cache, interface
  - Liste complète des tickers CAC 40
  - Messages d'erreur et de succès

#### Base de données (`database/`)
- `models.py` - Modèles de données et schémas SQL
  - Dataclasses: Transaction, Dividend, MarketData, Position, PriceHistory
  - Tables: transactions, dividends, market_cache, price_history
  - Requêtes SQL préparées (classe Queries)
  - Fonctions de conversion dict → objets

- `db_manager.py` - Gestionnaire CRUD complet
  - CRUD transactions (add, get, update, delete)
  - CRUD dividendes
  - Cache des données de marché
  - Statistiques et analyses
  - Backup et restauration
  - Context manager pour connexions SQLite

#### Logique métier (`core/`)
- `calculator.py` - Calculateur financier
  - Prix de Revient Unitaire (PRU)
  - Plus-values latentes
  - Plus-values réalisées (méthode FIFO)
  - Performance globale du portefeuille
  - Dividend yield
  - Break-even price
  - Validation des transactions

- `portfolio.py` - (vide, à implémenter)
- `tax_calculator.py` - (vide, à implémenter)

#### API (`api/`)
- `market_data.py` - (vide, à implémenter)
- `dividends.py` - (vide, à implémenter)

#### Interface (`ui/`)
- Tous les fichiers créés mais vides (à implémenter)
  - `main_window.py`
  - `dashboard.py`
  - `transactions.py`
  - `dividends_view.py`
  - `tax_view.py`

#### Utilitaires (`utils/`)
- `export.py` - (vide, à implémenter)
- `validators.py` - (vide, à implémenter)
- `formatters.py` - (vide, à implémenter)

#### Point d'entrée
- `main.py` - Version de test qui :
  - Affiche l'état du projet
  - Teste la connexion à la base de données
  - Affiche les statistiques

#### Autres
- `requirements.txt` - Toutes les dépendances
- `build_exe.py` - (vide, à créer)
- `README.md` - Documentation complète

### Tests effectués

✅ Application lance sans erreur
✅ Base de données s'initialise correctement
✅ Tables créées avec succès
✅ Encodage UTF-8 corrigé sur tous les fichiers

### Fonctionnalités implémentées

#### Base de données
- [x] Schéma complet des 4 tables
- [x] Index pour optimisation des requêtes
- [x] CRUD complet pour transactions
- [x] CRUD complet pour dividendes
- [x] Système de cache pour données de marché
- [x] Requêtes d'analyse (positions, statistiques)
- [x] Backup/Restauration automatique

#### Calculs financiers
- [x] Prix de Revient Unitaire (PRU) pondéré
- [x] Plus-values latentes (montant + %)
- [x] Plus-values réalisées FIFO (conforme fiscalité FR)
- [x] Performance globale du portefeuille
- [x] Dividend yield
- [x] Poids des positions
- [x] ROI
- [x] Break-even price
- [x] Validation des ventes (quantité suffisante)

#### Configuration
- [x] Tous les paramètres de l'app
- [x] Frais Trade Republic
- [x] Taux de fiscalité française
- [x] Liste CAC 40 complète
- [x] Messages multilingues

## Étape 2 : API et Données de Marché 🔄 À FAIRE

### À implémenter

#### `api/market_data.py`
- [ ] Wrapper yfinance pour récupération des prix
- [ ] Gestion du cache (5 min)
- [ ] Mode hors ligne
- [ ] Gestion des erreurs API
- [ ] Batch loading des tickers
- [ ] Historique des prix

#### `api/dividends.py`
- [ ] Récupération du calendrier des dividendes
- [ ] Calcul des montants bruts/nets
- [ ] Prévisions basées sur historique
- [ ] Dates ex-dividende et paiement

#### `core/portfolio.py`
- [ ] Classe Portfolio principale
- [ ] Gestion des positions
- [ ] Agrégation des données de marché
- [ ] Calculs de performance temps réel

#### `core/tax_calculator.py`
- [ ] Calcul PFU (30%)
- [ ] Calcul barème progressif
- [ ] Comparateur PFU vs Barème
- [ ] CSG déductible
- [ ] Export pour IFU

#### `utils/validators.py`
- [ ] Validation des tickers
- [ ] Validation des dates
- [ ] Validation des montants
- [ ] Validation des quantités

#### `utils/formatters.py`
- [ ] Formatage des montants (€)
- [ ] Formatage des dates (JJ/MM/AAAA)
- [ ] Formatage des pourcentages
- [ ] Formatage pour affichage

## Étape 3 : Interface Utilisateur ⏳ À FAIRE

### À implémenter

#### `ui/main_window.py`
- [ ] Fenêtre principale CustomTkinter
- [ ] Navigation par onglets
- [ ] Mode clair/sombre
- [ ] Barre de menu

#### `ui/dashboard.py`
- [ ] Cartes KPI (valeur, performance, PV, dividendes)
- [ ] Graphique évolution portefeuille
- [ ] Camembert répartition
- [ ] Top/Bottom performers
- [ ] Prochains dividendes

#### `ui/transactions.py`
- [ ] Formulaire ajout transaction
- [ ] Tableau des transactions
- [ ] Filtres et tri
- [ ] Édition/Suppression
- [ ] Export Excel

#### `ui/dividends_view.py`
- [ ] Calendrier visuel
- [ ] Tableau des dividendes
- [ ] Statistiques annuelles
- [ ] Graphique évolution mensuelle

#### `ui/tax_view.py`
- [ ] Sélecteur d'année
- [ ] Résumé fiscal
- [ ] Comparateur PFU/Barème
- [ ] Export déclaration

#### `utils/export.py`
- [ ] Export Excel multi-onglets
- [ ] Mise en forme professionnelle
- [ ] Export PDF (bonus)

## Étape 4 : Tests et Build 📦 À FAIRE

### Tests
- [ ] Tests unitaires (pytest)
- [ ] Tests d'intégration
- [ ] Tests de l'interface
- [ ] Coverage > 80%

### Build
- [ ] Script PyInstaller
- [ ] Création .exe Windows
- [ ] Inclusion des assets
- [ ] Tests du .exe

## Installation actuelle

```bash
# Cloner ou télécharger le projet
cd portfolio_manager

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application (version test)
python main.py
```

## Structure du projet

```
portfolio_manager/
├── main.py                 ✅ Point d'entrée (test)
├── config.py              ✅ Configuration complète
├── requirements.txt       ✅ Dépendances
├── build_exe.py           ⏳ À créer
├── data/                  ✅ Base de données SQLite
├── database/              ✅ CRUD complet
│   ├── db_manager.py
│   └── models.py
├── api/                   ⏳ À implémenter
│   ├── market_data.py
│   └── dividends.py
├── core/                  ✅ Calculateur (⏳ autres)
│   ├── portfolio.py
│   ├── calculator.py      ✅
│   └── tax_calculator.py
├── ui/                    ⏳ À implémenter
│   ├── main_window.py
│   ├── dashboard.py
│   ├── transactions.py
│   ├── dividends_view.py
│   └── tax_view.py
└── utils/                 ⏳ À implémenter
    ├── export.py
    ├── validators.py
    └── formatters.py
```

## Prochaines étapes recommandées

### Priorité 1 : Fonctionnalités de base
1. Implémenter `api/market_data.py` (yfinance)
2. Implémenter `utils/validators.py`
3. Implémenter `utils/formatters.py`
4. Créer interface basique transactions

### Priorité 2 : Interface complète
5. Dashboard avec KPIs
6. Graphiques
7. Gestion dividendes
8. Module fiscalité

### Priorité 3 : Polish et déploiement
9. Tests
10. Build .exe
11. Documentation utilisateur

## Notes importantes

### Encodage
Tous les fichiers Python ont l'en-tête `# -*- coding: utf-8 -*-` pour supporter les caractères accentués français.

### Base de données
La base SQLite est créée automatiquement dans `data/portfolio.db` au premier lancement.

### Calculs FIFO
Le calculateur implémente la méthode FIFO (First In First Out) obligatoire en France pour les plus-values.

### Fiscalité
Les taux sont configurables dans `config.py` :
- PFU : 30% (12.8% IR + 17.2% prélèvements sociaux)
- CSG déductible : 6.8%

## Estimation du temps restant

- **Étape 2** (API et données) : 4-6 heures
- **Étape 3** (Interface UI) : 10-15 heures
- **Étape 4** (Tests et build) : 3-4 heures

**Total estimé** : 17-25 heures de développement

---

*Dernière mise à jour : Étape 1 complète*
*Prêt pour l'étape 2*
