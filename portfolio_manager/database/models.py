# -*- coding: utf-8 -*-
"""
Modèles de données pour la base de données SQLite
Définit les schémas des tables et les requêtes SQL
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# ==============================================================================
# SCHÉMAS SQL DES TABLES
# ==============================================================================

# Table des transactions (achats et ventes d'actions)
CREATE_TRANSACTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    company_name TEXT NOT NULL,
    transaction_type TEXT NOT NULL CHECK(transaction_type IN ('ACHAT', 'VENTE')),
    quantity REAL NOT NULL CHECK(quantity > 0),
    price_per_share REAL NOT NULL CHECK(price_per_share > 0),
    transaction_date TEXT NOT NULL,
    total_cost REAL NOT NULL,
    fees REAL NOT NULL DEFAULT 1.0,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

# Index pour optimiser les requêtes fréquentes
CREATE_TRANSACTIONS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_ticker ON transactions(ticker)",
    "CREATE INDEX IF NOT EXISTS idx_date ON transactions(transaction_date)",
    "CREATE INDEX IF NOT EXISTS idx_type ON transactions(transaction_type)"
]

# Table des dividendes
CREATE_DIVIDENDS_TABLE = """
CREATE TABLE IF NOT EXISTS dividends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    company_name TEXT NOT NULL,
    amount_per_share REAL NOT NULL CHECK(amount_per_share > 0),
    ex_dividend_date TEXT NOT NULL,
    payment_date TEXT,
    quantity_owned REAL NOT NULL CHECK(quantity_owned > 0),
    gross_amount REAL NOT NULL,
    tax_amount REAL NOT NULL DEFAULT 0,
    net_amount REAL NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('PRÉVU', 'REÇU')) DEFAULT 'PRÉVU',
    received_date TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticker) REFERENCES transactions(ticker)
)
"""

# Index pour la table dividendes
CREATE_DIVIDENDS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_dividend_ticker ON dividends(ticker)",
    "CREATE INDEX IF NOT EXISTS idx_dividend_status ON dividends(status)",
    "CREATE INDEX IF NOT EXISTS idx_dividend_payment_date ON dividends(payment_date)"
]

# Table de cache pour les données de marché
CREATE_MARKET_CACHE_TABLE = """
CREATE TABLE IF NOT EXISTS market_cache (
    ticker TEXT PRIMARY KEY,
    current_price REAL,
    previous_close REAL,
    change_percent REAL,
    volume INTEGER,
    market_cap REAL,
    last_updated TEXT NOT NULL,
    FOREIGN KEY (ticker) REFERENCES transactions(ticker)
)
"""

# Table pour stocker l'historique des prix (optionnel, pour les graphiques)
CREATE_PRICE_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL NOT NULL,
    volume INTEGER,
    UNIQUE(ticker, date),
    FOREIGN KEY (ticker) REFERENCES transactions(ticker)
)
"""

# Index pour l'historique des prix
CREATE_PRICE_HISTORY_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_price_ticker ON price_history(ticker)",
    "CREATE INDEX IF NOT EXISTS idx_price_date ON price_history(date)"
]

# ==============================================================================
# DATACLASSES POUR MANIPULER LES DONNÉES
# ==============================================================================

@dataclass
class Transaction:
    """Représente une transaction (achat ou vente)"""
    ticker: str
    company_name: str
    transaction_type: str  # 'ACHAT' ou 'VENTE'
    quantity: float
    price_per_share: float
    transaction_date: str
    total_cost: float
    fees: float = 1.0
    notes: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        """Validation et calculs automatiques"""
        # Validation du type de transaction
        if self.transaction_type not in ['ACHAT', 'VENTE']:
            raise ValueError("transaction_type doit être 'ACHAT' ou 'VENTE'")

        # Si total_cost n'est pas fourni, le calculer
        if self.total_cost == 0:
            if self.transaction_type == 'ACHAT':
                # Achat : on paie le prix + les frais
                self.total_cost = (self.quantity * self.price_per_share) + self.fees
            else:
                # Vente : on reçoit le prix - les frais
                self.total_cost = (self.quantity * self.price_per_share) - self.fees


@dataclass
class Dividend:
    """Représente un dividende"""
    ticker: str
    company_name: str
    amount_per_share: float
    ex_dividend_date: str
    quantity_owned: float
    gross_amount: float
    tax_amount: float
    net_amount: float
    status: str = 'PRÉVU'  # 'PRÉVU' ou 'REÇU'
    payment_date: Optional[str] = None
    received_date: Optional[str] = None
    notes: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        """Validation et calculs automatiques"""
        if self.status not in ['PRÉVU', 'REÇU']:
            raise ValueError("status doit être 'PRÉVU' ou 'REÇU'")

        # Calculer gross_amount si non fourni
        if self.gross_amount == 0:
            self.gross_amount = self.amount_per_share * self.quantity_owned

        # Calculer net_amount si non fourni
        if self.net_amount == 0:
            self.net_amount = self.gross_amount - self.tax_amount


