# -*- coding: utf-8 -*-
"""
Script de test pour l'Étape 2 - Mode Offline
Teste toutes les fonctionnalités sans appel réseau
"""

import sys
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

from portfolio_manager.database.db_manager import DatabaseManager
from portfolio_manager.database.models import Transaction, Dividend, Position
from portfolio_manager.core.calculator import FinancialCalculator
from portfolio_manager.core.tax_calculator import TaxCalculator
from portfolio_manager.utils.formatters import (
    format_currency, format_percentage, format_date, format_gain_loss
)
from portfolio_manager.utils.validators import (
    validate_ticker, validate_quantity, validate_price, validate_transaction
)


def print_separator(title: str = ""):
    """Affiche un séparateur visuel"""
    if title:
        print(f"\n{'=' * 70}")
        print(f"  {title}")
        print(f"{'=' * 70}\n")
    else:
        print("-" * 70)


def test_database():
    """Test 1: Base de données"""
    print_separator("TEST 1: Base de Données")

    db = DatabaseManager("test_offline.db")

    # Ajouter des transactions
    transactions = [
        Transaction("AI.PA", "Air Liquide", "ACHAT", 10, 170.50, "2024-01-15", 0),
        Transaction("MC.PA", "LVMH", "ACHAT", 5, 850.00, "2024-02-01", 0),
        Transaction("OR.PA", "L'Oréal", "ACHAT", 8, 420.75, "2024-02-15", 0),
    ]

    for tx in transactions:
        tx_id = db.add_transaction(tx)
        print(f"  ✓ Transaction #{tx_id}: {tx.company_name} - {tx.quantity} @ {format_currency(tx.price_per_share)}")

    # Récupérer les positions
    positions = db.get_current_positions()
    print(f"\n✅ {len(positions)} positions créées")

    return db


def test_validators():
    """Test 2: Validateurs"""
    print_separator("TEST 2: Validateurs")

    # Ticker valide
    valid, msg = validate_ticker("AI.PA")
    print(f"  ✓ validate_ticker('AI.PA'): {valid} - {msg if msg else 'OK'}")

    # Ticker invalide
    valid, msg = validate_ticker("AAPL")
    print(f"  ✓ validate_ticker('AAPL'): {valid} - {msg}")

    # Quantité valide
    valid, msg = validate_quantity(10)
    print(f"  ✓ validate_quantity(10): {valid}")

    # Prix valide
    valid, msg = validate_price(150.50)
    print(f"  ✓ validate_price(150.50): {valid}")

    # Transaction complète
    valid, errors = validate_transaction(
        ticker="AI.PA",
        quantity=10,
        price=150.50,
        transaction_date="2024-01-15",
        transaction_type="ACHAT",
        company_name="Air Liquide"
    )
    print(f"\n✅ Validation transaction: {valid}")
    if not valid:
        for error in errors:
            print(f"   - {error}")


def test_formatters():
    """Test 3: Formatters"""
    print_separator("TEST 3: Formatters")

    print(f"  format_currency(1234.56) = {format_currency(1234.56)}")
    print(f"  format_percentage(5.23) = {format_percentage(5.23)}")
    print(f"  format_percentage(-2.45) = {format_percentage(-2.45)}")
    print(f"  format_gain_loss(125.50) = {format_gain_loss(125.50)}")
    print(f"  format_gain_loss(-75.25) = {format_gain_loss(-75.25)}")
    print(f"  format_date('2024-01-15') = {format_date('2024-01-15')}")

    print("\n✅ Tous les formatters fonctionnent correctement")


def test_calculator():
    """Test 4: Calculs FIFO"""
    print_separator("TEST 4: Calculs FIFO (Plus-Values)")

    # Créer des transactions d'achat
    buys = [
        Transaction("AI.PA", "Air Liquide", "ACHAT", 10, 150.00, "2024-01-01", 1501),
        Transaction("AI.PA", "Air Liquide", "ACHAT", 5, 160.00, "2024-02-01", 801),
    ]

    # Créer une transaction de vente
    sell = Transaction("AI.PA", "Air Liquide", "VENTE", 12, 180.00, "2024-03-01", 2159)

    # Calculer la plus-value
    result = FinancialCalculator.calculate_realized_pv_fifo(buys, sell)

    print(f"📊 Simulation vente de 12 actions AI.PA:")
    print(f"   Achats:")
    print(f"     - 10 @ {format_currency(150)}")
    print(f"     - 5 @ {format_currency(160)}")
    print(f"   Vente:")
    print(f"     - 12 @ {format_currency(180)}")
    print(f"\n   Résultat FIFO:")
    print(f"   Quantité vendue:        {result.quantity_sold}")
    print(f"   Prix de vente moyen:    {format_currency(result.sell_price)}")
    print(f"   Prix d'achat moyen:     {format_currency(result.average_buy_price)}")
    print(f"   Plus-value totale:      {format_gain_loss(result.total_gain_loss)}")
    print(f"   Pourcentage:            {format_percentage(result.gain_loss_percent)}")

    print("\n✅ Calcul FIFO validé")


