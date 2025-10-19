# -*- coding: utf-8 -*-
"""
Formatage des données pour l'affichage
"""

from datetime import datetime
from typing import Optional

from ..config import CURRENCY_SYMBOL, DATE_FORMAT, DECIMAL_PLACES, COLOR_GAIN, COLOR_LOSS


def format_currency(amount: float, symbol: str = CURRENCY_SYMBOL, decimals: int = DECIMAL_PLACES) -> str:
    """
    Formate un montant en devise

    Args:
        amount: Montant à formater
        symbol: Symbole de la devise
        decimals: Nombre de décimales

    Returns:
        Montant formaté (ex: "1 234,56€")
    """
    if amount is None:
        return f"0,00{symbol}"

    # Formater avec séparateur de milliers et décimales
    formatted = f"{amount:,.{decimals}f}".replace(',', ' ').replace('.', ',')
    return f"{formatted}{symbol}"


def format_percentage(value: float, decimals: int = 2, show_sign: bool = True) -> str:
    """
    Formate un pourcentage

    Args:
        value: Valeur à formater
        decimals: Nombre de décimales
        show_sign: Afficher le signe + pour les positifs

    Returns:
        Pourcentage formaté (ex: "+5,23%")
    """
    if value is None:
        return "0,00%"

    sign = ""
    if show_sign and value > 0:
        sign = "+"
    elif value < 0:
        sign = "-"
        value = abs(value)

    formatted = f"{value:.{decimals}f}".replace('.', ',')
    return f"{sign}{formatted}%"


def format_date(date_str: str, output_format: str = DATE_FORMAT) -> str:
    """
    Formate une date

    Args:
        date_str: Date au format ISO (YYYY-MM-DD)
        output_format: Format de sortie

    Returns:
        Date formatée (ex: "25/12/2024")
    """
    if not date_str:
        return ""

    try:
        # Essayer différents formats d'entrée
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"]:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime(output_format)
            except ValueError:
                continue
        return date_str
    except:
        return date_str


def format_number(value: float, decimals: int = 2) -> str:
    """
    Formate un nombre avec séparateur de milliers

    Args:
        value: Nombre à formater
        decimals: Nombre de décimales

    Returns:
        Nombre formaté (ex: "1 234,56")
    """
    if value is None:
        return "0"

    formatted = f"{value:,.{decimals}f}".replace(',', ' ').replace('.', ',')
    return formatted


def format_large_number(value: float) -> str:
    """
    Formate un grand nombre avec suffixes (K, M, B)

    Args:
        value: Nombre à formater

    Returns:
        Nombre formaté (ex: "1,5M")
    """
    if value is None:
        return "0"

    abs_value = abs(value)
    sign = "-" if value < 0 else ""

    if abs_value >= 1_000_000_000:
        return f"{sign}{abs_value/1_000_000_000:.2f}B".replace('.', ',')
    elif abs_value >= 1_000_000:
        return f"{sign}{abs_value/1_000_000:.2f}M".replace('.', ',')
    elif abs_value >= 1_000:
        return f"{sign}{abs_value/1_000:.2f}K".replace('.', ',')
    else:
        return f"{sign}{abs_value:.2f}".replace('.', ',')


def format_change(current: float, previous: float) -> str:
    """
    Formate une variation entre deux valeurs

    Args:
        current: Valeur actuelle
        previous: Valeur précédente

    Returns:
        Variation formatée (ex: "+5,23% (+12,45€)")
    """
    if previous == 0:
        return "N/A"

    change_amount = current - previous
    change_percent = (change_amount / previous) * 100

    amount_str = format_currency(abs(change_amount))
    percent_str = format_percentage(change_percent)

    return f"{percent_str} ({amount_str})"


def format_gain_loss(amount: float, use_color: bool = False) -> str:
    """
    Formate un gain ou une perte

    Args:
        amount: Montant
        use_color: Inclure le code couleur

    Returns:
        Montant formaté avec signe
    """
    sign = "+" if amount >= 0 else ""
    formatted = f"{sign}{format_currency(amount)}"

    if use_color:
        color = COLOR_GAIN if amount >= 0 else COLOR_LOSS
        return f"[{color}]{formatted}[/{color}]"

    return formatted


def format_quantity(quantity: float, decimals: int = 4) -> str:
    """
    Formate une quantité d'actions

    Args:
        quantity: Quantité
        decimals: Nombre de décimales max

    Returns:
        Quantité formatée
    """
    if quantity is None:
        return "0"

    # Supprimer les zéros inutiles
    formatted = f"{quantity:.{decimals}f}".rstrip('0').rstrip('.')
    return formatted.replace('.', ',')


def format_ticker_display(ticker: str) -> str:
    """
    Formate un ticker pour l'affichage

    Args:
        ticker: Ticker complet (ex: "AI.PA")

    Returns:
        Ticker formaté (ex: "AI")
    """
    if not ticker:
        return ""

    # Enlever le suffixe .PA
    return ticker.replace('.PA', '')


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Tronque un texte trop long

    Args:
        text: Texte à tronquer
        max_length: Longueur maximale
        suffix: Suffixe à ajouter

    Returns:
        Texte tronqué
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def format_duration(days: int) -> str:
    """
    Formate une durée en jours

    Args:
        days: Nombre de jours

    Returns:
        Durée formatée (ex: "2 ans 3 mois")
    """
    if days < 0:
        return "N/A"

    years = days // 365
    months = (days % 365) // 30
    remaining_days = days % 30

    parts = []
    if years > 0:
        parts.append(f"{years} an{'s' if years > 1 else ''}")
    if months > 0:
        parts.append(f"{months} mois")
    if remaining_days > 0 and not parts:
        parts.append(f"{remaining_days} jour{'s' if remaining_days > 1 else ''}")

    return " ".join(parts) if parts else "0 jour"


def format_status(status: str, use_emoji: bool = True) -> str:
    """
    Formate un statut

    Args:
        status: Statut ('PRÉVU', 'REÇU', etc.)
        use_emoji: Utiliser des emojis

    Returns:
        Statut formaté
    """
    if use_emoji:
        emojis = {
            'PRÉVU': '⏳ Prévu',
            'REÇU': '✅ Reçu',
            'ACHAT': '📈 Achat',
            'VENTE': '📉 Vente'
        }
        return emojis.get(status, status)

    return status


def format_rank(rank: int, total: int) -> str:
    """
    Formate un rang

    Args:
        rank: Position
        total: Total

    Returns:
        Rang formaté (ex: "3/10")
    """
    return f"{rank}/{total}"
