# -*- coding: utf-8 -*-
"""
Classe Portfolio - Orchestration principale
Gère l'ensemble du portefeuille avec mise à jour temps réel
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..database.db_manager import DatabaseManager
from ..database.models import Transaction, Dividend, Position
from ..api.market_data import MarketDataAPI
from ..api.dividends import DividendsAPI
from .calculator import FinancialCalculator
from .tax_calculator import TaxCalculator
from ..config import TRANSACTION_FEE


@dataclass
class PortfolioSnapshot:
    """Instantané du portefeuille à un moment donné"""
    date: str
    total_invested: float
    current_value: float
    total_gain_loss: float
    total_gain_loss_percent: float
    realized_gains: float
    unrealized_gains: float
    dividend_income: float
    positions_count: int
    positions: List[Dict]


@dataclass
class PerformanceMetrics:
    """Métriques de performance du portefeuille"""
    total_return: float
    total_return_percent: float
    annualized_return: float
    best_position: Dict
    worst_position: Dict
    dividend_yield: float
    total_fees_paid: float
    average_pru: float


class Portfolio:
    """
    Classe principale pour gérer un portefeuille Trade Republic
    """

    def __init__(self, db_path: str = None):
        """
        Initialise le portfolio

        Args:
            db_path: Chemin vers la base de données (optionnel)
        """
        self.db = DatabaseManager(db_path)
        self.market_api = MarketDataAPI(self.db)
        self.dividends_api = DividendsAPI(self.db)
        self.calculator = FinancialCalculator
        self.tax_calculator = TaxCalculator

    # ========================
    # TRANSACTIONS
    # ========================

    def add_transaction(
        self,
        ticker: str,
        company_name: str,
        transaction_type: str,
        quantity: float,
        price_per_share: float,
        transaction_date: str,
        notes: str = ""
    ) -> int:
        """
        Ajoute une transaction (achat ou vente)

        Args:
            ticker: Symbole de l'action
            company_name: Nom de l'entreprise
            transaction_type: 'ACHAT' ou 'VENTE'
            quantity: Quantité
            price_per_share: Prix par action
            transaction_date: Date (YYYY-MM-DD)
            notes: Notes (optionnel)

        Returns:
            ID de la transaction
        """
        # Calculer le coût total avec frais Trade Republic (1€)
        if transaction_type.upper() == 'ACHAT':
            total_cost = (quantity * price_per_share) + TRANSACTION_FEE
        else:
            total_cost = (quantity * price_per_share) - TRANSACTION_FEE

        transaction = Transaction(
            ticker=ticker,
            company_name=company_name,
            transaction_type=transaction_type.upper(),
            quantity=quantity,
            price_per_share=price_per_share,
            transaction_date=transaction_date,
            total_cost=total_cost,
            fees=TRANSACTION_FEE,
            notes=notes
        )

        transaction_id = self.db.add_transaction(transaction)

        # Si achat, synchroniser les dividendes pour cette position
        if transaction_type.upper() == 'ACHAT':
            self.sync_dividends_for_ticker(ticker, company_name)

        return transaction_id

    def get_all_transactions(self) -> List[Transaction]:
        """Récupère toutes les transactions"""
        return self.db.get_all_transactions()

    def get_transactions_by_ticker(self, ticker: str) -> List[Transaction]:
        """Récupère les transactions pour un ticker"""
        return self.db.get_transactions_by_ticker(ticker)

    def delete_transaction(self, transaction_id: int) -> bool:
        """Supprime une transaction"""
        return self.db.delete_transaction(transaction_id)

    # ========================
    # POSITIONS
    # ========================

    def get_current_positions(self) -> List[Position]:
        """
        Récupère les positions actuelles (avec prix de marché)

        Returns:
            Liste des positions avec données temps réel
        """
        positions = self.db.get_current_positions()

        if not positions:
            return []

        # Récupérer les prix actuels en batch (avec gestion d'erreur)
        try:
            tickers = [p.ticker for p in positions]
            market_data = self.market_api.get_multiple_prices(tickers)
        except Exception as e:
            print(f"⚠️ Erreur lors de la récupération des prix: {e}")
            market_data = {}

        enriched_positions = []
        for position in positions:
            market_info = market_data.get(position.ticker)

            if market_info:
                position.update_current_values(market_info.current_price)
            else:
                fallback_price = self._get_fallback_price(position.ticker)
                if fallback_price is not None:
                    position.update_current_values(fallback_price)
                else:
                    position.current_price = position.pru
                    position.current_value = position.quantity * position.pru
                    position.unrealized_gain_loss = 0
                    position.unrealized_gain_loss_percent = 0

            enriched_positions.append(position)

        return enriched_positions

    def _get_fallback_price(self, ticker: str) -> Optional[float]:
        """Renvoie un prix théorique quand aucune donnée marché fraîche n'est disponible."""
        try:
            cached = self.db.get_market_cache(ticker)
            if cached and cached.current_price:
                return cached.current_price
        except Exception:
            pass

        try:
            transactions = self.db.get_transactions_by_ticker(ticker)
            if transactions:
                latest = max(
                    transactions,
                    key=lambda t: (t.transaction_date, t.id or 0)
                )
                return latest.price_per_share
        except Exception:
            pass

        return None

    def get_position_details(self, ticker: str) -> Optional[Dict]:
        """
        Récupère les détails complets d'une position

        Args:
            ticker: Symbole de l'action

        Returns:
            Dictionnaire avec toutes les infos
        """
        positions = self.get_current_positions()
        position = next((p for p in positions if p.ticker == ticker), None)

        if not position:
            return None

        # Récupérer l'historique des transactions
        transactions = self.get_transactions_by_ticker(ticker)

        # Récupérer les dividendes
        dividends = self.dividends_api.db.get_dividends_by_ticker(ticker)

        # Récupérer l'historique des prix (1 an)
        price_history = self.market_api.get_price_history(ticker, period="1y")

        # Calculer le dividend yield
        dividend_yield = 0
        if position.current_price > 0:
            annual_div = self.dividends_api.calculate_annual_dividend(ticker)
            dividend_yield = (annual_div / position.current_price) * 100

        return {
            'position': position,
            'transactions': transactions,
            'dividends': dividends,
            'price_history': price_history,
            'dividend_yield': dividend_yield,
            'total_dividends_received': sum(
                d.net_amount for d in dividends if d.status == 'REÇU'
            )
        }

    # ========================
    # DIVIDENDES
    # ========================

    def sync_dividends_for_ticker(
        self,
        ticker: str,
        company_name: str = None
    ) -> List[Dividend]:
        """
        Synchronise les dividendes pour un ticker

        Args:
            ticker: Symbole de l'action
            company_name: Nom de l'entreprise (optionnel)

        Returns:
            Liste des dividendes synchronisés
        """
        # Récupérer la quantité actuelle détenue
        positions = self.db.get_current_positions()
        position = next((p for p in positions if p.ticker == ticker), None)

        if not position:
            return []

        if not company_name:
            company_name = position.company_name

        return self.dividends_api.sync_dividends_for_position(
            ticker=ticker,
            company_name=company_name,
            quantity=position.quantity,
            auto_save=True
        )

    def sync_all_dividends(self) -> Dict[str, int]:
        """
        Synchronise les dividendes pour toutes les positions

        Returns:
            Dictionnaire {ticker: nombre_de_dividendes}
        """
        positions = self.get_current_positions()
        results = {}

        for position in positions:
            dividends = self.sync_dividends_for_ticker(
                position.ticker,
                position.company_name
            )
            results[position.ticker] = len(dividends)

        return results

    def get_upcoming_dividends(self, days_ahead: int = 30) -> List[Dividend]:
        """Récupère les dividendes à venir"""
        return self.dividends_api.get_upcoming_dividends(days_ahead)

    def get_dividend_summary(self, year: int = None) -> Dict:
        """Génère un résumé des dividendes pour une année"""
        return self.dividends_api.get_dividend_summary(year)

    def get_upcoming_dividends_summary(self, days_ahead: int = 30) -> Dict[str, object]:
        """Retourne un résumé agrégé des dividendes à venir."""
        return self.dividends_api.get_upcoming_dividends_summary(days_ahead)

    # ========================
    # PORTFOLIO GLOBAL
    # ========================

    def get_portfolio_snapshot(self) -> PortfolioSnapshot:
        """
        Génère un instantané complet du portefeuille

        Returns:
            PortfolioSnapshot avec toutes les métriques
        """
        positions = self.get_current_positions()

        # Calculer les totaux
        total_invested = sum(p.total_invested for p in positions)
        current_value = sum(p.current_value for p in positions)
        unrealized_gains = sum(p.unrealized_gain_loss for p in positions)

        # Calculer les gains réalisés (ventes)
        realized_gains = self.db.get_realized_gains_total()

        # Gains totaux (réalisés + non réalisés)
        total_gain_loss = realized_gains + unrealized_gains

        # Pourcentage total
        total_gain_loss_percent = 0
        if total_invested > 0:
            total_gain_loss_percent = (total_gain_loss / total_invested) * 100

        # Dividendes reçus
        dividend_income = self.db.get_total_dividends_received()

        # Créer la liste des positions
        positions_data = []
        for p in positions:
            positions_data.append({
                'ticker': p.ticker,
                'company_name': p.company_name,
                'quantity': p.quantity,
                'pru': p.pru,
                'current_price': p.current_price,
                'current_value': p.current_value,
                'gain_loss': p.unrealized_gain_loss,
                'gain_loss_percent': p.unrealized_gain_loss_percent,
                'weight': (p.current_value / current_value * 100) if current_value > 0 else 0
            })

        return PortfolioSnapshot(
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_invested=total_invested,
            current_value=current_value,
            total_gain_loss=total_gain_loss,
            total_gain_loss_percent=total_gain_loss_percent,
            realized_gains=realized_gains,
            unrealized_gains=unrealized_gains,
            dividend_income=dividend_income,
            positions_count=len(positions),
            positions=positions_data
        )

    def get_performance_metrics(self) -> PerformanceMetrics:
        """
        Calcule les métriques de performance

        Returns:
            PerformanceMetrics
        """
        snapshot = self.get_portfolio_snapshot()

        # Meilleure et pire position
        positions = snapshot.positions
        best_position = max(positions, key=lambda p: p['gain_loss_percent']) if positions else None
        worst_position = min(positions, key=lambda p: p['gain_loss_percent']) if positions else None

        # Rendement annualisé (simplifié)
        # TODO: Calculer avec les dates réelles d'investissement
        annualized_return = snapshot.total_gain_loss_percent  # Placeholder

        # Dividend yield du portefeuille
        dividend_yield = 0
        if snapshot.current_value > 0:
            # Calculer les dividendes annuels estimés
            total_annual_div = 0
            for pos in self.get_current_positions():
                annual_div = self.dividends_api.calculate_annual_dividend(pos.ticker)
                total_annual_div += annual_div * pos.quantity
            dividend_yield = (total_annual_div / snapshot.current_value) * 100

        # Frais totaux payés
        total_fees = self.db.get_total_fees_paid()

        # PRU moyen (pondéré par valeur)
        average_pru = 0
        if snapshot.current_value > 0:
            weighted_pru_sum = sum(p['pru'] * p['current_value'] for p in positions)
            average_pru = weighted_pru_sum / snapshot.current_value

        return PerformanceMetrics(
            total_return=snapshot.total_gain_loss,
            total_return_percent=snapshot.total_gain_loss_percent,
            annualized_return=annualized_return,
            best_position=best_position or {},
            worst_position=worst_position or {},
            dividend_yield=dividend_yield,
            total_fees_paid=total_fees,
            average_pru=average_pru
        )

    # ========================
    # FISCALITÉ
    # ========================

    def get_annual_tax_report(
        self,
        year: int = None,
        marginal_tax_rate: float = None
    ) -> Dict:
        """
        Génère un rapport fiscal annuel

        Args:
            year: Année (par défaut année en cours)
            marginal_tax_rate: TMI pour comparaison PFU vs Barème

        Returns:
            Rapport fiscal complet
        """
        if year is None:
            year = datetime.now().year

        # Récupérer les dividendes de l'année
        dividend_summary = self.get_dividend_summary(year)

        # Récupérer les plus-values réalisées (ventes)
        transactions = self.db.get_all_transactions()
        sells = [t for t in transactions if t.transaction_type == 'VENTE']

        total_capital_gains = 0
        total_capital_losses = 0

        for sell in sells:
            sell_date = datetime.strptime(sell.transaction_date, "%Y-%m-%d")
            if sell_date.year != year:
                continue

            # Calculer la plus-value avec FIFO
            buys = [
                t for t in transactions
                if t.ticker == sell.ticker
                and t.transaction_type == 'ACHAT'
                and datetime.strptime(t.transaction_date, "%Y-%m-%d") <= sell_date
            ]

            result = self.calculator.calculate_realized_pv_fifo(buys, sell)
            if result.net_gain_loss > 0:
                total_capital_gains += result.net_gain_loss
            else:
                total_capital_losses += abs(result.net_gain_loss)

        # Calculer le résumé fiscal avec TaxCalculator
        tax_summary = self.tax_calculator.calculate_annual_tax_summary(
            total_dividends=dividend_summary['total_gross'],
            total_capital_gains=total_capital_gains,
            total_capital_losses=total_capital_losses,
            marginal_tax_rate=marginal_tax_rate
        )

        return {
            'year': year,
            'dividend_summary': dividend_summary,
            'capital_gains': total_capital_gains,
            'capital_losses': total_capital_losses,
            'tax_summary': tax_summary
        }

    def get_ifu_data(self, year: int = None) -> Dict:
        """
        Prépare les données pour l'IFU (Imprimé Fiscal Unique)

        Args:
            year: Année fiscale

        Returns:
            Données formatées pour déclaration
        """
        if year is None:
            year = datetime.now().year

        # Récupérer les dividendes (tous français pour CAC 40)
        dividend_summary = self.get_dividend_summary(year)

        # Récupérer les plus-values
        tax_report = self.get_annual_tax_report(year)

        return self.tax_calculator.calculate_ifu_data(
            dividends_fr=dividend_summary['total_gross'],
            dividends_foreign=0,  # CAC 40 = dividendes français
            capital_gains=tax_report['capital_gains'],
            capital_losses=tax_report['capital_losses']
        )

    # ========================
    # STATISTIQUES
    # ========================

    def get_statistics(self) -> Dict:
        """
        Récupère les statistiques complètes du portefeuille

        Returns:
            Dictionnaire avec toutes les stats
        """
        snapshot = self.get_portfolio_snapshot()
        performance = self.get_performance_metrics()

        # Répartition par secteur (si disponible)
        sector_allocation = {}
        for pos in self.get_current_positions():
            company_info = self.market_api.get_company_info(pos.ticker)
            sector = company_info.get('sector', 'N/A')
            if sector not in sector_allocation:
                sector_allocation[sector] = 0
            sector_allocation[sector] += pos.current_value

        return {
            'snapshot': snapshot,
            'performance': performance,
            'sector_allocation': sector_allocation,
            'total_transactions': len(self.get_all_transactions()),
            'total_dividends_count': len(self.dividends_api.db.get_all_dividends())
        }

    # ========================
    # UTILITAIRES
    # ========================

    def refresh_market_data(self) -> int:
        """
        Rafraîchit les données de marché pour toutes les positions

        Returns:
            Nombre de tickers mis à jour
        """
        positions = self.db.get_current_positions()
        tickers = [p.ticker for p in positions]
        return self.market_api.refresh_all_cache(tickers)

    def backup_database(self, backup_path: str = None) -> bool:
        """Crée une sauvegarde de la base de données"""
        return self.db.backup_database(backup_path)

    def export_to_excel(self, output_path: str) -> bool:
        """
        Exporte le portefeuille vers Excel

        Args:
            output_path: Chemin du fichier Excel

        Returns:
            True si succès
        """
        # TODO: Implémenter l'export Excel avec openpyxl
        # Sera implémenté dans l'Étape 3 avec l'UI
        pass
