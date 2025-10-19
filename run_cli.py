# -*- coding: utf-8 -*-
"""
CLI Interactive pour Portfolio Manager
Version de développement pour Mac - Compatible tous systèmes
La version GUI (run_app.py) sera utilisée sur Windows
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from portfolio_manager.core.portfolio import Portfolio
from portfolio_manager.utils.formatters import format_currency, format_percentage
from datetime import datetime


class PortfolioCLI:
    """Interface en ligne de commande pour Portfolio Manager"""

    def __init__(self):
        self.portfolio = Portfolio()
        self.running = True

        if self.portfolio.needs_market_refresh_today():
            print("⏳ Mise à jour initiale des prix en cours...")
            try:
                updated = self.portfolio.refresh_market_data_if_needed(force=True)
                print(f"✅ Mise à jour automatique: {updated} ticker(s) actualisé(s)\n")
            except Exception as exc:
                print(f"⚠️ Rafraîchissement automatique indisponible: {exc}\n")

    def clear_screen(self):
        """Efface l'écran (multi-plateforme)"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self, title):
        """Affiche un en-tête formaté"""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80 + "\n")

    def print_menu(self):
        """Affiche le menu principal"""
        self.clear_screen()
        print("\n" + "━" * 80)
        print("  📊 PORTFOLIO MANAGER - TRADE REPUBLIC")
        print("━" * 80 + "\n")
        print("  [1] 📈 Dashboard - Vue d'ensemble")
        print("  [2] 💼 Positions actuelles")
        print("  [3] 📝 Transactions - Historique")
        print("  [4] ➕ Ajouter une transaction")
        print("  [5] 💵 Dividendes")
        print("  [6] 📊 Performance & Fiscalité")
        print("  [7] 🔄 Rafraîchir les prix")
        print("  [8] 📤 Exporter en Excel")
        print("  [0] ❌ Quitter")
        print("\n" + "━" * 80)

    def show_dashboard(self):
        """Affiche le dashboard"""
        self.clear_screen()
        self.print_header("📈 DASHBOARD")

        try:
            snapshot = self.portfolio.get_portfolio_snapshot()
            performance = self.portfolio.get_performance_metrics()

            # Métriques principales
            print("  📊 MÉTRIQUES PRINCIPALES\n")
            print(f"    💰 Valeur Totale:      {format_currency(snapshot.total_invested)}")
            print(f"    📈 Gains/Pertes:       {format_currency(snapshot.total_gain_loss)} ({format_percentage(snapshot.total_gain_loss_percent)})")
            print(f"    💵 Dividendes:         {format_currency(snapshot.dividend_income)}")
            print(f"    🎯 Performance:        {format_percentage(performance.total_return_percent)}")
            print(f"    💳 Frais payés:        {format_currency(performance.total_fees_paid)}")
            print(f"    📦 Positions:          {snapshot.positions_count}")

            # Top 5 positions
            if snapshot.positions:
                print("\n  🏆 TOP 5 POSITIONS\n")
                print(f"    {'Ticker':<12} {'Société':<25} {'Valeur':<15} {'P&L':<15} {'Poids':<10}")
                print(f"    {'-' * 77}")

                for pos in snapshot.positions[:5]:
                    ticker = pos['ticker']
                    company = pos['company_name'][:23] + "..." if len(pos['company_name']) > 23 else pos['company_name']
                    value = format_currency(pos['current_value'])
                    pnl = format_percentage(pos['gain_loss_percent'])
                    weight = f"{pos['weight']:.1f}%"

                    print(f"    {ticker:<12} {company:<25} {value:<15} {pnl:<15} {weight:<10}")

        except Exception as e:
            print(f"  ❌ Erreur: {str(e)}")

        input("\n  Appuyez sur Entrée pour continuer...")

    def show_positions(self):
        """Affiche toutes les positions"""
        self.clear_screen()
        self.print_header("💼 POSITIONS ACTUELLES")

        try:
            positions = self.portfolio.db.get_current_positions()

            if not positions:
                print("  Aucune position dans le portefeuille.\n")
            else:
                print(f"  {'Ticker':<12} {'Société':<30} {'Quantité':<12} {'PMR':<15} {'Valeur':<15}")
                print(f"  {'-' * 84}")

                for pos in positions:
                    ticker = pos.ticker
                    company = pos.company_name[:28] + "..." if len(pos.company_name) > 28 else pos.company_name
                    qty = f"{pos.quantity:.4f}"
                    pmr = format_currency(pos.average_price)
                    value = format_currency(pos.total_invested)

                    print(f"  {ticker:<12} {company:<30} {qty:<12} {pmr:<15} {value:<15}")

                total = sum(p.total_invested for p in positions)
                print(f"\n  Total: {format_currency(total)}")

        except Exception as e:
            print(f"  ❌ Erreur: {str(e)}")

        input("\n  Appuyez sur Entrée pour continuer...")

    def show_transactions(self):
        """Affiche l'historique des transactions"""
        self.clear_screen()
        self.print_header("📝 HISTORIQUE DES TRANSACTIONS")

        try:
            transactions = self.portfolio.get_all_transactions()

            if not transactions:
                print("  Aucune transaction enregistrée.\n")
            else:
                print(f"  {'Date':<12} {'Type':<8} {'Ticker':<12} {'Qté':<10} {'Prix':<12} {'Total':<15}")
                print(f"  {'-' * 69}")

                for tx in transactions[-20:]:  # 20 dernières transactions
                    date = tx.transaction_date.strftime("%d/%m/%Y")
                    tx_type = tx.transaction_type[:6]
                    ticker = tx.ticker
                    qty = f"{tx.quantity:.2f}"
                    price = format_currency(tx.price_per_share)
                    total = format_currency(tx.quantity * tx.price_per_share + tx.fees)

                    print(f"  {date:<12} {tx_type:<8} {ticker:<12} {qty:<10} {price:<12} {total:<15}")

                print(f"\n  Total: {len(transactions)} transaction(s)")

        except Exception as e:
            print(f"  ❌ Erreur: {str(e)}")

        input("\n  Appuyez sur Entrée pour continuer...")

    def add_transaction(self):
        """Ajoute une nouvelle transaction"""
        self.clear_screen()
        self.print_header("➕ AJOUTER UNE TRANSACTION")

        try:
            print("  Type de transaction:")
            print("    [1] Achat")
            print("    [2] Vente")
            choice = input("\n  Choix: ").strip()

            tx_type = "ACHAT" if choice == "1" else "VENTE" if choice == "2" else None
            if not tx_type:
                print("\n  ❌ Choix invalide")
                input("\n  Appuyez sur Entrée pour continuer...")
                return

            ticker = input("\n  Ticker (ex: AI.PA): ").strip().upper()
            company = input("  Nom de la société: ").strip()
            quantity = float(input("  Quantité: ").strip())
            price = float(input("  Prix par action (€): ").strip())
            date_str = input("  Date (JJ/MM/AAAA, laisser vide pour aujourd'hui): ").strip()

            if not date_str:
                date_str = datetime.now().strftime("%Y-%m-%d")
            else:
                # Convertir JJ/MM/AAAA en AAAA-MM-JJ
                parts = date_str.split("/")
                if len(parts) == 3:
                    date_str = f"{parts[2]}-{parts[1]}-{parts[0]}"

            notes = input("  Notes (optionnel): ").strip()

            # Ajouter la transaction
            tx_id = self.portfolio.add_transaction(
                ticker=ticker,
                company_name=company,
                transaction_type=tx_type,
                quantity=quantity,
                price_per_share=price,
                transaction_date=date_str,
                notes=notes if notes else None
            )

            total = quantity * price + 1  # +1€ frais Trade Republic
            print(f"\n  ✅ Transaction ajoutée avec succès!")
            print(f"     {tx_type} de {quantity} {ticker} @ {format_currency(price)}")
            print(f"     Total: {format_currency(total)} (frais inclus)")

        except ValueError as e:
            print(f"\n  ❌ Erreur de saisie: {str(e)}")
        except Exception as e:
            print(f"\n  ❌ Erreur: {str(e)}")

        input("\n  Appuyez sur Entrée pour continuer...")

    def show_dividends(self):
        """Affiche les dividendes"""
        self.clear_screen()
        self.print_header("💵 DIVIDENDES")

        try:
            dividends = self.portfolio.db.get_all_dividends()

            if not dividends:
                print("  Aucun dividende enregistré.\n")
            else:
                print(f"  {'Date':<12} {'Ticker':<12} {'Montant Brut':<15} {'Montant Net':<15} {'Statut':<10}")
                print(f"  {'-' * 64}")

                total_brut = 0.0
                total_net = 0.0

                for div in dividends:
                    date = div.payment_date.strftime("%d/%m/%Y") if div.payment_date else "N/A"
                    ticker = div.ticker
                    brut = format_currency(div.gross_amount)
                    net = format_currency(div.net_amount)
                    status = div.status

                    print(f"  {date:<12} {ticker:<12} {brut:<15} {net:<15} {status:<10}")

                    total_brut += div.gross_amount
                    total_net += div.net_amount

                print(f"\n  Total Brut: {format_currency(total_brut)}")
                print(f"  Total Net:  {format_currency(total_net)}")

        except Exception as e:
            print(f"  ❌ Erreur: {str(e)}")

        input("\n  Appuyez sur Entrée pour continuer...")

    def show_performance(self):
        """Affiche la performance et fiscalité"""
        self.clear_screen()
        self.print_header("📊 PERFORMANCE & FISCALITÉ")

        try:
            performance = self.portfolio.get_performance_metrics()
            tax_report = self.portfolio.get_tax_report(year=datetime.now().year)

            print("  📈 PERFORMANCE\n")
            print(f"    Rendement total:       {format_percentage(performance.total_return_percent)}")
            print(f"    Gains réalisés:        {format_currency(performance.realized_gains)}")
            print(f"    Gains latents:         {format_currency(performance.unrealized_gains)}")
            print(f"    Rendement dividendes:  {format_percentage(performance.dividend_yield)}")
            print(f"    Frais totaux:          {format_currency(performance.total_fees_paid)}")

            print("\n  💰 FISCALITÉ " + str(datetime.now().year) + "\n")
            print(f"    Dividendes bruts:      {format_currency(tax_report.total_dividends_gross)}")
            print(f"    Dividendes nets:       {format_currency(tax_report.total_dividends_net)}")
            print(f"    Plus-values réalisées: {format_currency(tax_report.total_capital_gains)}")
            print(f"    Impôts estimés (PFU):  {format_currency(tax_report.estimated_tax_pfu)}")

        except Exception as e:
            print(f"  ❌ Erreur: {str(e)}")

        input("\n  Appuyez sur Entrée pour continuer...")

    def refresh_prices(self):
        """Rafraîchit les prix du marché"""
        self.clear_screen()
        self.print_header("🔄 RAFRAÎCHIR LES PRIX")

        print("  Mise à jour des prix en cours...\n")

        try:
            updated = self.portfolio.refresh_market_data_if_needed(force=True)
            print(f"  ✅ {updated} ticker(s) mis à jour avec succès!")
        except Exception as e:
            print(f"  ❌ Erreur: {str(e)}")
            print("\n  Note: L'application fonctionne avec les données en cache.")

        input("\n  Appuyez sur Entrée pour continuer...")

    def export_excel(self):
        """Export Excel"""
        self.clear_screen()
        self.print_header("📤 EXPORT EXCEL")

        print("  Cette fonctionnalité sera implémentée prochainement.\n")
        print("  Elle exportera:")
        print("    - Résumé du portefeuille")
        print("    - Positions détaillées")
        print("    - Historique des transactions")
        print("    - Dividendes")
        print("    - Rapport fiscal")

        input("\n  Appuyez sur Entrée pour continuer...")

    def run(self):
        """Boucle principale de la CLI"""
        while self.running:
            self.print_menu()
            choice = input("\n  Votre choix: ").strip()

            if choice == "1":
                self.show_dashboard()
            elif choice == "2":
                self.show_positions()
            elif choice == "3":
                self.show_transactions()
            elif choice == "4":
                self.add_transaction()
            elif choice == "5":
                self.show_dividends()
            elif choice == "6":
                self.show_performance()
            elif choice == "7":
                self.refresh_prices()
            elif choice == "8":
                self.export_excel()
            elif choice == "0":
                self.clear_screen()
                print("\n  👋 Au revoir ! Bon trading !\n")
                self.running = False
            else:
                input("\n  ❌ Choix invalide. Appuyez sur Entrée pour continuer...")


def main():
    """Lance la CLI"""
    print("\n🚀 Lancement de Portfolio Manager (CLI)...\n")

    try:
        cli = PortfolioCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n\n  👋 Au revoir ! Bon trading !\n")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
