"""Fallback static dividend data for CAC40 tickers when market APIs are unavailable."""

from __future__ import annotations

DIVIDEND_FALLBACKS = {
    "TTE.PA": {
        "company_name": "TotalEnergies",
        "amount_schedule": [0.74, 0.74, 0.74, 0.74],
        "months": [3, 6, 9, 12],
        "ex_day": 5,
        "payment_delay_days": 20,
    },
    "AI.PA": {
        "company_name": "Air Liquide",
        "amount_schedule": [3.10],
        "months": [5],
        "ex_day": 15,
        "payment_delay_days": 15,
    },
    "SAN.PA": {
        "company_name": "Sanofi",
        "amount_schedule": [3.76],
        "months": [5],
        "ex_day": 10,
        "payment_delay_days": 20,
    },
    "BN.PA": {
        "company_name": "Danone",
        "amount_schedule": [2.00],
        "months": [5],
        "ex_day": 8,
        "payment_delay_days": 15,
    },
    "MC.PA": {
        "company_name": "LVMH",
        "amount_schedule": [5.50],
        "months": [4, 12],
        "ex_day": 15,
        "payment_delay_days": 20,
    },
    "OR.PA": {
        "company_name": "L'Oréal",
        "amount_schedule": [6.00],
        "months": [7],
        "ex_day": 7,
        "payment_delay_days": 15,
    },
    "EN.PA": {
        "company_name": "Bouygues",
        "amount_schedule": [1.80],
        "months": [5],
        "ex_day": 3,
        "payment_delay_days": 15,
    },
}
