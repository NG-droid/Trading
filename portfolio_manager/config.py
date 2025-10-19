# -*- coding: utf-8 -*-
"""
Configuration de l'application Portfolio Manager
Contient toutes les constantes et paramètres de l'application
"""

# ==============================================================================
# FRAIS TRADE REPUBLIC
# ==============================================================================
TRANSACTION_FEE = 1.0  # ¬ par ordre (achat ou vente)
CUSTODY_FEE = 0.0      # Pas de frais de garde
INACTIVITY_FEE = 0.0   # Pas de frais d'inactivité

# ==============================================================================
# FISCALITÉ FRANÇAISE
# ==============================================================================

# Prélèvement Forfaitaire Unique (PFU / Flat Tax)
FLAT_TAX_RATE = 0.30              # 30% total
INCOME_TAX_RATE = 0.128           # 12.8% impôt sur le revenu
SOCIAL_TAX_RATE = 0.172           # 17.2% prélèvements sociaux
CSG_DEDUCTIBLE_RATE = 0.068       # 6.8% de CSG déductible (sur les 17.2%)

# Option barème progressif (si choisi au lieu du PFU)
DIVIDEND_ALLOWANCE_RATE = 0.40    # Abattement de 40% sur les dividendes
# Note: Le taux d'imposition dépend de la tranche marginale du contribuable

# ==============================================================================
# API ET DONNÉES DE MARCHÉ
# ==============================================================================

# Cache des données
CACHE_DURATION = 300               # 5 minutes en secondes
MAX_CACHE_AGE = 86400              # 24 heures max pour données en cache

# Alpha Vantage API (alternative à Yahoo Finance)
ALPHA_VANTAGE_API_KEY = "N91CVN62E6UQYWF7"  # Clé API gratuite (25 requêtes/jour - LIMITE ATTEINTE)
USE_ALPHA_VANTAGE = False          # Désactivé: limite atteinte. Utiliser Yahoo Finance maintenant qu'AdGuard est configuré

# yfinance (fallback si Alpha Vantage échoue)
MARKET_OPEN_HOUR = 9               # Heure d'ouverture du marché
MARKET_CLOSE_HOUR = 17             # Heure de fermeture du marché
MARKET_TIMEZONE = "Europe/Paris"   # Fuseau horaire

# Suffixes pour les tickers
PARIS_EXCHANGE_SUFFIX = ".PA"      # Euronext Paris (ex: "AI.PA" pour Air Liquide)

# Timeout pour les requêtes API
API_TIMEOUT = 10                   # secondes

# ==============================================================================
# BASE DE DONNÉES
# ==============================================================================

DB_NAME = "portfolio.db"
DB_PATH = "./data/"                # Chemin relatif vers le dossier de données
BACKUP_PATH = "./backups/"         # Chemin pour les sauvegardes

# ==============================================================================
# INTERFACE UTILISATEUR
# ==============================================================================

# Devise
DEFAULT_CURRENCY = "EUR"
CURRENCY_SYMBOL = "€"

# Formats
DATE_FORMAT = "%d/%m/%Y"           # Format français : JJ/MM/AAAA
DATETIME_FORMAT = "%d/%m/%Y %H:%M"
DECIMAL_PLACES = 2                 # Nombre de décimales pour les montants

# Couleurs (mode clair/sombre sera géré par CustomTkinter)
COLOR_GAIN = "#10b981"             # Vert pour les gains
COLOR_LOSS = "#ef4444"             # Rouge pour les pertes
COLOR_NEUTRAL = "#6b7280"          # Gris neutre
COLOR_PRIMARY = "#3b82f6"          # Bleu principal

# Taille de la fenêtre
WINDOW_TITLE = "Portfolio Manager - Trade Republic"
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
WINDOW_MIN_WIDTH = 1200
WINDOW_MIN_HEIGHT = 700

# Couleurs supplémentaires
COLOR_SUCCESS = "#10b981"           # Vert succès
COLOR_DANGER = "#ef4444"            # Rouge danger
COLOR_WARNING = "#f59e0b"           # Orange warning
COLOR_INFO = "#3b82f6"              # Bleu info
COLOR_SECONDARY = "#6b7280"         # Gris secondaire

# ==============================================================================
# EXPORT
# ==============================================================================

EXPORT_PATH = "./exports/"         # Chemin pour les exports Excel
EXCEL_SHEET_NAMES = {
    "summary": "Résumé",
    "transactions": "Transactions",
    "dividends": "Dividendes",
    "positions": "Positions",
    "tax": "Fiscalité"
}

# ==============================================================================
# VALIDATION
# ==============================================================================

# Contraintes de validation
MIN_QUANTITY = 0.0001              # Quantité minimale (pour actions fractionnées)
MAX_QUANTITY = 1000000             # Quantité maximale raisonnable
MIN_PRICE = 0.01                   # Prix minimal par action
MAX_PRICE = 100000                 # Prix maximal raisonnable par action

