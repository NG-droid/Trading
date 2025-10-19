# -*- coding: utf-8 -*-
"""
Gestionnaire de base de données SQLite
Gère toutes les opérations CRUD et la connexion à la base de données
"""

import sqlite3
import os
import shutil
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from contextlib import contextmanager

from .models import (
    Transaction, Dividend, MarketData, Position,
    CREATE_TRANSACTIONS_TABLE, CREATE_TRANSACTIONS_INDEXES,
    CREATE_DIVIDENDS_TABLE, CREATE_DIVIDENDS_INDEXES,
    CREATE_MARKET_CACHE_TABLE,
    CREATE_PRICE_HISTORY_TABLE, CREATE_PRICE_HISTORY_INDEXES,
    Queries,
    dict_to_transaction, dict_to_dividend, dict_to_market_data
)
from ..config import DB_NAME, DB_PATH, BACKUP_PATH


class DatabaseManager:
    """
    Gestionnaire de base de données pour le portefeuille d'actions
    Gère toutes les opérations CRUD et la connexion SQLite
    """

    def __init__(self, db_path: str = None):
        """
        Initialise le gestionnaire de base de données

        Args:
            db_path: Chemin complet vers le fichier de base de données
                     Si None, utilise DB_PATH + DB_NAME depuis config
        """
        if db_path is None:
            # Créer le dossier data s'il n'existe pas
            os.makedirs(DB_PATH, exist_ok=True)
            db_path = os.path.join(DB_PATH, DB_NAME)

        self.db_path = db_path
        self._initialize_database()

    def _initialize_database(self):
        """Crée les tables si elles n'existent pas"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Créer la table transactions
            cursor.execute(CREATE_TRANSACTIONS_TABLE)
            for index_query in CREATE_TRANSACTIONS_INDEXES:
                cursor.execute(index_query)

            # Créer la table dividendes
            cursor.execute(CREATE_DIVIDENDS_TABLE)
            for index_query in CREATE_DIVIDENDS_INDEXES:
                cursor.execute(index_query)

            # Créer la table de cache
            cursor.execute(CREATE_MARKET_CACHE_TABLE)

            # Créer la table d'historique des prix
            cursor.execute(CREATE_PRICE_HISTORY_TABLE)
            for index_query in CREATE_PRICE_HISTORY_INDEXES:
                cursor.execute(index_query)

            conn.commit()

    @contextmanager
    def get_connection(self):
        """
        Context manager pour gérer les connexions à la base de données
        Usage:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(...)
        """
        conn = sqlite3.connect(self.db_path)
        # Permet de récupérer les résultats comme des dictionnaires
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    # ==========================================================================
    # TRANSACTIONS - CRUD
    # ==========================================================================

    def add_transaction(self, transaction: Transaction) -> int:
        """
        Ajoute une nouvelle transaction

        Args:
            transaction: Objet Transaction à ajouter

        Returns:
            L'ID de la transaction créée

        Raises:
            sqlite3.Error: Si erreur lors de l'insertion
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                Queries.INSERT_TRANSACTION,
                (
                    transaction.ticker,
                    transaction.company_name,
                    transaction.transaction_type,
                    transaction.quantity,
                    transaction.price_per_share,
                    transaction.transaction_date,
                    transaction.total_cost,
                    transaction.fees,
                    transaction.notes
                )
            )
            conn.commit()
            return cursor.lastrowid

    def get_transaction(self, transaction_id: int) -> Optional[Transaction]:
        """Récupère une transaction par son ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(Queries.GET_TRANSACTION_BY_ID, (transaction_id,))
            row = cursor.fetchone()

            if row:
                return dict_to_transaction(dict(row))
            return None

    def get_all_transactions(self) -> List[Transaction]:
        """Récupère toutes les transactions"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(Queries.GET_ALL_TRANSACTIONS)
            rows = cursor.fetchall()

            return [dict_to_transaction(dict(row)) for row in rows]

    def get_transactions_by_ticker(self, ticker: str) -> List[Transaction]:
        """Récupère toutes les transactions pour un ticker donné"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(Queries.GET_TRANSACTIONS_BY_TICKER, (ticker,))
            rows = cursor.fetchall()

            return [dict_to_transaction(dict(row)) for row in rows]

    def get_transactions_by_type(self, transaction_type: str) -> List[Transaction]:
        """Récupère toutes les transactions d'un type (ACHAT ou VENTE)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(Queries.GET_TRANSACTIONS_BY_TYPE, (transaction_type,))
            rows = cursor.fetchall()

            return [dict_to_transaction(dict(row)) for row in rows]

    def get_transactions_by_date_range(self, start_date: str, end_date: str) -> List[Transaction]:
        """Récupère les transactions dans une plage de dates"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(Queries.GET_TRANSACTIONS_BY_DATE_RANGE, (start_date, end_date))
            rows = cursor.fetchall()

            return [dict_to_transaction(dict(row)) for row in rows]

    def update_transaction(self, transaction: Transaction) -> bool:
        """
        Met à jour une transaction existante

        Args:
            transaction: Transaction avec l'ID et les nouvelles valeurs

        Returns:
            True si la mise à jour a réussi, False sinon
        """
        if transaction.id is None:
            return False

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                Queries.UPDATE_TRANSACTION,
                (
                    transaction.ticker,
                    transaction.company_name,
                    transaction.transaction_type,
                    transaction.quantity,
                    transaction.price_per_share,
                    transaction.transaction_date,
                    transaction.total_cost,
                    transaction.fees,
                    transaction.notes,
                    transaction.id
                )
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_transaction(self, transaction_id: int) -> bool:
        """
        Supprime une transaction

        Args:
            transaction_id: ID de la transaction à supprimer

        Returns:
            True si la suppression a réussi, False sinon
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(Queries.DELETE_TRANSACTION, (transaction_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ==========================================================================
    # DIVIDENDES - CRUD
    # ==========================================================================

    def add_dividend(self, dividend: Dividend) -> int:
        """Ajoute un nouveau dividende"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                Queries.INSERT_DIVIDEND,
                (
                    dividend.ticker,
                    dividend.company_name,
                    dividend.amount_per_share,
                    dividend.ex_dividend_date,
                    dividend.payment_date,
                    dividend.quantity_owned,
                    dividend.gross_amount,
                    dividend.tax_amount,
                    dividend.net_amount,
                    dividend.status,
                    dividend.received_date,
                    dividend.notes
                )
            )
            conn.commit()
            return cursor.lastrowid

    def get_dividend(self, dividend_id: int) -> Optional[Dividend]:
        """Récupère un dividende par son ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(Queries.GET_DIVIDEND_BY_ID, (dividend_id,))
            row = cursor.fetchone()

            if row:
                return dict_to_dividend(dict(row))
            return None

    def get_all_dividends(self) -> List[Dividend]:
        """Récupère tous les dividendes"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(Queries.GET_ALL_DIVIDENDS)
            rows = cursor.fetchall()

            return [dict_to_dividend(dict(row)) for row in rows]

    def get_dividends_by_ticker(self, ticker: str) -> List[Dividend]:
        """Récupère tous les dividendes pour un ticker"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(Queries.GET_DIVIDENDS_BY_TICKER, (ticker,))
            rows = cursor.fetchall()

            return [dict_to_dividend(dict(row)) for row in rows]

    def get_dividends_by_status(self, status: str) -> List[Dividend]:
        """Récupère les dividendes par statut (PRÉVU ou REÇU)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(Queries.GET_DIVIDENDS_BY_STATUS, (status,))
            rows = cursor.fetchall()

            return [dict_to_dividend(dict(row)) for row in rows]

    def get_dividends_by_year(self, year: str) -> List[Dividend]:
        """Récupère les dividendes pour une année donnée"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(Queries.GET_DIVIDENDS_BY_YEAR, (year,))
            rows = cursor.fetchall()

            return [dict_to_dividend(dict(row)) for row in rows]

    def update_dividend(self, dividend: Dividend) -> bool:
        """Met à jour un dividende existant"""
        if dividend.id is None:
            return False

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                Queries.UPDATE_DIVIDEND,
                (
                    dividend.ticker,
                    dividend.company_name,
                    dividend.amount_per_share,
                    dividend.ex_dividend_date,
                    dividend.payment_date,
                    dividend.quantity_owned,
                    dividend.gross_amount,
                    dividend.tax_amount,
                    dividend.net_amount,
                    dividend.status,
                    dividend.received_date,
                    dividend.notes,
                    dividend.id
                )
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_dividend(self, dividend_id: int) -> bool:
        """Supprime un dividende"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(Queries.DELETE_DIVIDEND, (dividend_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_upcoming_dividends(self, limit: int = 5) -> List[Dividend]:
        """Récupère les prochains dividendes prévus"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(Queries.GET_UPCOMING_DIVIDENDS, (limit,))
            rows = cursor.fetchall()

            return [dict_to_dividend(dict(row)) for row in rows]

    # ==========================================================================
    # CACHE MARCHÉ
    # ==========================================================================

    def upsert_market_cache(self, market_data: MarketData):
        """Insère ou met à jour le cache des données de marché"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                Queries.UPSERT_MARKET_CACHE,
                (
                    market_data.ticker,
                    market_data.current_price,
                    market_data.previous_close,
                    market_data.change_percent,
                    market_data.volume,
                    market_data.market_cap,
                    market_data.last_updated or datetime.now().isoformat()
                )
            )
            conn.commit()

    def get_market_cache(self, ticker: str) -> Optional[MarketData]:
        """Récupère les données de marché en cache pour un ticker"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(Queries.GET_MARKET_CACHE, (ticker,))
            row = cursor.fetchone()

            if row:
                return dict_to_market_data(dict(row))
            return None

    def get_all_market_cache(self) -> List[MarketData]:
        """Récupère toutes les données de marché en cache"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(Queries.GET_ALL_MARKET_CACHE)
            rows = cursor.fetchall()

            return [dict_to_market_data(dict(row)) for row in rows]

    def clean_old_cache(self, days: int = 1):
        """Supprime les données de cache plus anciennes que X jours"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(Queries.DELETE_OLD_CACHE, (days,))
            conn.commit()

    # ==========================================================================
    # STATISTIQUES ET ANALYSES
    # ==========================================================================

    def _calculate_position_cost(self, transactions: List[Transaction]) -> Tuple[float, float]:
        """Calcule la quantité et le coût restant après ventes (FIFO approximatif)."""
        lots: List[Dict[str, float]] = []

        for tx in transactions:
            if tx.transaction_type == 'ACHAT':
                lots.append({'quantity': tx.quantity, 'cost': tx.total_cost})
            elif tx.transaction_type == 'VENTE':
                quantity_to_sell = tx.quantity
                while quantity_to_sell > 0 and lots:
                    lot = lots[0]
                    if lot['quantity'] <= quantity_to_sell + 1e-9:
                        quantity_to_sell -= lot['quantity']
                        lots.pop(0)
                    else:
                        proportion = quantity_to_sell / lot['quantity']
                        lot['cost'] -= lot['cost'] * proportion
                        lot['quantity'] -= quantity_to_sell
                        quantity_to_sell = 0

        total_quantity = sum(lot['quantity'] for lot in lots)
        total_cost = sum(lot['cost'] for lot in lots)
        return total_quantity, total_cost

    def get_current_positions(self) -> List[Position]:
        """
        Récupère toutes les positions actuelles du portefeuille
        Une position = ensemble des actions d'un même ticker encore détenues
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(Queries.GET_CURRENT_POSITIONS)
            rows = cursor.fetchall()

            positions = []
            for row in rows:
                ticker = row['ticker']
                company_name = row['company_name']

                transactions = self.get_transactions_by_ticker(ticker)
                quantity, total_cost = self._calculate_position_cost(transactions)

                if quantity <= 0:
                    continue

                avg_price = total_cost / quantity if quantity > 0 else 0

                position = Position(
                    ticker=ticker,
                    company_name=company_name,
                    quantity=quantity,
                    average_buy_price=avg_price,
                    total_invested=total_cost
                )
                positions.append(position)

            return positions

    def get_dividends_summary_by_year(self) -> List[Dict[str, Any]]:
        """Récupère un résumé des dividendes par année"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(Queries.GET_DIVIDENDS_SUMMARY_BY_YEAR)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def get_total_invested(self) -> float:
        """Calcule le montant total investi dans le portefeuille"""
        positions = self.get_current_positions()
        return sum(p.total_invested for p in positions)

    def get_unique_tickers(self) -> List[str]:
        """Récupère la liste des tickers uniques ayant des positions actuelles"""
        positions = self.get_current_positions()
        return [p.ticker for p in positions]

    # ==========================================================================
    # BACKUP ET MAINTENANCE
    # ==========================================================================

    def create_backup(self, backup_name: str = None) -> str:
        """
        Crée une sauvegarde de la base de données

        Args:
            backup_name: Nom du fichier de backup (optionnel)
                        Si None, utilise un nom avec timestamp

        Returns:
            Le chemin complet du fichier de backup créé
        """
        # Créer le dossier de backup s'il n'existe pas
        os.makedirs(BACKUP_PATH, exist_ok=True)

        # Générer un nom de fichier si non fourni
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"portfolio_backup_{timestamp}.db"

        backup_path = os.path.join(BACKUP_PATH, backup_name)

        # Copier le fichier de base de données
        shutil.copy2(self.db_path, backup_path)

        return backup_path

    def restore_backup(self, backup_path: str) -> bool:
        """
        Restaure une sauvegarde de la base de données

        Args:
            backup_path: Chemin vers le fichier de backup

        Returns:
            True si la restauration a réussi

        Raises:
            FileNotFoundError: Si le fichier de backup n'existe pas
        """
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Le fichier de backup {backup_path} n'existe pas")

        # Créer un backup de la DB actuelle avant de restaurer
        self.create_backup("pre_restore_backup.db")

        # Restaurer le backup
        shutil.copy2(backup_path, self.db_path)

        # Réinitialiser la connexion
        self._initialize_database()

        return True

    def vacuum(self):
        """Optimise la base de données (récupère l'espace et optimise)"""
        with self.get_connection() as conn:
            conn.execute("VACUUM")

    def get_realized_gains_total(self) -> float:
        """Calcule le total des gains réalisés (ventes)"""
        # Pour simplifier, on retourne 0 pour l'instant
        # Une implémentation complète nécessiterait de calculer avec FIFO
        return 0.0

    def get_total_dividends_received(self) -> float:
        """Calcule le total des dividendes reçus"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT SUM(net_amount) as total FROM dividends WHERE status = 'REÇU'"
            )
            row = cursor.fetchone()
            if row and row['total']:
                return row['total']
            return 0.0

    def get_total_fees_paid(self) -> float:
        """Calcule le total des frais payés"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(fees) as total FROM transactions")
            row = cursor.fetchone()
            if row and row['total']:
                return row['total']
            return 0.0

    def backup_database(self, backup_path: str = None) -> bool:
        """Alias pour create_backup"""
        try:
            self.create_backup(backup_path)
            return True
        except:
            return False

    def get_database_stats(self) -> Dict[str, Any]:
        """Retourne des statistiques sur la base de données"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            # Nombre de transactions
            cursor.execute("SELECT COUNT(*) as count FROM transactions")
            stats['transactions_count'] = cursor.fetchone()['count']

            # Nombre de dividendes
            cursor.execute("SELECT COUNT(*) as count FROM dividends")
            stats['dividends_count'] = cursor.fetchone()['count']

            # Nombre de positions actuelles
            stats['positions_count'] = len(self.get_current_positions())

            # Taille du fichier DB
            stats['db_size_mb'] = os.path.getsize(self.db_path) / (1024 * 1024)

            return stats
