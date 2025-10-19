# -*- coding: utf-8 -*-
"""
API pour récupérer les données de marché via Alpha Vantage ou yfinance
Gère le cache, les erreurs et les requêtes par batch
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import time

from ..database.models import MarketData, PriceHistory
from ..database.db_manager import DatabaseManager
from ..config import (
    CACHE_DURATION, MAX_CACHE_AGE,
    PARIS_EXCHANGE_SUFFIX, ERROR_MESSAGES,
    USE_ALPHA_VANTAGE
)
from .alpha_vantage import AlphaVantageAPI


class MarketDataAPI:
    """
    Wrapper pour yfinance avec gestion du cache et des erreurs
    """

    def __init__(self, db_manager: DatabaseManager = None):
        """
        Initialise l'API

        Args:
            db_manager: Gestionnaire de base de données (optionnel)
        """
        self.db = db_manager or DatabaseManager()

        # Initialiser Alpha Vantage si activé
        if USE_ALPHA_VANTAGE:
            try:
                self.alpha_vantage = AlphaVantageAPI()
                print("✅ Alpha Vantage API initialisée")
            except Exception as e:
                print(f"⚠️ Impossible d'initialiser Alpha Vantage: {e}")
                self.alpha_vantage = None
        else:
            self.alpha_vantage = None

    def get_current_price(self, ticker: str, use_cache: bool = True) -> Optional[MarketData]:
        """
        Récupère le prix actuel d'une action

        Args:
            ticker: Symbole de l'action (ex: "AI.PA")
            use_cache: Utiliser le cache si disponible

        Returns:
            MarketData ou None si erreur
        """
        # Vérifier le cache si demandé
        if use_cache:
            cached_data = self._get_from_cache(ticker)
            if cached_data:
                return cached_data

        # Essayer Alpha Vantage en premier si activé
        if self.alpha_vantage:
            try:
                market_data = self.alpha_vantage.get_quote(ticker)
                if market_data:
                    self.db.upsert_market_cache(market_data)
                    return market_data
                else:
                    # Alpha Vantage n'a pas trouvé ce ticker
                    print(f"⚠️ Alpha Vantage: ticker {ticker} non trouvé")
                    return None
            except Exception as e:
                print(f"⚠️ Alpha Vantage échec pour {ticker}: {e}")
                return None

        # Fallback: Récupérer depuis yfinance (uniquement si Alpha Vantage non activé)
        if not self.alpha_vantage:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info

                # Vérifier que les données sont valides
                if not info or 'currentPrice' not in info:
                    # Essayer avec fast_info (plus rapide mais moins de données)
                    try:
                        current_price = stock.fast_info['lastPrice']
                        previous_close = stock.fast_info['previousClose']
                    except:
                        return None
                else:
                    current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                    previous_close = info.get('previousClose', info.get('regularMarketPreviousClose', 0))

                if current_price == 0:
                    return None

                # Calculer la variation
                change_percent = 0
                if previous_close > 0:
                    change_percent = ((current_price - previous_close) / previous_close) * 100

                # Créer l'objet MarketData
                market_data = MarketData(
                    ticker=ticker,
                    current_price=current_price,
                    previous_close=previous_close,
                    change_percent=change_percent,
                    volume=info.get('volume', 0),
                    market_cap=info.get('marketCap', 0),
                    last_updated=datetime.now().isoformat()
                )

                # Mettre en cache
                self.db.upsert_market_cache(market_data)

                return market_data

            except Exception as e:
                print(f"Erreur lors de la récupération de {ticker}: {e}")
                return None

        return None

    def get_multiple_prices(
        self,
        tickers: List[str],
        use_cache: bool = True
    ) -> Dict[str, MarketData]:
        """
        Récupère les prix de plusieurs actions en batch

        Args:
            tickers: Liste des tickers
            use_cache: Utiliser le cache si disponible

        Returns:
            Dictionnaire {ticker: MarketData}
        """
        results = {}

        # Tickers à récupérer (pas en cache ou cache expiré)
        tickers_to_fetch = []

        for ticker in tickers:
            if use_cache:
                cached = self._get_from_cache(ticker)
                if cached:
                    results[ticker] = cached
                    continue
            tickers_to_fetch.append(ticker)

        # Récupérer les tickers manquants
        if tickers_to_fetch:
            # Essayer Alpha Vantage en premier si activé
            if self.alpha_vantage:
                try:
                    print(f"🔄 Récupération de {len(tickers_to_fetch)} tickers via Alpha Vantage...")
                    alpha_results = self.alpha_vantage.get_multiple_quotes(tickers_to_fetch)
                    for ticker, market_data in alpha_results.items():
                        results[ticker] = market_data
                        self.db.upsert_market_cache(market_data)

                    # Alpha Vantage activé : retourner directement, pas de fallback yfinance
                    print(f"✅ Alpha Vantage: {len(alpha_results)}/{len(tickers_to_fetch)} tickers récupérés")
                    return results

                except Exception as e:
                    print(f"⚠️ Alpha Vantage échec batch: {e}")
                    # Retourner les résultats partiels sans fallback yfinance
                    return results

            # Fallback yfinance uniquement si Alpha Vantage n'est PAS activé
            if tickers_to_fetch and not self.alpha_vantage:
                # yfinance permet de télécharger plusieurs tickers à la fois
                try:
                    # Créer une chaîne de tickers séparés par des espaces
                    tickers_str = " ".join(tickers_to_fetch)
                    data = yf.download(
                        tickers_str,
                        period="2d",  # 2 jours pour avoir previous_close
                        interval="1d",
                        progress=False
                    )

                    # Si un seul ticker, data a une structure différente
                    if len(tickers_to_fetch) == 1:
                        ticker = tickers_to_fetch[0]
                        if not data.empty and len(data) >= 1:
                            current_price = float(data['Close'].iloc[-1])
                            previous_close = float(data['Close'].iloc[-2]) if len(data) >= 2 else current_price
                            change_percent = ((current_price - previous_close) / previous_close * 100) if previous_close > 0 else 0

                            market_data = MarketData(
                                ticker=ticker,
                                current_price=current_price,
                                previous_close=previous_close,
                                change_percent=change_percent,
                                volume=int(data['Volume'].iloc[-1]) if 'Volume' in data else 0,
                                market_cap=0,
                                last_updated=datetime.now().isoformat()
                            )
                            results[ticker] = market_data
                            self.db.upsert_market_cache(market_data)
                    else:
                        # Plusieurs tickers
                        for ticker in tickers_to_fetch:
                            try:
                                if ticker not in data['Close'].columns:
                                    continue

                                ticker_data = data['Close'][ticker]
                                if ticker_data.empty or len(ticker_data) < 1:
                                    continue

                                current_price = float(ticker_data.iloc[-1])
                                previous_close = float(ticker_data.iloc[-2]) if len(ticker_data) >= 2 else current_price
                                change_percent = ((current_price - previous_close) / previous_close * 100) if previous_close > 0 else 0

                                volume = 0
                                if 'Volume' in data and ticker in data['Volume'].columns:
                                    volume = int(data['Volume'][ticker].iloc[-1])

                                market_data = MarketData(
                                    ticker=ticker,
                                    current_price=current_price,
                                    previous_close=previous_close,
                                    change_percent=change_percent,
                                    volume=volume,
                                    market_cap=0,
                                    last_updated=datetime.now().isoformat()
                                )
                                results[ticker] = market_data
                                self.db.upsert_market_cache(market_data)

                            except Exception as e:
                                print(f"Erreur pour {ticker}: {e}")
                                continue

                except Exception as e:
                    print(f"Erreur batch download: {e}")
                    # Fallback: récupérer un par un
                    for ticker in tickers_to_fetch:
                        data = self.get_current_price(ticker, use_cache=False)
                        if data:
                            results[ticker] = data

        return results

    def get_price_history(
        self,
        ticker: str,
        period: str = "1y",
        interval: str = "1d"
    ) -> List[PriceHistory]:
        """
        Récupère l'historique des prix

        Args:
            ticker: Symbole de l'action
            period: Période (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Intervalle (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            Liste de PriceHistory
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period, interval=interval)

            if hist.empty:
                return []

            history = []
            for date, row in hist.iterrows():
                price_point = PriceHistory(
                    ticker=ticker,
                    date=date.strftime("%Y-%m-%d"),
                    close=float(row['Close']),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    volume=int(row['Volume']) if 'Volume' in row else 0
                )
                history.append(price_point)

            return history

        except Exception as e:
            print(f"Erreur récupération historique {ticker}: {e}")
            return []

    def get_company_info(self, ticker: str) -> Dict:
        """
        Récupère les informations sur l'entreprise

        Args:
            ticker: Symbole de l'action

        Returns:
            Dictionnaire avec les informations
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            return {
                'name': info.get('longName', info.get('shortName', ticker)),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'website': info.get('website', ''),
                'description': info.get('longBusinessSummary', ''),
                'employees': info.get('fullTimeEmployees', 0),
                'city': info.get('city', ''),
                'country': info.get('country', ''),
            }

        except Exception as e:
            print(f"Erreur récupération info {ticker}: {e}")
            return {'name': ticker}

    def validate_ticker(self, ticker: str) -> bool:
        """
        Vérifie si un ticker est valide

        Args:
            ticker: Symbole à vérifier

        Returns:
            True si valide
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Vérifier qu'on a au moins quelques infos
            return bool(info and len(info) > 5)

        except:
            return False

    def _get_from_cache(self, ticker: str) -> Optional[MarketData]:
        """
        Récupère les données depuis le cache si valide

        Args:
            ticker: Symbole de l'action

        Returns:
            MarketData ou None si cache expiré/inexistant
        """
        cached = self.db.get_market_cache(ticker)

        if not cached:
            return None

        # Vérifier l'âge du cache
        try:
            last_updated = datetime.fromisoformat(cached.last_updated)
            age_seconds = (datetime.now() - last_updated).total_seconds()

            if age_seconds < CACHE_DURATION:
                return cached

            # Accepter des données plus anciennes si disponibles (mode hors ligne)
            if age_seconds < MAX_CACHE_AGE:
                return cached

        except Exception:
            return cached

        return None

    def refresh_all_cache(self, tickers: List[str]) -> int:
        """
        Rafraîchit le cache pour tous les tickers

        Args:
            tickers: Liste des tickers à rafraîchir

        Returns:
            Nombre de tickers mis à jour avec succès
        """
        results = self.get_multiple_prices(tickers, use_cache=False)
        return len(results)

    def clean_old_cache(self, max_age_days: int = 1):
        """
        Nettoie les données de cache trop anciennes

        Args:
            max_age_days: Âge maximum en jours
        """
        self.db.clean_old_cache(max_age_days)

    def get_real_time_quote(self, ticker: str) -> Optional[Dict]:
        """
        Récupère un quote en temps réel (avec plus de détails)

        Args:
            ticker: Symbole de l'action

        Returns:
            Dictionnaire avec les détails du quote
        """
        try:
            stock = yf.Ticker(ticker)

            # Utiliser fast_info pour les données rapides
            try:
                fast = stock.fast_info
                return {
                    'price': fast.get('lastPrice', 0),
                    'previous_close': fast.get('previousClose', 0),
                    'open': fast.get('open', 0),
                    'day_high': fast.get('dayHigh', 0),
                    'day_low': fast.get('dayLow', 0),
                    'volume': fast.get('lastVolume', 0),
                    'market_cap': fast.get('marketCap', 0),
                }
            except:
                # Fallback sur info
                info = stock.info
                return {
                    'price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
                    'previous_close': info.get('previousClose', 0),
                    'open': info.get('open', info.get('regularMarketOpen', 0)),
                    'day_high': info.get('dayHigh', info.get('regularMarketDayHigh', 0)),
                    'day_low': info.get('dayLow', info.get('regularMarketDayLow', 0)),
                    'volume': info.get('volume', 0),
                    'market_cap': info.get('marketCap', 0),
                }

        except Exception as e:
            print(f"Erreur récupération quote {ticker}: {e}")
            return None


# Fonction utilitaire pour formater un ticker Euronext Paris
def format_ticker_paris(symbol: str) -> str:
    """
    Formate un ticker pour Euronext Paris

    Args:
        symbol: Symbole court (ex: "AI", "MC")

    Returns:
        Ticker complet (ex: "AI.PA", "MC.PA")
    """
    if not symbol.endswith(PARIS_EXCHANGE_SUFFIX):
        return f"{symbol}{PARIS_EXCHANGE_SUFFIX}"
    return symbol


# Fonction utilitaire pour extraire le symbole court
def extract_symbol(ticker: str) -> str:
    """
    Extrait le symbole court d'un ticker

    Args:
        ticker: Ticker complet (ex: "AI.PA")

    Returns:
        Symbole court (ex: "AI")
    """
    return ticker.replace(PARIS_EXCHANGE_SUFFIX, "")
