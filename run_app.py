# -*- coding: utf-8 -*-
"""Lance Portfolio Manager en mode GUI CustomTkinter ou en mode console."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Assurer les imports relatifs
sys.path.insert(0, str(Path(__file__).parent))


def _run_portfolio_cli(db_path: Optional[str] = None) -> int:
    """Affiche un tableau de bord texte pour le portefeuille."""
    from portfolio_manager.core.portfolio import Portfolio
    from portfolio_manager.utils.formatters import format_currency, format_percentage

    portfolio = Portfolio(db_path)
    snapshot = portfolio.get_portfolio_snapshot()
    performance = portfolio.get_performance_metrics()

    print("📊 Portfolio Manager – Mode console")
    print("=" * 60)
    print(f"Date: {snapshot.date}")
    print(f"Positions actives: {snapshot.positions_count}")
    print(f"Capital investi: {format_currency(snapshot.total_invested)}")
    print(f"Valeur actuelle: {format_currency(snapshot.current_value)}")
    print(f"Gains latents: {format_currency(snapshot.unrealized_gains)}")
    print(f"Gains réalisés: {format_currency(snapshot.realized_gains)}")
    print(f"Performance totale: {format_percentage(snapshot.total_gain_loss_percent)}")
    print(f"Dividendes reçus: {format_currency(snapshot.dividend_income)}")
    print()

    if snapshot.positions:
        print("Top positions (max 5):")
        for pos in snapshot.positions[:5]:
            ticker = pos['ticker']
            name = pos['company_name']
            value = format_currency(pos['current_value'])
            pnl = format_currency(pos['gain_loss'])
            pnl_pct = format_percentage(pos['gain_loss_percent'])
            weight = f"{pos['weight']:.1f}%"
            print(f" - {ticker:8s} | {name:25.25s} | Valeur {value:>12s} | P&L {pnl:>12s} ({pnl_pct}) | Poids {weight}")
        print()

    print("Métriques globales:")
    print(f" - Rendement total: {format_currency(performance.total_return)} ({format_percentage(performance.total_return_percent)})")
    print(f" - Rendement annualisé: {format_percentage(performance.annualized_return)}")
    print(f" - Dividend yield estimé: {format_percentage(performance.dividend_yield)}")
    print(f" - Frais payés: {format_currency(performance.total_fees_paid)}")
    print(f" - PRU moyen pondéré: {format_currency(performance.average_pru)}")

    return 0


def _run_gui_child(db_path: Optional[str] = None) -> int:
    """Démarre l'interface graphique CustomTkinter (processus enfant)."""
    from portfolio_manager.ui.main_window import PortfolioApp

    app = PortfolioApp(db_path)
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
    return 0


def _launch_gui(db_path: Optional[str] = None) -> int:
    """Lance la GUI dans un sous-processus pour détecter les échecs proprement."""
    env = os.environ.copy()
    env["PM_GUI_CHILD"] = "1"

    args = [sys.executable, str(Path(__file__).resolve())]
    if db_path:
        args.extend(["--db", db_path])

    result = subprocess.run(args, env=env)
    return result.returncode


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Portfolio Manager launcher")
    parser.add_argument("--db", dest="db_path", help="Chemin vers la base SQLite")
    parser.add_argument("--cli", action="store_true", help="Forcer le mode console")
    parser.add_argument("--gui", action="store_true", help="Forcer le mode graphique")
    return parser.parse_args()


def main() -> int:
    # Mode enfant GUI: ne pas re-parcourir la logique principale
    if os.environ.get("PM_GUI_CHILD") == "1":
        # Parser uniquement pour récupérer --db éventuel
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--db", dest="db_path")
        args, _ = parser.parse_known_args()
        return _run_gui_child(args.db_path)

    args = parse_arguments()

    if args.cli and args.gui:
        print("⚠️ Options --cli et --gui incompatibles. Passage en mode console.")
        return _run_portfolio_cli(args.db_path)

    if args.cli:
        return _run_portfolio_cli(args.db_path)

    # Sur macOS, lancer directement la GUI sans subprocess pour éviter les problèmes
    # Le subprocess cause des problèmes avec CustomTkinter sur Mac
    if sys.platform == "darwin":
        try:
            return _run_gui_child(args.db_path)
        except Exception as e:
            print(f"⚠️ Impossible de lancer l'interface graphique: {e}")
            print("   Passage automatique en mode console.")
            return _run_portfolio_cli(args.db_path)

    # Sur Windows/Linux, utiliser le subprocess comme avant
    gui_returncode = _launch_gui(args.db_path)
    if gui_returncode == 0:
        return 0

    print("⚠️ Impossible de lancer l'interface graphique (code retour", gui_returncode, ").")
    print("   Passage automatique en mode console.")
    return _run_portfolio_cli(args.db_path)


if __name__ == "__main__":
    sys.exit(main())