@dataclass
class MarketData:
    """Représente les données de marché pour une action"""
    ticker: str
    current_price: float
    previous_close: float
    change_percent: float
    volume: int = 0
    market_cap: float = 0
    last_updated: Optional[str] = None

    @property
    def change_amount(self) -> float:
        """Calcul du montant de variation"""
        return self.current_price - self.previous_close

    @property
    def is_gain(self) -> bool:
        """True si l'action est en hausse"""
        return self.change_percent > 0


@dataclass
class Position:
    """Représente une position actuelle dans le portefeuille"""
    ticker: str
    company_name: str
    quantity: float
    average_buy_price: float  # Prix de revient moyen (PRU)
    total_invested: float     # Montant total investi (incluant frais)
    current_price: float = 0
    current_value: float = 0
    unrealized_pnl: float = 0
    unrealized_pnl_percent: float = 0

    # Alias pour compatibilité avec différents noms
    @property
    def pru(self) -> float:
        """Alias pour average_buy_price (Prix de Revient Unitaire)"""
        return self.average_buy_price

    @property
    def unrealized_gain_loss(self) -> float:
        """Alias pour unrealized_pnl"""
        return self.unrealized_pnl

    @property
    def unrealized_gain_loss_percent(self) -> float:
        """Alias pour unrealized_pnl_percent"""
        return self.unrealized_pnl_percent

    def update_current_values(self, current_price: float):
        """Met à jour les valeurs actuelles en fonction du prix du marché"""
        self.current_price = current_price
        self.current_value = self.quantity * current_price
        self.unrealized_pnl = self.current_value - self.total_invested

        if self.total_invested > 0:
            self.unrealized_pnl_percent = (self.unrealized_pnl / self.total_invested) * 100
        else:
            self.unrealized_pnl_percent = 0


@dataclass
class PriceHistory:
    """Représente un point de l'historique des prix"""
    ticker: str
    date: str
    close: float
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[int] = None
    id: Optional[int] = None


# ==============================================================================
# REQUÊTES SQL PRÉPARÉES
# ==============================================================================

