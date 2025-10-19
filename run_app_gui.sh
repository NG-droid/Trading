#!/bin/bash
# Script pour lancer l'interface graphique avec Python 3.12

echo "🚀 Lancement de Portfolio Manager (GUI)..."
echo "📦 Activation de l'environnement virtuel Python 3.12..."

# Activer l'environnement virtuel
source venv/bin/activate

# Lancer l'application
python run_app.py

# Désactiver l'environnement virtuel à la fin
deactivate