# ==============================================================================
# FONCTIONNALITÉS
# ==============================================================================

# Alertes
DIVIDEND_ALERT_DAYS = 7            # Alerter si dividende dans X jours
ENABLE_NOTIFICATIONS = True        # Activer les notifications

# Backup
AUTO_BACKUP = True                 # Sauvegarde automatique de la DB
BACKUP_FREQUENCY_DAYS = 7          # Fréquence des backups automatiques
MAX_BACKUPS = 10                   # Nombre max de backups à conserver

# Performance
ASYNC_DATA_LOADING = True          # Chargement asynchrone des données de marché
BATCH_SIZE = 10                    # Nombre de tickers à charger simultanément

# ==============================================================================
# MÉTHODES DE CALCUL
# ==============================================================================

# Méthode de calcul des plus-values
PV_CALCULATION_METHOD = "FIFO"     # First In First Out (obligatoire en France)
# Note: La méthode FIFO est obligatoire pour le calcul fiscal en France

# ==============================================================================
# ACTIONS CAC 40 (LISTE DE RÉFÉRENCE)
# ==============================================================================

CAC40_TICKERS = {
    "AI.PA": "Air Liquide",
    "AIR.PA": "Airbus",
    "ALO.PA": "Alstom",
    "MT.AS": "ArcelorMittal",
    "CS.PA": "AXA",
    "BNP.PA": "BNP Paribas",
    "EN.PA": "Bouygues",
    "CAP.PA": "Capgemini",
    "CA.PA": "Carrefour",
    "ACA.PA": "Crédit Agricole",
    "BN.PA": "Danone",
    "ENGI.PA": "ENGIE",
    "EL.PA": "EssilorLuxottica",
    "RMS.PA": "Hermès",
    "KER.PA": "Kering",
    "OR.PA": "L'Oréal",
    "LR.PA": "Legrand",
    "MC.PA": "LVMH",
    "ML.PA": "Michelin",
    "ORA.PA": "Orange",
    "RI.PA": "Pernod Ricard",
    "PUB.PA": "Publicis",
    "RNO.PA": "Renault",
    "SAF.PA": "Safran",
    "SGO.PA": "Saint-Gobain",
    "SAN.PA": "Sanofi",
    "SU.PA": "Schneider Electric",
    "GLE.PA": "Société Générale",
    "STLA.PA": "Stellantis",
    "STM.PA": "STMicroelectronics",
    "TEP.PA": "Teleperformance",
    "HO.PA": "Thales",
    "TTE.PA": "TotalEnergies",
    "URW.AS": "Unibail-Rodamco-Westfield",
    "VIE.PA": "Veolia",
    "DG.PA": "Vinci",
    "VIV.PA": "Vivendi",
    "WLN.PA": "Worldline"
}

# Certains tickers Yahoo Finance ont changé de suffixe ou de place de cotation.
# Cette table permet de conserver les anciens symboles dans la base tout en
# requêtant les tickers actifs lors des appels API.
YAHOO_TICKER_ALIASES = {
    "FP.PA": "TTE.PA",
    "MT.PA": "MT.AS",
    "STLAP.PA": "STLA.PA",
    "STMPA.PA": "STM.PA",
    "URW.PA": "URW.AS",
}

# ==============================================================================
# MESSAGES
# ==============================================================================

# Messages d'erreur
ERROR_MESSAGES = {
    "invalid_ticker": "Le ticker saisi est invalide. Format attendu: XX.PA",
    "invalid_quantity": f"La quantité doit être entre {MIN_QUANTITY} et {MAX_QUANTITY}",
    "invalid_price": f"Le prix doit être entre {MIN_PRICE}¬ et {MAX_PRICE}¬",
    "invalid_date": "La date saisie est invalide",
    "future_date": "La date ne peut pas être dans le futur",
    "api_error": "Erreur lors de la récupération des données de marché",
    "db_error": "Erreur de base de données",
    "insufficient_shares": "Quantité insuffisante d'actions pour cette vente"
}

# Messages de succès
SUCCESS_MESSAGES = {
    "transaction_added": "Transaction ajoutée avec succès",
    "transaction_updated": "Transaction modifiée avec succès",
    "transaction_deleted": "Transaction supprimée avec succès",
    "export_success": "Export Excel créé avec succès",
    "backup_success": "Sauvegarde créée avec succès"
}

# ==============================================================================
# CONFIGURATION DE DÉVELOPPEMENT / PRODUCTION
# ==============================================================================

DEBUG_MODE = False                 # Mode debug (logs détaillés)
LOG_LEVEL = "INFO"                 # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = "portfolio_manager.log"