class Queries:
    """Classe contenant toutes les requêtes SQL utilisées par l'application"""

    # ========== TRANSACTIONS ==========

    INSERT_TRANSACTION = """
        INSERT INTO transactions
        (ticker, company_name, transaction_type, quantity, price_per_share,
         transaction_date, total_cost, fees, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    UPDATE_TRANSACTION = """
        UPDATE transactions
        SET ticker = ?, company_name = ?, transaction_type = ?, quantity = ?,
            price_per_share = ?, transaction_date = ?, total_cost = ?,
            fees = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """

    DELETE_TRANSACTION = "DELETE FROM transactions WHERE id = ?"

    GET_TRANSACTION_BY_ID = "SELECT * FROM transactions WHERE id = ?"

    GET_ALL_TRANSACTIONS = """
        SELECT * FROM transactions
        ORDER BY transaction_date DESC, id DESC
    """

    GET_TRANSACTIONS_BY_TICKER = """
        SELECT * FROM transactions
        WHERE ticker = ?
        ORDER BY transaction_date ASC, id ASC
    """

    GET_TRANSACTIONS_BY_TYPE = """
        SELECT * FROM transactions
        WHERE transaction_type = ?
        ORDER BY transaction_date DESC
    """

    GET_TRANSACTIONS_BY_DATE_RANGE = """
        SELECT * FROM transactions
        WHERE transaction_date BETWEEN ? AND ?
        ORDER BY transaction_date DESC
    """

    # ========== DIVIDENDES ==========

    INSERT_DIVIDEND = """
        INSERT INTO dividends
        (ticker, company_name, amount_per_share, ex_dividend_date, payment_date,
         quantity_owned, gross_amount, tax_amount, net_amount, status, received_date, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    UPDATE_DIVIDEND = """
        UPDATE dividends
        SET ticker = ?, company_name = ?, amount_per_share = ?, ex_dividend_date = ?,
            payment_date = ?, quantity_owned = ?, gross_amount = ?, tax_amount = ?,
            net_amount = ?, status = ?, received_date = ?, notes = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """

    DELETE_DIVIDEND = "DELETE FROM dividends WHERE id = ?"

    GET_DIVIDEND_BY_ID = "SELECT * FROM dividends WHERE id = ?"

    GET_ALL_DIVIDENDS = """
        SELECT * FROM dividends
        ORDER BY payment_date DESC, ex_dividend_date DESC
    """

    GET_DIVIDENDS_BY_TICKER = """
        SELECT * FROM dividends
        WHERE ticker = ?
        ORDER BY payment_date DESC
    """

    GET_DIVIDENDS_BY_STATUS = """
        SELECT * FROM dividends
        WHERE status = ?
        ORDER BY payment_date DESC
    """

    GET_DIVIDENDS_BY_YEAR = """
        SELECT * FROM dividends
        WHERE strftime('%Y', COALESCE(payment_date, received_date, ex_dividend_date)) = ?
        ORDER BY payment_date DESC
    """

    # ========== CACHE MARCHÉ ==========

    UPSERT_MARKET_CACHE = """
        INSERT OR REPLACE INTO market_cache
        (ticker, current_price, previous_close, change_percent, volume,
         market_cap, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    GET_MARKET_CACHE = "SELECT * FROM market_cache WHERE ticker = ?"

    GET_ALL_MARKET_CACHE = "SELECT * FROM market_cache"

    GET_LAST_MARKET_REFRESH = """
        SELECT MAX(last_updated) AS last_updated
        FROM market_cache
    """

    DELETE_OLD_CACHE = """
        DELETE FROM market_cache
        WHERE julianday('now') - julianday(last_updated) > ?
    """

    # ========== HISTORIQUE DES PRIX ==========

    INSERT_PRICE_HISTORY = """
        INSERT OR REPLACE INTO price_history
        (ticker, date, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    GET_PRICE_HISTORY = """
        SELECT * FROM price_history
        WHERE ticker = ? AND date BETWEEN ? AND ?
        ORDER BY date ASC
    """

    GET_LATEST_PRICE = """
        SELECT * FROM price_history
        WHERE ticker = ?
        ORDER BY date DESC
        LIMIT 1
    """

    # ========== STATISTIQUES ET ANALYSES ==========

    # Obtenir toutes les positions actuelles (actions détenues)
    GET_CURRENT_POSITIONS = """
        SELECT
            ticker,
            MAX(company_name) as company_name,
            SUM(CASE WHEN transaction_type = 'ACHAT' THEN quantity ELSE -quantity END) as quantity,
            SUM(CASE WHEN transaction_type = 'ACHAT' THEN total_cost ELSE -total_cost END) as total_invested
        FROM transactions
        GROUP BY ticker
        HAVING quantity > 0
        ORDER BY ticker
    """

    # Calculer les dividendes totaux par année
    GET_DIVIDENDS_SUMMARY_BY_YEAR = """
        SELECT
            strftime('%Y', payment_date) as year,
            COUNT(*) as count,
            SUM(gross_amount) as total_gross,
            SUM(tax_amount) as total_tax,
            SUM(net_amount) as total_net
        FROM dividends
        WHERE status = 'REÇU'
        GROUP BY year
        ORDER BY year DESC
    """

    # Calculer le total investi
    GET_TOTAL_INVESTED = """
        SELECT
            SUM(CASE WHEN transaction_type = 'ACHAT' THEN total_cost ELSE -total_cost END) as total_invested
        FROM transactions
    """

    # Obtenir les prochains dividendes
    GET_UPCOMING_DIVIDENDS = """
        SELECT * FROM dividends
        WHERE status = 'PRÉVU'
        AND payment_date >= date('now')
        ORDER BY payment_date ASC
        LIMIT ?
    """


# ==============================================================================
# FONCTIONS UTILITAIRES
# ==============================================================================

def dict_to_transaction(data: dict) -> Transaction:
    """Convertit un dictionnaire (résultat de requête SQL) en objet Transaction"""
    return Transaction(
        id=data.get('id'),
        ticker=data['ticker'],
        company_name=data['company_name'],
        transaction_type=data['transaction_type'],
        quantity=data['quantity'],
        price_per_share=data['price_per_share'],
        transaction_date=data['transaction_date'],
        total_cost=data['total_cost'],
        fees=data.get('fees', 1.0),
        notes=data.get('notes'),
        created_at=data.get('created_at'),
        updated_at=data.get('updated_at')
    )


def dict_to_dividend(data: dict) -> Dividend:
    """Convertit un dictionnaire en objet Dividend"""
    return Dividend(
        id=data.get('id'),
        ticker=data['ticker'],
        company_name=data['company_name'],
        amount_per_share=data['amount_per_share'],
        ex_dividend_date=data['ex_dividend_date'],
        payment_date=data.get('payment_date'),
        quantity_owned=data['quantity_owned'],
        gross_amount=data['gross_amount'],
        tax_amount=data['tax_amount'],
        net_amount=data['net_amount'],
        status=data.get('status', 'PRÉVU'),
        received_date=data.get('received_date'),
        notes=data.get('notes'),
        created_at=data.get('created_at'),
        updated_at=data.get('updated_at')
    )


def dict_to_market_data(data: dict) -> MarketData:
    """Convertit un dictionnaire en objet MarketData"""
    return MarketData(
        ticker=data['ticker'],
        current_price=data['current_price'],
        previous_close=data['previous_close'],
        change_percent=data['change_percent'],
        volume=data.get('volume', 0),
        market_cap=data.get('market_cap', 0),
        last_updated=data.get('last_updated')
    )
