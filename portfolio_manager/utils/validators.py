# -*- coding: utf-8 -*-
"""
Validation des données saisies par l'utilisateur
"""

from datetime import datetime
from typing import Tuple, List
import re

from ..config import (
    MIN_QUANTITY, MAX_QUANTITY,
    MIN_PRICE, MAX_PRICE,
    PARIS_EXCHANGE_SUFFIX,
    ERROR_MESSAGES
)


def validate_ticker(ticker: str) -> Tuple[bool, str]:
    """
    Valide un ticker

    Args:
        ticker: Symbole de l'action

    Returns:
        Tuple (is_valid, error_message)
    """
    if not ticker or not ticker.strip():
        return False, "Le ticker ne peut pas être vide"

    ticker = ticker.strip().upper()

    # Vérifier le format (lettres + .PA)
    if not ticker.endswith(PARIS_EXCHANGE_SUFFIX):
        return False, ERROR_MESSAGES["invalid_ticker"]

    # Extraire le symbole (sans .PA)
    symbol = ticker.replace(PARIS_EXCHANGE_SUFFIX, "")

    # Le symbole doit contenir uniquement des lettres
    if not re.match(r'^[A-Z]+$', symbol):
        return False, "Le symbole doit contenir uniquement des lettres"

    # Le symbole doit faire entre 1 et 6 caractères
    if len(symbol) < 1 or len(symbol) > 6:
        return False, "Le symbole doit faire entre 1 et 6 caractères"

    return True, ""


def validate_quantity(quantity: float) -> Tuple[bool, str]:
    """
    Valide une quantité d'actions

    Args:
        quantity: Quantité à valider

    Returns:
        Tuple (is_valid, error_message)
    """
    try:
        qty = float(quantity)
    except (ValueError, TypeError):
        return False, "La quantité doit être un nombre"

    if qty <= 0:
        return False, "La quantité doit être positive"

    if qty < MIN_QUANTITY:
        return False, f"La quantité minimale est {MIN_QUANTITY}"

    if qty > MAX_QUANTITY:
        return False, f"La quantité maximale est {MAX_QUANTITY}"

    return True, ""


def validate_price(price: float) -> Tuple[bool, str]:
    """
    Valide un prix par action

    Args:
        price: Prix à valider

    Returns:
        Tuple (is_valid, error_message)
    """
    try:
        p = float(price)
    except (ValueError, TypeError):
        return False, "Le prix doit être un nombre"

    if p <= 0:
        return False, "Le prix doit être positif"

    if p < MIN_PRICE:
        return False, f"Le prix minimal est {MIN_PRICE}€"

    if p > MAX_PRICE:
        return False, f"Le prix maximal est {MAX_PRICE}€"

    return True, ""


def validate_date(date_str: str, allow_future: bool = False) -> Tuple[bool, str]:
    """
    Valide une date

    Args:
        date_str: Date au format DD/MM/YYYY ou YYYY-MM-DD
        allow_future: Autoriser les dates futures

    Returns:
        Tuple (is_valid, error_message)
    """
    if not date_str or not date_str.strip():
        return False, "La date ne peut pas être vide"

    # Essayer différents formats
    formats = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"]
    date_obj = None

    for fmt in formats:
        try:
            date_obj = datetime.strptime(date_str.strip(), fmt)
            break
        except ValueError:
            continue

    if not date_obj:
        return False, ERROR_MESSAGES["invalid_date"]

    # Vérifier si la date n'est pas dans le futur (sauf si autorisé)
    if not allow_future and date_obj > datetime.now():
        return False, ERROR_MESSAGES["future_date"]

    # Vérifier que la date n'est pas trop ancienne (> 50 ans)
    min_date = datetime.now().replace(year=datetime.now().year - 50)
    if date_obj < min_date:
        return False, "La date ne peut pas être antérieure à 50 ans"

    return True, ""


