# -*- coding: utf-8 -*-
"""
Script pour créer des données de test dans la base de données
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from portfolio_manager.core.portfolio import Portfolio

def create_test_data():
    """Crée des données de test pour l'application"""
    print("📊 Création des données de test...\n")

    # Créer le portfolio (utilise portfolio.db par défaut)
    portfolio = Portfolio()

    # Vérifier s'il y a déjà des transactions
    existing_transactions = portfolio.get_all_transactions()
    if len(existing_transactions) > 0:
        print(f"✅ La base de données contient déjà {len(existing_transactions)} transaction(s)")
        response = input("Voulez-vous ajouter plus de transactions ? (o/n): ")
        if response.lower() != 'o':
            print("✅ Utilisation des données existantes")
            return

    # Transactions de test
    test_transactions = [
        ("AI.PA", "Air Liquide", "ACHAT", 10, 170.50, "2024-01-15"),
        ("MC.PA", "LVMH", "ACHAT", 5, 850.00, "2024-02-01"),
        ("OR.PA", "L'Oréal", "ACHAT", 8, 420.75, "2024-02-15"),
        ("SAN.PA", "Sanofi", "ACHAT", 15, 95.30, "2024-03-01"),
        ("BN.PA", "Danone", "ACHAT", 12, 58.20, "2024-03-15"),
    ]

    print("➕ Ajout de transactions de test...\n")

    for ticker, company, type_tx, qty, price, date in test_transactions:
        try:
            tx_id = portfolio.add_transaction(
                ticker=ticker,
                company_name=company,
                transaction_type=type_tx,
                quantity=qty,
                price_per_share=price,
                transaction_date=date,
                notes="Données de test"
            )
            total = qty * price + 1  # +1€ frais
            print(f"  ✓ {company} ({ticker}): {qty} actions @ {price}€ = {total:.2f}€")
        except Exception as e:
            print(f"  ✗ Erreur pour {company}: {e}")

    print(f"\n✅ Données de test créées avec succès!")
    print(f"\n📊 Résumé:")

    # Afficher un résumé
    positions = portfolio.db.get_current_positions()
    print(f"   Positions: {len(positions)}")

    total_invested = sum(p.total_invested for p in positions)
    print(f"   Total investi: {total_invested:.2f}€")

    print(f"\n🚀 Vous pouvez maintenant lancer l'application avec:")
    print(f"   python3 run_app.py")

if __name__ == "__main__":
    create_test_data()
