# 🔧 Installation - Portfolio Manager

## Installation sur Mac (Pour GUI)

### Prérequis
- macOS 10.15 ou plus récent
- Homebrew installé

### Étapes d'installation

#### 1. Installer Python 3.12
```bash
brew install python@3.12
brew install python-tk@3.12
```

#### 2. Créer l'environnement virtuel
```bash
cd /Users/guichardnicolas/Trading
/opt/homebrew/bin/python3.12 -m venv venv
```

#### 3. Installer les dépendances
```bash
source venv/bin/activate
pip install --upgrade pip
pip install customtkinter yfinance openpyxl pillow
```

#### 4. Vérifier l'installation
```bash
python -c "import customtkinter; print('✅ CustomTkinter OK')"
python -c "from portfolio_manager.core.portfolio import Portfolio; print('✅ Portfolio OK')"
```

### ✅ Installation terminée !

Vous pouvez maintenant lancer l'application :
```bash
./run_app_gui.sh
```

---

## Installation sur Windows (Pour GUI)

### Prérequis
- Windows 10 ou Windows 11
- Python 3.9 ou plus récent

### Étapes d'installation

#### 1. Vérifier Python
```bash
python --version
```

Si Python n'est pas installé, téléchargez-le depuis [python.org](https://www.python.org/downloads/)

#### 2. Installer les dépendances
```bash
cd C:\path\to\Trading
pip install customtkinter yfinance openpyxl pillow
```

#### 3. Lancer l'application
```bash
python run_app.py
```

---

## Installation CLI uniquement (Mac/Windows)

Si vous voulez juste utiliser la CLI sans GUI :

### Sur Mac
```bash
cd /Users/guichardnicolas/Trading
python3 run_cli.py
```

### Sur Windows
```bash
cd C:\path\to\Trading
python run_cli.py
```

**Aucune installation supplémentaire requise** - la CLI utilise uniquement les bibliothèques Python standard !

---

## Résolution de problèmes

### Erreur "macOS 26 required"
➡️ Installer Python 3.12+ via Homebrew (voir ci-dessus)

### Erreur "No module named 'customtkinter'"
➡️ Activer l'environnement virtuel :
```bash
source venv/bin/activate
```

### Erreur Yahoo Finance
➡️ C'est normal ! L'application fonctionne avec les données en cache. Les prix seront mis à jour quand la connexion fonctionnera.

### La GUI ne se lance pas
➡️ Essayez la CLI en attendant :
```bash
python3 run_cli.py
```

---

## Structure des fichiers

```
Trading/
├── venv/                    # Environnement virtuel Python 3.12 (Mac GUI)
├── data/
│   └── portfolio.db         # Base de données SQLite
├── portfolio_manager/       # Code source
├── run_app.py              # Lancement GUI
├── run_cli.py              # Lancement CLI
├── run_app_gui.sh          # Script Mac pour GUI
└── create_test_data.py     # Créer des données de test
```

---

## Commandes utiles

### Activer l'environnement virtuel
```bash
source venv/bin/activate
```

### Désactiver l'environnement virtuel
```bash
deactivate
```

### Mettre à jour les dépendances
```bash
source venv/bin/activate
pip install --upgrade customtkinter yfinance openpyxl pillow
```

### Créer des données de test
```bash
python3 create_test_data.py
```

---

**Besoin d'aide ?** Consultez `LANCER_APP.md` pour les instructions de lancement !
