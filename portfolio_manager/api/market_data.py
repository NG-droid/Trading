# -*- coding: utf-8 -*-
"""
API pour récupérer les données de marché via Alpha Vantage ou yfinance
Gère le cache, les erreurs et les requêtes par batch
"""

import yfinance as yf

try:
    from yfinance.exceptions import YFPricesMissingError  # type: ignore
except ImportError:  # Compatibilité avec anciennes versions de yfinance
    class YFPricesMissingError(Exception):
        """Fallback local exception lorsque yfinance ne définit pas YFPricesMissingError."""
        pass
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import time

import pandas as pd

from ..database.models import MarketData, PriceHistory
from ..database.db_manager import DatabaseManager
from ..config import (
    CACHE_DURATION, MAX_CACHE_AGE,
    PARIS_EXCHANGE_SUFFIX, ERROR_MESSAGES,
    USE_ALPHA_VANTAGE
)
from ..utils.tickers import resolve_yahoo_ticker, translate_missing_aliases
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
                yf_ticker = self._resolve_yahoo_ticker(ticker)
                stock = yf.Ticker(yf_ticker)
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
                alias_info = f" (Yahoo {yf_ticker})" if 'yf_ticker' in locals() and yf_ticker != ticker else ""
                print(f"Erreur lors de la récupération de {ticker}{alias_info}: {e}")
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
                alias_map = self._build_alias_map(tickers_to_fetch)

                # yfinance permet de télécharger plusieurs tickers à la fois
                try:
                    aliases = list(alias_map.keys())
                    if not aliases:
                        return results

                    download_kwargs = {
                        "tickers": " ".join(aliases),
                        "period": "2d",  # 2 jours pour avoir previous_close
                        "interval": "1d",
                        "progress": False,
                        "auto_adjust": False,
                    }

                    try:
                        data = yf.download(**download_kwargs, raise_errors=False)
                    except TypeError:
                        # Ancienne version de yfinance sans paramètre raise_errors
                        data = yf.download(**download_kwargs)

                    if data.empty:
                        raise ValueError("Aucune donnée renvoyée par yfinance")

                    is_multi_index = isinstance(data.columns, pd.MultiIndex)
                    failed_downloads: List[str] = []

                    for alias, originals in alias_map.items():
                        try:
                            close_series = None
                            volume_series = None

                            if is_multi_index:
                                if 'Close' in data and alias in data['Close'].columns:
                                    close_series = data['Close'][alias]
                                if 'Volume' in data and alias in data['Volume'].columns:
                                    volume_series = data['Volume'][alias]
                            else:
                                close_series = data['Close'] if 'Close' in data else None
                                volume_series = data['Volume'] if 'Volume' in data else None

                            if close_series is None or close_series.empty:
                                raise KeyError(alias)

                            for original in originals:
                                market_data = self._build_market_data_from_series(
                                    original,
                                    close_series,
                                    volume_series
                                )

                                if market_data:
                                    results[original] = market_data
                                    self.db.upsert_market_cache(market_data)
                                else:
                                    failed_downloads.append(original)

                        except Exception as e:
                            print(f"Erreur pour {', '.join(originals)}: {e}")
                            failed_downloads.extend(originals)

                    if failed_downloads:
                        print(
                            f"⚠️ yfinance: tickers sans données : {', '.join(sorted(set(failed_downloads)))}"
                        )

                except YFPricesMissingError as exc:
                    # yfinance remonte ce type d'erreur lorsqu'aucune donnée n'est disponible pour un ticker
                    missing = getattr(exc, "ticker", None) or getattr(exc, "tickers", None)
                    if isinstance(missing, str):
                        missing_aliases = [missing]
                    elif isinstance(missing, (list, tuple, set)):
                        missing_aliases = list(missing)
                    else:
                        missing_aliases = list(alias_map.keys())

                    missing_tickers = translate_missing_aliases(missing_aliases, alias_map)

                    print(
                        "⚠️ yfinance: aucune donnée pour "
                        + ", ".join(sorted(set(missing_tickers)))
                    )

                    # Fallback: récupérer un par un (certains tickers peuvent encore être disponibles)
                    for ticker in tickers_to_fetch:
                        data = self.get_current_price(ticker, use_cache=False)
                        if data:
                            results[ticker] = data

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
            yf_ticker = self._resolve_yahoo_ticker(ticker)
            stock = yf.Ticker(yf_ticker)
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
            alias_info = f" (Yahoo {yf_ticker})" if 'yf_ticker' in locals() and yf_ticker != ticker else ""
            print(f"Erreur récupération historique {ticker}{alias_info}: {e}")
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
            yf_ticker = self._resolve_yahoo_ticker(ticker)
            stock = yf.Ticker(yf_ticker)
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
            alias_info = f" (Yahoo {yf_ticker})" if 'yf_ticker' in locals() and yf_ticker != ticker else ""
            print(f"Erreur récupération info {ticker}{alias_info}: {e}")
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
            yf_ticker = self._resolve_yahoo_ticker(ticker)
            stock = yf.Ticker(yf_ticker)
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

    def _resolve_yahoo_ticker(self, ticker: str) -> str:
        """Retourne le ticker Yahoo Finance à utiliser pour un symbole donné."""
        return resolve_yahoo_ticker(ticker)

    def _build_alias_map(self, tickers: List[str]) -> Dict[str, List[str]]:
        """Construit une correspondance alias->tickers originaux pour yfinance."""
        alias_map: Dict[str, List[str]] = {}
        for original in tickers:
            alias = self._resolve_yahoo_ticker(original)
            alias_map.setdefault(alias, []).append(original)
        return alias_map

    def _build_market_data_from_series(self, ticker, close_series, volume_series=None) -> Optional[MarketData]:
        """Construit un objet MarketData à partir des séries pandas retournées par yfinance."""

        if close_series is None or close_series.empty:
            return None

        # Series peut être renvoyée sous forme DataFrame dans certains cas (ex. une seule colonne)
        if isinstance(close_series, pd.DataFrame):
            # On sélectionne la première colonne disponible
            close_series = close_series.iloc[:, 0]

        last_valid_index = close_series.last_valid_index()

        if last_valid_index is None:
            return None

        current_price = close_series.loc[last_valid_index]

        if pd.isna(current_price):
            return None

        valid_closes = close_series.loc[:last_valid_index].dropna()
        previous_close = valid_closes.iloc[-2] if len(valid_closes) >= 2 else current_price

        if pd.isna(previous_close) or previous_close <= 0:
            previous_close = current_price

        volume = 0
        if volume_series is not None and not isinstance(volume_series, (int, float)):
            if isinstance(volume_series, pd.DataFrame):
                volume_series = volume_series.iloc[:, 0]

            if last_valid_index in volume_series.index:
                volume_value = volume_series.loc[last_valid_index]
                if pd.notna(volume_value):
                    try:
                        volume = int(float(volume_value))
                    except (ValueError, TypeError):
                        volume = 0

        current_price = float(current_price)
        previous_close = float(previous_close)

        change_percent = 0
        if previous_close > 0:
            change_percent = ((current_price - previous_close) / previous_close) * 100

        return MarketData(
            ticker=ticker,
            current_price=current_price,
            previous_close=previous_close,
            change_percent=change_percent,
            volume=volume,
            market_cap=0,
            last_updated=datetime.now().isoformat()
        )

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
            yf_ticker = self._resolve_yahoo_ticker(ticker)
            stock = yf.Ticker(yf_ticker)

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
            alias_info = f" (Yahoo {yf_ticker})" if 'yf_ticker' in locals() and yf_ticker != ticker else ""
            print(f"Erreur récupération quote {ticker}{alias_info}: {e}")
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