def validate_transaction_type(transaction_type: str) -> Tuple[bool, str]:
    """
    Valide un type de transaction

    Args:
        transaction_type: Type de transaction

    Returns:
        Tuple (is_valid, error_message)
    """
    if not transaction_type or not transaction_type.strip():
        return False, "Le type de transaction ne peut pas être vide"

    transaction_type = transaction_type.strip().upper()

    if transaction_type not in ['ACHAT', 'VENTE']:
        return False, "Le type de transaction doit être 'ACHAT' ou 'VENTE'"

    return True, ""


def validate_company_name(name: str) -> Tuple[bool, str]:
    """
    Valide un nom d'entreprise

    Args:
        name: Nom à valider

    Returns:
        Tuple (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Le nom de l'entreprise ne peut pas être vide"

    name = name.strip()

    if len(name) < 2:
        return False, "Le nom de l'entreprise doit contenir au moins 2 caractères"

    if len(name) > 100:
        return False, "Le nom de l'entreprise ne peut pas dépasser 100 caractères"

    return True, ""


def sanitize_string(text: str, max_length: int = None) -> str:
    """
    Nettoie une chaîne de caractères

    Args:
        text: Texte à nettoyer
        max_length: Longueur maximale (optionnel)

    Returns:
        Texte nettoyé
    """
    if not text:
        return ""

    # Supprimer les espaces en début et fin
    cleaned = text.strip()

    # Supprimer les caractères de contrôle
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned)

    # Réduire les espaces multiples à un seul
    cleaned = re.sub(r'\s+', ' ', cleaned)

    # Tronquer si nécessaire
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length].strip()

    return cleaned


def normalize_ticker(ticker: str) -> str:
    """
    Normalise un ticker (majuscules, ajout .PA si nécessaire)

    Args:
        ticker: Ticker à normaliser

    Returns:
        Ticker normalisé
    """
    if not ticker:
        return ""

    ticker = ticker.strip().upper()

    # Ajouter .PA si nécessaire
    if not ticker.endswith(PARIS_EXCHANGE_SUFFIX):
        ticker = f"{ticker}{PARIS_EXCHANGE_SUFFIX}"

    return ticker


def normalize_date(date_str: str, output_format: str = "%Y-%m-%d") -> str:
    """
    Normalise une date vers un format standard

    Args:
        date_str: Date à normaliser
        output_format: Format de sortie

    Returns:
        Date normalisée ou chaîne vide si invalide
    """
    is_valid, _ = validate_date(date_str, allow_future=True)

    if not is_valid:
        return ""

    # Essayer différents formats d'entrée
    formats = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"]

    for fmt in formats:
        try:
            date_obj = datetime.strptime(date_str.strip(), fmt)
            return date_obj.strftime(output_format)
        except ValueError:
            continue

    return ""


# Fonction de validation complète d'une transaction
def validate_transaction(
    ticker: str,
    quantity: float,
    price: float,
    transaction_date: str,
    transaction_type: str,
    company_name: str = None
) -> Tuple[bool, List[str]]:
    """
    Valide tous les champs d'une transaction

    Args:
        ticker: Symbole de l'action
        quantity: Quantité
        price: Prix par action
        transaction_date: Date de la transaction
        transaction_type: Type (ACHAT/VENTE)
        company_name: Nom de l'entreprise (optionnel)

    Returns:
        Tuple (is_valid, list_of_errors)
    """
    errors = []

    # Valider le ticker
    is_valid, error = validate_ticker(ticker)
    if not is_valid:
        errors.append(f"Ticker: {error}")

    # Valider la quantité
    is_valid, error = validate_quantity(quantity)
    if not is_valid:
        errors.append(f"Quantité: {error}")

    # Valider le prix
    is_valid, error = validate_price(price)
    if not is_valid:
        errors.append(f"Prix: {error}")

    # Valider la date
    is_valid, error = validate_date(transaction_date)
    if not is_valid:
        errors.append(f"Date: {error}")

    # Valider le type
    is_valid, error = validate_transaction_type(transaction_type)
    if not is_valid:
        errors.append(f"Type: {error}")

    # Valider le nom de l'entreprise si fourni
    if company_name:
        is_valid, error = validate_company_name(company_name)
        if not is_valid:
            errors.append(f"Nom: {error}")

    return len(errors) == 0, errors
