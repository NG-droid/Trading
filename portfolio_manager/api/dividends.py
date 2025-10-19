# -*- coding: utf-8 -*-
"""
API pour récupérer et gérer les dividendes
Utilise yfinance pour le calendrier et l'historique
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import pandas as pd

from ..database.models import Dividend
from ..database.db_manager import DatabaseManager
from ..config import FLAT_TAX_RATE
from ..data.dividends_reference import DIVIDEND_FALLBACKS
from ..utils.tickers import resolve_yahoo_ticker


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse une chaîne de date en datetime, ou None si invalide."""
    if not date_str:
        return None

    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def _normalize_dividend_amount(value) -> Optional[float]:
    """Convertit un montant de dividende en float, même si suffixe devise."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None

    if isinstance(value, (int, float)) and not pd.isna(value):
        return float(value)

    str_value = str(value).strip()
    if not str_value:
        return None

    # Supprimer un éventuel suffixe devise ("0.25 USD" => "0.25")
    token = str_value.split()[0].replace(',', '.')

    try:
        return float(token)
    except (TypeError, ValueError):
        return None


class DividendsAPI:
    """
    Gère la récupération et le calcul des dividendes
    """

    def __init__(self, db_manager: DatabaseManager = None):
        """
        Initialise l'API des dividendes

        Args:
            db_manager: Gestionnaire de base de données (optionnel)
        """
        self.db = db_manager or DatabaseManager()

    def get_dividend_history(self, ticker: str, years: int = 5) -> List[Dict]:
        """
        Récupère l'historique des dividendes

        Args:
            ticker: Symbole de l'action
            years: Nombre d'années d'historique

        Returns:
            Liste de dictionnaires avec les dividendes
        """
        try:
            yf_ticker = resolve_yahoo_ticker(ticker)
            stock = yf.Ticker(yf_ticker)
            dividends = stock.dividends

            if dividends.empty:
                return []

            # Filtrer sur les X dernières années
            # Convertir l'index en timezone-naive pour la comparaison
            dividends_index_naive = dividends.index.tz_localize(None)
            cutoff_date = datetime.now() - timedelta(days=years*365)
            mask = dividends_index_naive >= cutoff_date
            dividends = dividends[mask]

            history = []
            for date, amount in dividends.items():
                normalized_amount = _normalize_dividend_amount(amount)
                if normalized_amount is None:
                    continue
                history.append({
                    'date': date.strftime("%Y-%m-%d"),
                    'amount_per_share': normalized_amount,
                    'year': date.year,
                    'quarter': (date.month - 1) // 3 + 1
                })

            return history

        except Exception as e:
            alias_info = f" (Yahoo {yf_ticker})" if 'yf_ticker' in locals() and yf_ticker != ticker else ""
            print(f"Erreur récupération dividendes {ticker}{alias_info}: {e}")
            return []

    def get_next_dividend_estimate(self, ticker: str) -> Optional[Dict]:
        """
        Estime le prochain dividende basé sur l'historique

        Args:
            ticker: Symbole de l'action

        Returns:
            Dictionnaire avec l'estimation ou None
        """
        history = self.get_dividend_history(ticker, years=2)

        if not history:
            return None

        # Trier par date
        history = sorted(history, key=lambda x: x['date'], reverse=True)

        # Prendre le dernier dividende
        last_dividend = history[0]
        last_date = datetime.strptime(last_dividend['date'], "%Y-%m-%d")

        # Estimer la fréquence (trimestrielle, semestrielle, annuelle)
        frequency = self._estimate_frequency(history)

        if not frequency:
            return None

        # Calculer la date estimée du prochain dividende
        if frequency == 'quarterly':
            next_date = last_date + timedelta(days=90)
        elif frequency == 'semi-annual':
            next_date = last_date + timedelta(days=180)
        elif frequency == 'annual':
            next_date = last_date + timedelta(days=365)
        else:
            next_date = last_date + timedelta(days=90)  # Par défaut trimestriel

        # Montant estimé = moyenne des derniers dividendes (fallback sur dernier)
        recent_amounts = [d['amount_per_share'] for d in history[:4]]
        if recent_amounts:
            estimated_amount = sum(recent_amounts) / len(recent_amounts)
        else:
            estimated_amount = last_dividend['amount_per_share']

        return {
            'estimated_date': next_date.strftime("%Y-%m-%d"),
            'estimated_amount': estimated_amount,
            'frequency': frequency,
            'confidence': 'medium' if len(history) >= 4 else 'low'
        }

    def _estimate_frequency(self, history: List[Dict]) -> Optional[str]:
        """
        Estime la fréquence de versement des dividendes

        Args:
            history: Historique des dividendes

        Returns:
            'quarterly', 'semi-annual', 'annual' ou None
        """
        if len(history) < 2:
            return None

        # Calculer les intervalles entre dividendes
        sorted_history = sorted(history, key=lambda x: x['date'])
        intervals = []

        for i in range(1, len(sorted_history)):
            date1 = datetime.strptime(sorted_history[i-1]['date'], "%Y-%m-%d")
            date2 = datetime.strptime(sorted_history[i]['date'], "%Y-%m-%d")
            days = (date2 - date1).days
            intervals.append(days)

        if not intervals:
            return None

        # Moyenne des intervalles
        avg_interval = sum(intervals) / len(intervals)

        # Déterminer la fréquence
        if avg_interval < 120:  # ~3 mois
            return 'quarterly'
        elif avg_interval < 240:  # ~6 mois
            return 'semi-annual'
        else:
            return 'annual'

    def calculate_annual_dividend(self, ticker: str) -> float:
        """
        Calcule le dividende annuel (somme des 12 derniers mois)

        Args:
            ticker: Symbole de l'action

        Returns:
            Montant annuel du dividende
        """
        history = self.get_dividend_history(ticker, years=1)

        if not history:
            return 0.0

        # Somme des dividendes de l'année écoulée
        cutoff_date = datetime.now() - timedelta(days=365)
        recent_dividends = [
            d['amount_per_share'] for d in history
            if datetime.strptime(d['date'], "%Y-%m-%d") >= cutoff_date
        ]

        return sum(recent_dividends)

    def calculate_dividend_yield(self, ticker: str, current_price: float) -> float:
        """
        Calcule le dividend yield

        Args:
            ticker: Symbole de l'action
            current_price: Prix actuel de l'action

        Returns:
            Yield en pourcentage
        """
        annual_dividend = self.calculate_annual_dividend(ticker)

        if current_price <= 0:
            return 0.0

        return (annual_dividend / current_price) * 100

    def create_dividend_entry(
        self,
        ticker: str,
        company_name: str,
        amount_per_share: float,
        ex_dividend_date: str,
        quantity_owned: float,
        payment_date: str = None,
        status: str = 'PRÉVU'
    ) -> Dividend:
        """
        Crée une entrée de dividende avec calcul fiscal

        Args:
            ticker: Symbole de l'action
            company_name: Nom de l'entreprise
            amount_per_share: Montant par action
            ex_dividend_date: Date ex-dividende
            quantity_owned: Quantité d'actions détenues
            payment_date: Date de paiement (optionnel)
            status: 'PRÉVU' ou 'REÇU'

        Returns:
            Objet Dividend
        """
        # Montant brut
        gross_amount = amount_per_share * quantity_owned

        # Calcul de l'impôt (PFU 30%)
        tax_amount = gross_amount * FLAT_TAX_RATE

        # Montant net
        net_amount = gross_amount - tax_amount

        dividend = Dividend(
            ticker=ticker,
            company_name=company_name,
            amount_per_share=amount_per_share,
            ex_dividend_date=ex_dividend_date,
            payment_date=payment_date,
            quantity_owned=quantity_owned,
            gross_amount=gross_amount,
            tax_amount=tax_amount,
            net_amount=net_amount,
            status=status
        )

        return dividend

    def sync_dividends_for_position(
        self,
        ticker: str,
        company_name: str,
        quantity: float,
        auto_save: bool = True
    ) -> List[Dividend]:
        """
        Synchronise les dividendes pour une position
        Récupère les dividendes futurs estimés et les enregistre

        Args:
            ticker: Symbole de l'action
            company_name: Nom de l'entreprise
            quantity: Quantité détenue
            auto_save: Sauvegarder automatiquement en base

        Returns:
            Liste des dividendes créés/mis à jour
        """
        dividends = []

        # Récupérer l'estimation du prochain dividende
        next_div = self.get_next_dividend_estimate(ticker)

        if not next_div:
            dividends.extend(
                self._generate_fallback_dividends(
                    ticker,
                    company_name,
                    quantity,
                    auto_save=auto_save
                )
            )
            return dividends

        # Créer l'entrée de dividende prévue
        dividend = self.create_dividend_entry(
            ticker=ticker,
            company_name=company_name,
            amount_per_share=next_div['estimated_amount'],
            ex_dividend_date=next_div['estimated_date'],
            quantity_owned=quantity,
            payment_date=None,  # On ne connaît pas encore la date exacte
            status='PRÉVU'
        )

        if auto_save:
            # Vérifier si ce dividende existe déjà
            existing_dividends = self.db.get_dividends_by_ticker(ticker)
            exists = any(
                d.ex_dividend_date == dividend.ex_dividend_date and d.status == 'PRÉVU'
                for d in existing_dividends
            )

            if not exists:
                dividend_id = self.db.add_dividend(dividend)
                dividend.id = dividend_id

        dividends.append(dividend)
        return dividends

    def _generate_fallback_dividends(
        self,
        ticker: str,
        company_name: Optional[str],
        quantity: float,
        auto_save: bool = True
    ) -> List[Dividend]:
        """Crée des dividendes prévisionnels via les données statiques si API indisponible."""
        ref = DIVIDEND_FALLBACKS.get(ticker)
        if not ref:
            return []

        now = datetime.now()
        existing = self.db.get_dividends_by_ticker(ticker)
        existing_keys = {(d.ex_dividend_date, d.status) for d in existing}

        months = ref.get('months', [])
        amounts = ref.get('amount_schedule', [])
        ex_day = ref.get('ex_day', 1)
        payment_delay = ref.get('payment_delay_days', 15)

        generated: List[Dividend] = []

        for index, month in enumerate(months):
            ex_year = now.year
            try:
                ex_date = datetime(ex_year, month, ex_day)
            except ValueError:
                continue

            if ex_date < now:
                ex_date = datetime(ex_year + 1, month, ex_day)

            pay_date = ex_date + timedelta(days=payment_delay)
            amount = amounts[index % len(amounts)] if amounts else 0.0

            dividend = self.create_dividend_entry(
                ticker=ticker,
                company_name=company_name or ref.get('company_name', ticker),
                amount_per_share=amount,
                ex_dividend_date=ex_date.strftime("%Y-%m-%d"),
                quantity_owned=quantity,
                payment_date=pay_date.strftime("%Y-%m-%d"),
                status='PRÉVU'
            )

            key = (dividend.ex_dividend_date, 'PRÉVU')
            if auto_save and key not in existing_keys:
                dividend.id = self.db.add_dividend(dividend)
                existing_keys.add(key)

            generated.append(dividend)

        return generated

    def get_received_dividends(self, year: Optional[int] = None) -> List[Dividend]:
        """Retourne les dividendes marqués comme reçus, éventuellement filtrés par année."""
        dividends = self.db.get_dividends_by_status('REÇU')

        if year is None:
            result = dividends
        else:
            result = []
            for div in dividends:
                date = _parse_date(div.received_date) or _parse_date(div.payment_date) or _parse_date(div.ex_dividend_date)
                if date and date.year == year:
                    result.append(div)

        result.sort(
            key=lambda d: _parse_date(d.received_date)
            or _parse_date(d.payment_date)
            or _parse_date(d.ex_dividend_date)
            or datetime.min,
            reverse=True
        )
        return result

    def mark_dividend_as_planned(self, dividend_id: int) -> bool:
        """Reclasse un dividende reçu en prévu."""
        dividend = self.db.get_dividend(dividend_id)

        if not dividend:
            return False

        dividend.status = 'PRÉVU'
        dividend.received_date = None
        return self.db.update_dividend(dividend)

    # ------------------------------------------------------------------
    # Aide pour quantité et ajout manuel
    # ------------------------------------------------------------------

    def get_fallback_schedule(self, ticker: str, year: int) -> List[Dict[str, object]]:
        """Retourne la liste des échéances fallback pour un ticker et une année."""
        ref = DIVIDEND_FALLBACKS.get(ticker)
        if not ref:
            return []

        months = ref.get('months', [])
        amounts = ref.get('amount_schedule', [])
        ex_day = ref.get('ex_day', 1)
        payment_delay = ref.get('payment_delay_days', 15)

        schedule: List[Dict[str, object]] = []
        for index, month in enumerate(months):
            try:
                ex_date = datetime(year, month, ex_day)
            except ValueError:
                continue

            pay_date = ex_date + timedelta(days=payment_delay)
            amount = amounts[index % len(amounts)] if amounts else 0.0

            schedule.append({
                'ex_dividend_date': ex_date.strftime("%Y-%m-%d"),
                'payment_date': pay_date.strftime("%Y-%m-%d"),
                'amount_per_share': amount,
            })

        return schedule

    def get_quantity_on_date(self, ticker: str, date_str: str) -> float:
        """Calcule la quantité détenue pour un ticker à une date donnée (incluse)."""
        target = _parse_date(date_str)
        if not target:
            return 0.0

        transactions = self.db.get_transactions_by_ticker(ticker)
        quantity = 0.0

        for tx in sorted(transactions, key=lambda t: (t.transaction_date, t.id or 0)):
            tx_date = _parse_date(tx.transaction_date)
            if not tx_date or tx_date > target:
                continue
            if tx.transaction_type == 'ACHAT':
                quantity += tx.quantity
            else:
                quantity -= tx.quantity

        return max(quantity, 0.0)

    def add_manual_dividend(
        self,
        ticker: str,
        company_name: str,
        amount_per_share: float,
        ex_dividend_date: str,
        quantity_owned: float,
        payment_date: Optional[str] = None,
        status: str = 'REÇU',
        received_date: Optional[str] = None,
        net_amount_override: Optional[float] = None,
        notes: Optional[str] = None
    ) -> Dividend:
        """Ajoute un dividende manuel (prévu ou reçu)."""
        dividend = self.create_dividend_entry(
            ticker=ticker,
            company_name=company_name,
            amount_per_share=amount_per_share,
            ex_dividend_date=ex_dividend_date,
            payment_date=payment_date,
            quantity_owned=quantity_owned,
            status=status
        )

        if notes:
            dividend.notes = notes

        if status == 'REÇU':
            dividend.received_date = received_date or payment_date or datetime.now().strftime("%Y-%m-%d")
            if net_amount_override is not None:
                dividend.net_amount = net_amount_override
                dividend.gross_amount = net_amount_override / (1 - FLAT_TAX_RATE)
                dividend.tax_amount = dividend.gross_amount - dividend.net_amount
        else:
            dividend.received_date = None

        dividend_id = self.db.add_dividend(dividend)
        dividend.id = dividend_id
        return dividend

    def get_upcoming_dividends(self, days_ahead: int = 30) -> List[Dividend]:
        """Récupère les dividendes à venir dans les X prochains jours."""
        all_dividends = self.db.get_dividends_by_status('PRÉVU')

        now = datetime.now()
        cutoff_date = now + timedelta(days=days_ahead)

        upcoming: List[Dividend] = []
        for div in all_dividends:
            div_date = _parse_date(div.ex_dividend_date)
            if not div_date:
                continue
            if now <= div_date <= cutoff_date:
                upcoming.append(div)

        upcoming.sort(key=lambda d: d.ex_dividend_date or "")
        return upcoming

    def get_upcoming_dividends_summary(self, days_ahead: int = 30) -> Dict[str, object]:
        """Retourne un résumé agrégé des dividendes à venir."""
        upcoming = self.get_upcoming_dividends(days_ahead)

        totals = {
            'gross_total': 0.0,
            'net_total': 0.0,
            'count': len(upcoming),
        }

        by_ticker: Dict[str, Dict[str, object]] = {}

        for div in upcoming:
            totals['gross_total'] += div.gross_amount
            totals['net_total'] += div.net_amount

            info = by_ticker.setdefault(div.ticker, {
                'ticker': div.ticker,
                'company_name': div.company_name,
                'amount_per_share': div.amount_per_share,
                'quantity_owned': div.quantity_owned,
                'gross_total': 0.0,
                'net_total': 0.0,
                'next_ex_date': div.ex_dividend_date,
                'next_payment_date': div.payment_date,
            })

            info['gross_total'] += div.gross_amount
            info['net_total'] += div.net_amount
            info['amount_per_share'] = div.amount_per_share
            info['quantity_owned'] = div.quantity_owned

            current_ex = _parse_date(info['next_ex_date'])
            candidate_ex = _parse_date(div.ex_dividend_date)
            if candidate_ex and (current_ex is None or candidate_ex < current_ex):
                info['next_ex_date'] = div.ex_dividend_date

            current_pay = _parse_date(info['next_payment_date'])
            candidate_pay = _parse_date(div.payment_date)
            if candidate_pay and (current_pay is None or candidate_pay < current_pay):
                info['next_payment_date'] = div.payment_date

        per_ticker = list(by_ticker.values())

        def sort_key(item: Dict[str, object]) -> Tuple[int, Optional[datetime]]:
            date_obj = _parse_date(item.get('next_ex_date'))
            return (0 if date_obj else 1, date_obj)

        per_ticker.sort(key=sort_key)

        return {
            'totals': totals,
            'per_ticker': per_ticker,
        }

    def mark_dividend_as_received(
        self,
        dividend_id: int,
        received_date: str = None,
        actual_net_amount: float = None
    ) -> bool:
        """
        Marque un dividende comme reçu

        Args:
            dividend_id: ID du dividende
            received_date: Date de réception (optionnel, sinon aujourd'hui)
            actual_net_amount: Montant net réel reçu (optionnel)

        Returns:
            True si succès
        """
        dividend = self.db.get_dividend(dividend_id)

        if not dividend:
            return False

        dividend.status = 'REÇU'
        dividend.received_date = received_date or datetime.now().strftime("%Y-%m-%d")

        # Si un montant réel est fourni, recalculer les taxes
        if actual_net_amount is not None:
            dividend.net_amount = actual_net_amount
            # Rétro-calculer le montant brut et les taxes
            dividend.gross_amount = actual_net_amount / (1 - FLAT_TAX_RATE)
            dividend.tax_amount = dividend.gross_amount - dividend.net_amount

        return self.db.update_dividend(dividend)

    def get_dividend_summary(self, year: int = None) -> Dict:
        """
        Génère un résumé des dividendes

        Args:
            year: Année (optionnel, sinon année en cours)

        Returns:
            Dictionnaire avec les statistiques
        """
        if year is None:
            year = datetime.now().year

        dividends = self.db.get_dividends_by_year(str(year))

        # Filtrer uniquement les dividendes reçus
        received = [d for d in dividends if d.status == 'REÇU']

        total_gross = sum(d.gross_amount for d in received)
        total_tax = sum(d.tax_amount for d in received)
        total_net = sum(d.net_amount for d in received)

        # Par mois
        monthly = {}
        for d in received:
            try:
                date = datetime.strptime(d.payment_date or d.ex_dividend_date, "%Y-%m-%d")
                month = date.month
                if month not in monthly:
                    monthly[month] = {'gross': 0, 'net': 0, 'count': 0}
                monthly[month]['gross'] += d.gross_amount
                monthly[month]['net'] += d.net_amount
                monthly[month]['count'] += 1
            except:
                continue

        return {
            'year': year,
            'total_gross': total_gross,
            'total_tax': total_tax,
            'total_net': total_net,
            'count': len(received),
            'average_per_dividend': total_net / len(received) if received else 0,
            'monthly': monthly
        }

    def get_dividend_calendar(
        self,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dividend]:
        """
        Récupère un calendrier des dividendes

        Args:
            start_date: Date de début (format YYYY-MM-DD)
            end_date: Date de fin (format YYYY-MM-DD)

        Returns:
            Liste des dividendes dans la période
        """
        all_dividends = self.db.get_all_dividends()

        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")

        if not end_date:
            # 1 an à l'avance par défaut
            end_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")

        filtered = []
        for div in all_dividends:
            div_date = div.payment_date or div.ex_dividend_date
            if start_date <= div_date <= end_date:
                filtered.append(div)

        # Trier par date
        filtered.sort(key=lambda d: d.payment_date or d.ex_dividend_date)

        return filtered
