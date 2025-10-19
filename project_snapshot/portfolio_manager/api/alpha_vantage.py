# -*- coding: utf-8 -*-
"""
API Alpha Vantage - Alternative à Yahoo Finance
Récupère les prix des actions via Alpha Vantage
"""

import requests
from typing import Optional, Dict
from datetime import datetime
from ..config import ALPHA_VANTAGE_API_KEY, API_TIMEOUT
from ..database.models import MarketData


class AlphaVantageAPI:
    """Client API Alpha Vantage pour récupérer les prix des actions"""

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str = None):
        """
        Initialise le client Alpha Vantage

        Args:
            api_key: Clé API Alpha Vantage (utilise la config par défaut si None)
        """
        self.api_key = api_key or ALPHA_VANTAGE_API_KEY

        if not self.api_key:
            raise ValueError("Clé API Alpha Vantage non configurée")

    def get_quote(self, ticker: str) -> Optional[MarketData]:
        """
        Récupère le prix actuel d'une action

        Args:
            ticker: Symbole de l'action (ex: "AI.PA", "AAPL")

        Returns:
            MarketData ou None si erreur
        """
        try:
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': ticker,
                'apikey': self.api_key
            }

            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=API_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            # Vérifier si on a des données
            if 'Global Quote' not in data or not data['Global Quote']:
                print(f"⚠️ Alpha Vantage: Pas de données pour {ticker}")
                return None

            quote = data['Global Quote']

            # Extraire les informations
            current_price = float(quote.get('05. price', 0))
            previous_close = float(quote.get('08. previous close', 0))
            change = float(quote.get('09. change', 0))
            change_percent = quote.get('10. change percent', '0%').replace('%', '')
            volume = int(quote.get('06. volume', 0))

            if current_price == 0:
                return None

            # Créer l'objet MarketData
            market_data = MarketData(
                ticker=ticker,
                current_price=current_price,
                previous_close=previous_close,
                change_percent=float(change_percent),
                volume=volume,
                market_cap=0,  # Alpha Vantage ne fournit pas market cap dans GLOBAL_QUOTE
                last_updated=datetime.now().isoformat()
            )

            print(f"✅ Alpha Vantage: {ticker} = {current_price}€")
            return market_data

        except requests.exceptions.RequestException as e:
            print(f"❌ Alpha Vantage erreur réseau pour {ticker}: {e}")
            return None
        except (KeyError, ValueError, TypeError) as e:
            print(f"❌ Alpha Vantage erreur parsing pour {ticker}: {e}")
            return None
        except Exception as e:
            print(f"❌ Alpha Vantage erreur inattendue pour {ticker}: {e}")
            return None

    def get_multiple_quotes(self, tickers: list) -> Dict[str, MarketData]:
        """
        Récupère les prix pour plusieurs actions

        Note: Alpha Vantage limite à 5 requêtes/minute en version gratuite
        On ajoute donc un délai entre les requêtes

        Args:
            tickers: Liste de symboles d'actions

        Returns:
            Dictionnaire {ticker: MarketData}
        """
        import time

        results = {}

        for i, ticker in enumerate(tickers):
            market_data = self.get_quote(ticker)

            if market_data:
                results[ticker] = market_data

            # Respecter la limite de 5 requêtes/minute (gratuit)
            # Attendre 12 secondes entre chaque requête (5 req/min = 1 req/12s)
            if i < len(tickers) - 1:  # Pas d'attente après la dernière requête
                print(f"⏳ Attente de 12 secondes (limite Alpha Vantage)...")
                time.sleep(12)

        return results