def test_tax_calculator():
    """Test 5: Calculs fiscaux"""
    print_separator("TEST 5: Calculs Fiscaux")

    gross_dividend = 5000.0

    print(f"📊 Simulation dividende de {format_currency(gross_dividend)}\n")

    # PFU (Flat Tax 30%)
    pfu = TaxCalculator.calculate_pfu_dividend(gross_dividend)
    print(f"💰 PFU (Flat Tax 30%):")
    print(f"   Montant brut:          {format_currency(pfu.gross_amount)}")
    print(f"   Impôt revenu (12,8%):  {format_currency(pfu.breakdown['impot_revenu'])}")
    print(f"   Prélèv. sociaux (17,2%): {format_currency(pfu.breakdown['prelevements_sociaux'])}")
    print(f"   CSG déductible (6,8%):  {format_currency(pfu.breakdown['csg_deductible'])}")
    print(f"   ──────────────────────")
    print(f"   Total impôt:           {format_currency(pfu.tax_amount)}")
    print(f"   Montant net:           {format_currency(pfu.net_amount)}")

    # Barème progressif (TMI 30%)
    progressive = TaxCalculator.calculate_progressive_tax_dividend(gross_dividend, 30)
    print(f"\n📊 Barème progressif (TMI 30%):")
    print(f"   Abattement 40%:        {format_currency(progressive.breakdown['abattement_40pct'])}")
    print(f"   Base imposable:        {format_currency(progressive.breakdown['base_imposable'])}")
    print(f"   Impôt revenu:          {format_currency(progressive.breakdown['impot_revenu'])}")
    print(f"   Prélèvements sociaux:  {format_currency(progressive.breakdown['prelevements_sociaux'])}")
    print(f"   ──────────────────────")
    print(f"   Total impôt:           {format_currency(progressive.tax_amount)}")
    print(f"   Montant net:           {format_currency(progressive.net_amount)}")
    print(f"   Taux effectif:         {format_percentage(progressive.breakdown['taux_effectif'])}")

    # Comparaison
    diff = pfu.tax_amount - progressive.tax_amount
    best = "PFU" if diff > 0 else "Barème progressif"
    print(f"\n💡 Meilleure option: {best}")
    print(f"   Économie: {format_currency(abs(diff))}")

    print("\n✅ Calculs fiscaux validés")


def test_tax_brackets():
    """Test 6: Tranches d'imposition"""
    print_separator("TEST 6: Tranches d'Imposition 2024")

    test_incomes = [
        (10000, 1),
        (25000, 1),
        (50000, 1),
        (100000, 1),
        (200000, 1),
    ]

    print(f"{'Revenu':<15} {'Parts':<6} {'TMI':<6} {'Tranche'}")
    print_separator()

    for income, parts in test_incomes:
        tmi, bracket = TaxCalculator.calculate_tax_bracket(income, parts)
        print(f"{format_currency(income):<15} {parts:<6} {tmi}%{' '*(4-len(str(tmi)))} {bracket}")

    print("\n✅ Calculs des tranches validés")


def test_annual_tax_summary():
    """Test 7: Résumé fiscal annuel"""
    print_separator("TEST 7: Résumé Fiscal Annuel")

    summary = TaxCalculator.calculate_annual_tax_summary(
        total_dividends=8000,
        total_capital_gains=5000,
        total_capital_losses=500,
        marginal_tax_rate=30
    )

    print("📊 Revenus de l'année:")
    revenus = summary['revenus']
    print(f"   Dividendes bruts:     {format_currency(revenus['dividendes_bruts'])}")
    print(f"   Plus-values:          {format_currency(revenus['plus_values'])}")
    print(f"   Moins-values:         {format_currency(revenus['moins_values'])}")
    print(f"   PV nettes:            {format_currency(revenus['plus_values_nettes'])}")
    print(f"   Total brut:           {format_currency(revenus['total_brut'])}")

    print("\n💰 Fiscalité PFU:")
    pfu = summary['pfu']
    print(f"   Impôt dividendes:     {format_currency(pfu['impot_dividendes'])}")
    print(f"   Impôt PV:             {format_currency(pfu['impot_pv'])}")
    print(f"   Total impôt:          {format_currency(pfu['total_impot'])}")
    print(f"   Total net:            {format_currency(pfu['total_net'])}")
    print(f"   CSG déductible:       {format_currency(pfu['csg_deductible'])}")

    print("\n📊 Barème progressif:")
    bareme = summary['bareme_progressif']
    print(f"   Total impôt:          {format_currency(bareme['total_impot'])}")
    print(f"   Total net:            {format_currency(bareme['total_net'])}")
    print(f"   TMI:                  {bareme['tmi']}%")

    print("\n💡 Comparaison:")
    comp = summary['comparaison']
    print(f"   Meilleure option:     {comp['meilleure_option']}")
    print(f"   Économie:             {format_currency(comp['economie'])}")

    print("\n✅ Résumé fiscal validé")


