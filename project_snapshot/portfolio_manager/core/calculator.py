# -*- coding: utf-8 -*-
"""
Calculateur financier pour le portefeuille
Gère tous les calculs financiers : PRU, PV latentes, PV réalisées, etc.
"""

from typing import List, Tuple, Dict
from datetime import datetime
from dataclasses import dataclass

from ..database.models import Transaction, Position
from ..config import TRANSACTION_FEE, PV_CALCULATION_METHOD


@dataclass
class RealizedGainLoss:
    """Représente une plus ou moins-value réalisée"""
    ticker: str
    quantity_sold: float
    sell_price: float
    average_buy_price: float  # Prix de revient moyen des actions vendues
    total_gain_loss: float    # PV totale (positive ou négative)
    gain_loss_percent: float
    sell_date: str
    buy_transactions_used: List[int]  # IDs des transactions d'achat utilisées (FIFO)


class FinancialCalculator:
    """
    Calculateur financier pour analyser le portefeuille
    Calcule les PRU, PV latentes, PV réalisées, performances, etc.
    """

    @staticmethod
    def calculate_average_buy_price(transactions: List[Transaction]) -> float:
        """
        Calcule le Prix de Revient Unitaire (PRU) moyen pondéré

        Formule : PRU = (Somme des achats avec frais) / (Somme des quantités)

        Args:
            transactions: Liste des transactions d'achat pour un ticker

        Returns:
            Le prix de revient moyen par action
        """
        sorted_transactions = sorted(transactions, key=lambda t: t.transaction_date)
        remaining_buys: List[Transaction] = []

        for tx in sorted_transactions:
            if tx.transaction_type == 'ACHAT':
                remaining_buys.append(tx)
            elif tx.transaction_type == 'VENTE':
                remaining_buys = FinancialCalculator._update_remaining_buys(
                    remaining_buys,
                    tx.quantity
                )

        total_cost = sum(t.total_cost for t in remaining_buys)
        total_quantity = sum(t.quantity for t in remaining_buys)

        if total_quantity <= 0:
            return 0

        return total_cost / total_quantity

    @staticmethod
    def calculate_unrealized_pnl(
        position: Position,
        current_price: float
    ) -> Tuple[float, float]:
        """
        Calcule la plus-value latente (non réalisée)

        Args:
            position: Position actuelle
            current_price: Prix actuel de l'action

        Returns:
            Tuple (PV en euros, PV en pourcentage)
        """
        # Valeur actuelle du portefeuille
        current_value = position.quantity * current_price

        # Plus-value latente = Valeur actuelle - Montant investi
        pnl_amount = current_value - position.total_invested

        # Pourcentage de gain/perte
        if position.total_invested > 0:
            pnl_percent = (pnl_amount / position.total_invested) * 100
        else:
            pnl_percent = 0

        return pnl_amount, pnl_percent

    @staticmethod
    def calculate_realized_pv_fifo(
        buy_transactions: List[Transaction],
        sell_transaction: Transaction
    ) -> RealizedGainLoss:
        """
        Calcule la plus-value réalisée selon la méthode FIFO
        (First In First Out - obligatoire en France)

        Principe FIFO : Les premières actions achetées sont les premières vendues

        Args:
            buy_transactions: Liste des achats (triés par date croissante)
            sell_transaction: Transaction de vente

        Returns:
            RealizedGainLoss avec les détails de la PV réalisée
        """
        quantity_to_sell = sell_transaction.quantity
        total_buy_cost = 0
        quantity_sold = 0
        transactions_used = []

        # Parcourir les achats dans l'ordre (FIFO)
        for buy_tx in buy_transactions:
            if quantity_sold >= quantity_to_sell:
                break

            # Quantité qu'on peut prendre de cet achat
            quantity_from_this_buy = min(
                buy_tx.quantity,
                quantity_to_sell - quantity_sold
            )

            # Coût proportionnel de cet achat (incluant les frais)
            cost_per_share = buy_tx.total_cost / buy_tx.quantity
            total_buy_cost += quantity_from_this_buy * cost_per_share

            quantity_sold += quantity_from_this_buy
            transactions_used.append(buy_tx.id)

        # Prix de revient moyen des actions vendues
        average_buy_price = total_buy_cost / quantity_sold if quantity_sold > 0 else 0

        # Montant de la vente (prix de vente - frais de vente)
        # Le sell_transaction.total_cost contient déjà: (quantité × prix) - frais
        sell_amount = sell_transaction.total_cost

        # Plus-value réalisée = Montant vente - Coût d'achat
        total_pv = sell_amount - total_buy_cost

        # Pourcentage de gain/perte
        pv_percent = (total_pv / total_buy_cost * 100) if total_buy_cost > 0 else 0

        return RealizedGainLoss(
            ticker=sell_transaction.ticker,
            quantity_sold=quantity_sold,
            sell_price=sell_transaction.price_per_share,
            average_buy_price=average_buy_price,
            total_gain_loss=total_pv,
            gain_loss_percent=pv_percent,
            sell_date=sell_transaction.transaction_date,
            buy_transactions_used=transactions_used
        )

    @staticmethod
    def calculate_all_realized_pv(transactions: List[Transaction]) -> List[RealizedGainLoss]:
        """
        Calcule toutes les plus-values réalisées pour un ticker

        Args:
            transactions: Toutes les transactions pour un ticker (achats et ventes)

        Returns:
            Liste des plus-values réalisées pour chaque vente
        """
        # Trier par date (ordre chronologique)
        sorted_tx = sorted(transactions, key=lambda t: t.transaction_date)

        realized_pvs = []
        remaining_buys = []

        for tx in sorted_tx:
            if tx.transaction_type == 'ACHAT':
                # Ajouter cet achat aux achats disponibles
                remaining_buys.append(tx)

            elif tx.transaction_type == 'VENTE':
                # Calculer la PV pour cette vente
                pv = FinancialCalculator.calculate_realized_pv_fifo(
                    remaining_buys,
                    tx
                )
                realized_pvs.append(pv)

                # Mettre à jour les achats restants après cette vente
                remaining_buys = FinancialCalculator._update_remaining_buys(
                    remaining_buys,
                    tx.quantity
                )

        return realized_pvs

    @staticmethod
    def _update_remaining_buys(
        buy_transactions: List[Transaction],
        quantity_sold: float
    ) -> List[Transaction]:
        """
        Met à jour la liste des achats après une vente (FIFO)

        Args:
            buy_transactions: Liste des achats disponibles
            quantity_sold: Quantité vendue

        Returns:
            Liste des achats mis à jour (avec quantités réduites)
        """
        remaining = []
        quantity_to_remove = quantity_sold

        for buy_tx in buy_transactions:
            if quantity_to_remove <= 0:
                # Plus rien à retirer, garder cet achat tel quel
                remaining.append(buy_tx)
            elif buy_tx.quantity > quantity_to_remove:
                # Cet achat n'est que partiellement vendu
                # Créer une nouvelle transaction avec la quantité réduite
                updated_tx = Transaction(
                    id=buy_tx.id,
                    ticker=buy_tx.ticker,
                    company_name=buy_tx.company_name,
                    transaction_type=buy_tx.transaction_type,
                    quantity=buy_tx.quantity - quantity_to_remove,
                    price_per_share=buy_tx.price_per_share,
                    transaction_date=buy_tx.transaction_date,
                    total_cost=buy_tx.total_cost * (buy_tx.quantity - quantity_to_remove) / buy_tx.quantity,
                    fees=buy_tx.fees * (buy_tx.quantity - quantity_to_remove) / buy_tx.quantity,
                    notes=buy_tx.notes
                )
                remaining.append(updated_tx)
                quantity_to_remove = 0
            else:
                # Cet achat est entièrement vendu, on le supprime
                quantity_to_remove -= buy_tx.quantity

        return remaining

    @staticmethod
    def calculate_portfolio_performance(
        total_invested: float,
        current_value: float,
        total_dividends_received: float
    ) -> Dict[str, float]:
        """
        Calcule la performance globale du portefeuille

        Performance totale = (Valeur actuelle + Dividendes - Capital investi) / Capital investi

        Args:
            total_invested: Montant total investi (achats - ventes)
            current_value: Valeur actuelle du portefeuille
            total_dividends_received: Total des dividendes reçus

        Returns:
            Dictionnaire avec les métriques de performance
        """
        # Gains latents (non réalisés)
        unrealized_gain = current_value - total_invested

        # Gains totaux = Gains latents + Dividendes
        total_gain = unrealized_gain + total_dividends_received

        # Pourcentage de performance
        if total_invested > 0:
            performance_percent = (total_gain / total_invested) * 100
        else:
            performance_percent = 0

        return {
            'total_invested': total_invested,
            'current_value': current_value,
            'unrealized_gain': unrealized_gain,
            'unrealized_gain_percent': (unrealized_gain / total_invested * 100) if total_invested > 0 else 0,
            'total_dividends': total_dividends_received,
            'total_gain': total_gain,
            'total_performance_percent': performance_percent
        }

    @staticmethod
    def calculate_dividend_yield(
        annual_dividend_per_share: float,
        current_price: float
    ) -> float:
        """
        Calcule le rendement de dividende (dividend yield)

        Yield = (Dividende annuel / Prix actuel) × 100

        Args:
            annual_dividend_per_share: Dividende annuel par action
            current_price: Prix actuel de l'action

        Returns:
            Rendement en pourcentage
        """
        if current_price <= 0:
            return 0

        return (annual_dividend_per_share / current_price) * 100

    @staticmethod
    def calculate_portfolio_dividend_yield(
        positions: List[Position],
        annual_dividends_by_ticker: Dict[str, float]
    ) -> float:
        """
        Calcule le rendement moyen du portefeuille

        Args:
            positions: Liste des positions actuelles
            annual_dividends_by_ticker: Dict {ticker: dividende_annuel_total}

        Returns:
            Rendement moyen pondéré du portefeuille
        """
        total_value = sum(p.current_value for p in positions)
        total_annual_dividends = sum(annual_dividends_by_ticker.values())

        if total_value <= 0:
            return 0

        return (total_annual_dividends / total_value) * 100

    @staticmethod
    def calculate_position_weight(position: Position, total_portfolio_value: float) -> float:
        """
        Calcule le poids d'une position dans le portefeuille

        Args:
            position: Position à analyser
            total_portfolio_value: Valeur totale du portefeuille

        Returns:
            Poids en pourcentage (0-100)
        """
        if total_portfolio_value <= 0:
            return 0

        return (position.current_value / total_portfolio_value) * 100

    @staticmethod
    def validate_sell_transaction(
        current_quantity: float,
        quantity_to_sell: float
    ) -> Tuple[bool, str]:
        """
        Valide qu'une vente est possible

        Args:
            current_quantity: Quantité actuelle détenue
            quantity_to_sell: Quantité à vendre

        Returns:
            Tuple (is_valid, error_message)
        """
        if quantity_to_sell <= 0:
            return False, "La quantité à vendre doit être positive"

        if quantity_to_sell > current_quantity:
            return False, f"Quantité insuffisante. Vous détenez {current_quantity} actions, vous voulez en vendre {quantity_to_sell}"

        return True, ""

    @staticmethod
    def calculate_fees_total(num_transactions: int) -> float:
        """
        Calcule le total des frais Trade Republic

        Args:
            num_transactions: Nombre de transactions (achats + ventes)

        Returns:
            Montant total des frais
        """
        return num_transactions * TRANSACTION_FEE

    @staticmethod
    def calculate_roi(initial_investment: float, final_value: float) -> float:
        """
        Calcule le ROI (Return On Investment)

        ROI = ((Valeur finale - Investissement initial) / Investissement initial) × 100

        Args:
            initial_investment: Investissement initial
            final_value: Valeur finale

        Returns:
            ROI en pourcentage
        """
        if initial_investment <= 0:
            return 0

        return ((final_value - initial_investment) / initial_investment) * 100

    @staticmethod
    def calculate_break_even_price(
        buy_price: float,
        buy_fees: float,
        sell_fees: float,
        quantity: float
    ) -> float:
        """
        Calcule le prix de vente nécessaire pour être à l'équilibre (break-even)

        Prix break-even = (Prix d'achat × quantité + frais achat + frais vente) / quantité

        Args:
            buy_price: Prix d'achat par action
            buy_fees: Frais d'achat
            sell_fees: Frais de vente
            quantity: Quantité d'actions

        Returns:
            Prix de vente pour être à l'équilibre
        """
        if quantity <= 0:
            return 0

        total_cost = (buy_price * quantity) + buy_fees + sell_fees
        return total_cost / quantity
