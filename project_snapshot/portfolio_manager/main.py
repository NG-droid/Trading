# -*- coding: utf-8 -*-
"""
Portfolio Manager - Application de gestion de portefeuille Trade Republic
Point d'entrée principal de l'application
"""

import sys
import os
from pathlib import Path

# Ajouter le dossier parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# TODO: Importer l'interface graphique une fois créée
# from portfolio_manager.ui.main_window import MainWindow


def main():
    """
    Point d'entrée principal de l'application
    """
    print("=" * 60)
    print("Portfolio Manager - Trade Republic")
    print("Application de gestion de portefeuille d'actions")
    print("=" * 60)
    print()

    # Pour l'instant, afficher un message
    # L'interface CustomTkinter sera créée dans les prochaines étapes
    print("Application en cours de développement...")
    print()
    print("Étape 1 - Structure et base de données : Complète")
    print("Étape 2 - API et données de marché : En cours")
    print("Étape 3 - Interface utilisateur : À venir")
    print()
    print("Structure du projet créée avec succès !")
    print()

    # Test de connexion à la base de données
    try:
        from portfolio_manager.database.db_manager import DatabaseManager
        from portfolio_manager.config import DB_PATH, DB_NAME

        print(f"Test de connexion à la base de données...")
        print(f"Chemin: {DB_PATH}{DB_NAME}")

        db = DatabaseManager()
        stats = db.get_database_stats()

        print("Base de données initialisée avec succès")
        print(f"  - Transactions: {stats['transactions_count']}")
        print(f"  - Dividendes: {stats['dividends_count']}")
        print(f"  - Positions: {stats['positions_count']}")
        print(f"  - Taille DB: {stats['db_size_mb']:.2f} MB")
        print()

    except Exception as e:
        print("Erreur lors de l'initialisation de la base de données:")
        print(f"  {e}")
        print()

    # TODO: Lancer l'interface graphique
    # app = MainWindow()
    # app.mainloop()


if __name__ == "__main__":
    main()
