# 🚀 Comment Lancer Portfolio Manager

## Sur Mac

### Option 1 : Interface Graphique (GUI) - Recommandé ✨

**Prérequis** : Environnement virtuel Python 3.12 configuré

1. Ouvrir le Terminal (`Cmd + Espace` → "Terminal" → `Entrée`)
2. Aller dans le dossier du projet :
   ```bash
   cd /Users/guichardnicolas/Trading
   ```
3. Lancer l'interface graphique :
   ```bash
   ./run_app_gui.sh
   ```

   Ou manuellement :
   ```bash
   source venv/bin/activate
   python run_app.py
   ```

Une belle interface graphique s'ouvre avec CustomTkinter !

### Option 2 : Interface Ligne de Commande (CLI)

Pour une utilisation rapide sans GUI :

```bash
cd /Users/guichardnicolas/Trading
python3 run_cli.py
```

Un menu interactif apparaît directement dans le Terminal.

---

## Sur Windows (Version GUI)

### Lancer l'application graphique

```bash
python3 run_app.py
```

Une fenêtre CustomTkinter s'ouvrira avec l'interface graphique moderne.

---

## 📊 Que voir dans l'application ?

L'application affiche actuellement **5 positions de test** :
- Air Liquide (AI.PA) - 10 actions
- LVMH (MC.PA) - 5 actions
- L'Oréal (OR.PA) - 8 actions
- Sanofi (SAN.PA) - 15 actions
- Danone (BN.PA) - 12 actions

**Total investi : 11 453,90€**

---

## 🎨 Fonctionnalités disponibles

### CLI (Mac) - Menu interactif
- **[1] Dashboard** - Vue d'ensemble avec métriques et top 5 positions
- **[2] Positions** - Liste complète de toutes vos positions
- **[3] Transactions** - Historique des 20 dernières transactions
- **[4] Ajouter transaction** - Ajouter un achat ou une vente
- **[5] Dividendes** - Voir tous les dividendes reçus
- **[6] Performance & Fiscalité** - Rapport détaillé
- **[7] Rafraîchir** - Mettre à jour les prix du marché
- **[8] Export Excel** - Exporter vos données (à venir)
- **[0] Quitter**

### GUI (Windows) - Interface graphique
- Dashboard avec métriques visuelles
- Navigation par onglets (sidebar à gauche)
- Bouton "Rafraîchir" pour mettre à jour les prix
- Sélecteur de thème (Dark/Light)
- Graphiques et visualisations

---

## ⚠️ Notes importantes

### Sur Mac
- **GUI** : Nécessite Python 3.12+ (installé via Homebrew) et l'environnement virtuel `venv/`
- **CLI** : Fonctionne avec Python 3.9+ système (pas besoin de venv)
- Les messages d'erreur Yahoo Finance lors du rafraîchissement sont normaux (problème réseau) - l'app utilise les données en cache

### Sur Windows
La version graphique avec CustomTkinter nécessite Python 3.9+ et fonctionnera sans problème sur Windows 10/11.

---

## 🛑 Pour fermer l'application

### CLI (Mac)
- Tapez `0` dans le menu pour quitter proprement
- Ou appuyez sur `Ctrl + C`

### GUI (Windows)
- Cliquez sur le bouton de fermeture de la fenêtre
- Ou appuyez sur `Alt + F4`

---

## 📚 Documentation complète

- `README_ETAPE2.md` - Documentation de la logique métier
- `README_ETAPE3.md` - Documentation de l'interface
- `README.md` - Vue d'ensemble du projet

---

## 🔧 En cas de problème

Si l'application ne se lance pas :

1. Vérifiez que CustomTkinter est installé :
   ```bash
   pip3 install customtkinter
   ```

2. Vérifiez que vous êtes dans le bon dossier :
   ```bash
   pwd
   # Devrait afficher : /Users/guichardnicolas/Trading
   ```

3. Vérifiez que Python 3 est installé :
   ```bash
   python3 --version
   # Devrait afficher : Python 3.9.x ou plus
   ```

---

**Bon trading ! 📊💰**