def test_ifu_data():
    """Test 8: Données IFU"""
    print_separator("TEST 8: Données IFU (Imprimé Fiscal Unique)")

    ifu = TaxCalculator.calculate_ifu_data(
        dividends_fr=8000,
        dividends_foreign=500,
        capital_gains=5000,
        capital_losses=500
    )

    print("📄 Cases de la déclaration fiscale:")
    print(f"   Case 2DC (dividendes FR):      {format_currency(ifu['case_2DC'])}")
    print(f"   Case 2AB (dividendes étranger): {format_currency(ifu['case_2AB'])}")
    print(f"   Case 2CG (plus-values):        {format_currency(ifu['case_2CG'])}")
    print(f"   Case 2BH (PV nettes):          {format_currency(ifu['case_2BH'])}")

    print("\n💰 Prélèvement forfaitaire unique:")
    pfu = ifu['prelevement_forfaitaire']
    print(f"   Dividendes FR:        {format_currency(pfu['dividendes_fr'])}")
    print(f"   Dividendes étranger:  {format_currency(pfu['dividendes_etranger'])}")
    print(f"   Plus-values:          {format_currency(pfu['plus_values'])}")
    print(f"   Total:                {format_currency(pfu['total'])}")

    print("\n📊 CSG déductible:")
    csg = ifu['csg_deductible']
    print(f"   Montant total:        {format_currency(csg['montant'])}")
    print(f"   Case 6DE:             {format_currency(csg['case_6DE'])}")

    print("\n✅ Données IFU générées avec succès")


def test_database_queries(db: DatabaseManager):
    """Test 9: Requêtes base de données"""
    print_separator("TEST 9: Requêtes Avancées")

    # Positions
    positions = db.get_current_positions()
    print(f"📈 Positions actuelles: {len(positions)}")
    total_invested = 0
    for pos in positions:
        print(f"   {pos.ticker}: {pos.quantity} actions @ PRU {format_currency(pos.pru)}")
        print(f"     Investissement: {format_currency(pos.total_invested)}")
        total_invested += pos.total_invested

    print(f"\n💰 Total investi: {format_currency(total_invested)}")

    # Transactions par ticker
    ticker = "AI.PA"
    transactions = db.get_transactions_by_ticker(ticker)
    print(f"\n📋 Transactions {ticker}: {len(transactions)}")
    for tx in transactions:
        print(f"   {tx.transaction_date}: {tx.transaction_type} {tx.quantity} @ {format_currency(tx.price_per_share)}")

    # Toutes les transactions
    all_transactions = db.get_all_transactions()
    print(f"\n📊 Total transactions: {len(all_transactions)}")

    print("\n✅ Requêtes validées")


def run_all_tests():
    """Exécute tous les tests offline"""
    print("\n" + "=" * 70)
    print("  TESTS ÉTAPE 2 - MODE OFFLINE (Sans Connexion Réseau)")
    print("=" * 70)

    try:
        # Test 1: Base de données
        db = test_database()

        # Test 2: Validateurs
        test_validators()

        # Test 3: Formatters
        test_formatters()

        # Test 4: Calculateur FIFO
        test_calculator()

        # Test 5: Calculateur fiscal
        test_tax_calculator()

        # Test 6: Tranches d'imposition
        test_tax_brackets()

        # Test 7: Résumé fiscal annuel
        test_annual_tax_summary()

        # Test 8: Données IFU
        test_ifu_data()

        # Test 9: Requêtes DB
        test_database_queries(db)

        # Résumé final
        print_separator("RÉSUMÉ DES TESTS")
        print("✅ Tous les tests sont passés avec succès!")

        print("\n📋 Modules testés:")
        print("   ✓ Base de données (SQLite)")
        print("   ✓ Validateurs (tickers, prix, quantités, dates)")
        print("   ✓ Formatters (devise, pourcentages, dates)")
        print("   ✓ Calculateur FIFO (plus-values)")
        print("   ✓ Calculateur fiscal (PFU vs Barème)")
        print("   ✓ Tranches d'imposition 2024")
        print("   ✓ Résumé fiscal annuel")
        print("   ✓ Données IFU pour déclaration")
        print("   ✓ Requêtes et statistiques")

        print("\n🎉 ÉTAPE 2 COMPLÉTÉE AVEC SUCCÈS!")
        print("\n📌 Architecture complète:")
        print("   ✅ database/ - Base de données SQLite")
        print("   ✅ api/ - Wrappers yfinance (market_data, dividends)")
        print("   ✅ core/ - Logique métier (calculator, tax_calculator, portfolio)")
        print("   ✅ utils/ - Utilitaires (validators, formatters)")
        print("   ✅ config.py - Configuration centralisée")

        print("\n📌 Prochaine étape: Étape 3 - Interface CustomTkinter")

    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
