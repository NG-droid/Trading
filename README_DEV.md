# 🛠️ Guide de Développement - Portfolio Manager

## 📋 Architecture Multi-Plateforme

Ce projet propose **deux interfaces** pour le même moteur de gestion de portefeuille :

### 1️⃣ CLI (Command Line Interface) - Pour Mac
**Fichier:** `run_cli.py`

- ✅ Compatible avec toutes les versions de macOS
- ✅ Ne dépend pas de CustomTkinter
- ✅ Parfait pour le développement et les tests
- ✅ Interface complète en mode texte

**Utilisation:**
```bash
python3 run_cli.py
```

### 2️⃣ GUI (Graphical User Interface) - Pour Windows
**Fichier:** `run_app.py`

- ✅ Interface graphique moderne avec CustomTkinter
- ✅ Optimisée pour Windows 10/11
- ✅ Graphiques et visualisations
- ✅ Expérience utilisateur premium

**Utilisation:**
```bash
python3 run_app.py
```

---

## 🏗️ Structure du Projet

```
Trading/
│
├── portfolio_manager/           # Package principal
│   ├── core/                    # Logique métier
│   │   ├── portfolio.py         # Gestionnaire de portefeuille
│   │   ├── fifo_calculator.py   # Calculs FIFO
│   │   └── tax_calculator.py    # Calculs fiscaux
│   │
│   ├── database/                # Couche données
│   │   ├── db_manager.py        # Gestionnaire SQLite
│   │   └── models.py            # Modèles de données
│   │
│   ├── api/                     # APIs externes
│   │   └── market_data.py       # yfinance wrapper
│   │
│   ├── ui/                      # Interface GUI (Windows)
│   │   ├── main_window.py       # Fenêtre principale
│   │   ├── dashboard.py         # Dashboard
│   │   └── ...                  # Autres onglets
│   │
│   ├── utils/                   # Utilitaires
│   │   ├── formatters.py        # Formatage
│   │   └── validators.py        # Validation
│   │
│   └── config.py                # Configuration globale
│
├── data/                        # Base de données SQLite
│   └── portfolio.db
│
├── run_cli.py                   # 🖥️  CLI pour Mac
├── run_app.py                   # 🪟 GUI pour Windows
├── run_app_tkinter.py           # Alternative Tkinter (legacy)
└── create_test_data.py          # Données de test
```

---

## 🎯 Stratégie de Développement

### Phase 1 : Développement sur Mac ✅
- Utiliser `run_cli.py` pour développer et tester
- Toutes les fonctionnalités sont accessibles via la CLI
- Tests de la logique métier et des calculs

### Phase 2 : Implémentation GUI (en cours)
- Développer l'interface CustomTkinter dans `portfolio_manager/ui/`
- Sera testée et finalisée sur Windows
- Partage le même code métier que la CLI

### Phase 3 : Fonctionnalités Avancées
- [ ] Graphiques avec Plotly/Matplotlib
- [ ] Export Excel complet
- [ ] Alertes et notifications
- [ ] Import automatique depuis Trade Republic

---

## 🔧 Développement Local

### Sur Mac (recommandé pour le dev)

1. **Lancer la CLI:**
   ```bash
   python3 run_cli.py
   ```

2. **Créer des données de test:**
   ```bash
   python3 create_test_data.py
   ```

3. **Tester les modifications:**
   - Modifier le code dans `portfolio_manager/`
   - Relancer la CLI pour tester
   - Toutes les modifications sont immédiatement visibles

### Sur Windows (pour tester la GUI)

1. **Installer les dépendances:**
   ```bash
   pip install customtkinter yfinance
   ```

2. **Lancer la GUI:**
   ```bash
   python3 run_app.py
   ```

---

## 📊 Fonctionnalités Disponibles

| Fonctionnalité | CLI (Mac) | GUI (Windows) | Statut |
|----------------|-----------|---------------|--------|
| Dashboard | ✅ | ✅ | Complet |
| Positions | ✅ | 🚧 | En cours |
| Transactions | ✅ | 🚧 | En cours |
| Ajouter transaction | ✅ | 🚧 | En cours |
| Dividendes | ✅ | 🚧 | En cours |
| Performance & Fiscalité | ✅ | 🚧 | En cours |
| Rafraîchir prix | ✅ | ✅ | Complet |
| Export Excel | 🚧 | 🚧 | À venir |
| Graphiques | ❌ | 🚧 | À venir |

**Légende:**
- ✅ Complet et fonctionnel
- 🚧 En développement
- ❌ Pas encore commencé

---

## 🧪 Tests

### Tester une nouvelle fonctionnalité

1. **Ajouter la logique métier** dans `portfolio_manager/core/`
2. **Tester via la CLI** (`run_cli.py`) sur Mac
3. **Implémenter dans la GUI** (`portfolio_manager/ui/`) pour Windows
4. **Valider sur Windows** avec `run_app.py`

### Données de test

Le script `create_test_data.py` crée 5 positions de test :
- Air Liquide (AI.PA)
- LVMH (MC.PA)
- L'Oréal (OR.PA)
- Sanofi (SAN.PA)
- Danone (BN.PA)

Total investi : ~11 453,90€

---

## 🚀 Prochaines Étapes

1. **Terminer les onglets GUI** (Portfolio, Transactions, Dividendes, Fiscalité)
2. **Implémenter l'export Excel** complet
3. **Ajouter des graphiques** (évolution portefeuille, répartition sectorielle)
4. **Créer un installeur Windows** (.exe avec PyInstaller)
5. **Ajouter l'import CSV** depuis Trade Republic

---

## 📚 Documentation

- `README.md` - Vue d'ensemble du projet
- `README_ETAPE2.md` - Documentation de la logique métier
- `README_ETAPE3.md` - Documentation de l'interface
- `LANCER_APP.md` - Guide de lancement
- `README_DEV.md` - Ce fichier (guide développement)

---

## 💡 Conseils

### Pour développer efficacement
- Utilisez la CLI sur Mac pour tester rapidement les modifications
- Le code métier dans `portfolio_manager/core/` est partagé entre CLI et GUI
- Modifiez `config.py` pour ajuster les paramètres globaux

### Pour déboguer
- La CLI affiche les erreurs directement dans le terminal
- Activez `DEBUG_MODE = True` dans `config.py` pour plus de logs
- Consultez `portfolio_manager.log` pour les erreurs

### Avant de commit
- Vérifier que la CLI fonctionne sur Mac
- Vérifier que la GUI se lance sans erreur (même si fonctionnalité incomplète)
- Mettre à jour ce README si ajout de nouvelles fonctionnalités

---

**Happy coding! 🚀📊**
