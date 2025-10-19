# -*- coding: utf-8 -*-
"""
Calculateur fiscal pour la France
Gère le PFU (Flat Tax) et le barème progressif
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass

from ..config import (
    FLAT_TAX_RATE, INCOME_TAX_RATE, SOCIAL_TAX_RATE,
    CSG_DEDUCTIBLE_RATE, DIVIDEND_ALLOWANCE_RATE
)


@dataclass
class TaxResult:
    """Résultat d'un calcul fiscal"""
    gross_amount: float
    tax_amount: float
    net_amount: float
    breakdown: Dict[str, float]


class TaxCalculator:
    """
    Calculateur fiscal pour dividendes et plus-values
    Conforme à la fiscalité française
    """

    @staticmethod
    def calculate_pfu_dividend(gross_dividend: float) -> TaxResult:
        """
        Calcule l'impôt sur les dividendes avec le PFU (Flat Tax)

        PFU = 30% total:
        - Impôt sur le revenu: 12,8%
        - Prélèvements sociaux: 17,2%

        Args:
            gross_dividend: Montant brut du dividende

        Returns:
            TaxResult avec le détail
        """
        income_tax = gross_dividend * INCOME_TAX_RATE
        social_tax = gross_dividend * SOCIAL_TAX_RATE
        total_tax = income_tax + social_tax
        net_amount = gross_dividend - total_tax

        # CSG déductible (6,8% des prélèvements sociaux)
        csg_deductible = gross_dividend * CSG_DEDUCTIBLE_RATE

        return TaxResult(
            gross_amount=gross_dividend,
            tax_amount=total_tax,
            net_amount=net_amount,
            breakdown={
                'impot_revenu': income_tax,
                'prelevements_sociaux': social_tax,
                'csg_deductible': csg_deductible,
                'taux_effectif': FLAT_TAX_RATE
            }
        )

    @staticmethod
    def calculate_pfu_capital_gain(capital_gain: float) -> TaxResult:
        """
        Calcule l'impôt sur les plus-values avec le PFU

        Args:
            capital_gain: Montant de la plus-value

        Returns:
            TaxResult avec le détail
        """
        # Même calcul que pour les dividendes
        return TaxCalculator.calculate_pfu_dividend(capital_gain)

    @staticmethod
    def calculate_progressive_tax_dividend(
        gross_dividend: float,
        marginal_tax_rate: float
    ) -> TaxResult:
        """
        Calcule l'impôt sur les dividendes avec le barème progressif

        Avec abattement de 40% sur les dividendes

        Args:
            gross_dividend: Montant brut du dividende
            marginal_tax_rate: Taux marginal d'imposition (TMI) en %

        Returns:
            TaxResult avec le détail
        """
        # Abattement de 40%
        taxable_amount = gross_dividend * (1 - DIVIDEND_ALLOWANCE_RATE)

        # Impôt sur le revenu (au barème)
        income_tax = taxable_amount * (marginal_tax_rate / 100)

        # Prélèvements sociaux (toujours 17,2%, pas d'abattement)
        social_tax = gross_dividend * SOCIAL_TAX_RATE

        total_tax = income_tax + social_tax
        net_amount = gross_dividend - total_tax

        # CSG déductible
        csg_deductible = gross_dividend * CSG_DEDUCTIBLE_RATE

        return TaxResult(
            gross_amount=gross_dividend,
            tax_amount=total_tax,
            net_amount=net_amount,
            breakdown={
                'abattement_40pct': gross_dividend * DIVIDEND_ALLOWANCE_RATE,
                'base_imposable': taxable_amount,
                'impot_revenu': income_tax,
                'prelevements_sociaux': social_tax,
                'csg_deductible': csg_deductible,
                'taux_marginal': marginal_tax_rate,
                'taux_effectif': (total_tax / gross_dividend) * 100
            }
        )

    @staticmethod
    def compare_pfu_vs_progressive(
        gross_dividend: float,
        marginal_tax_rate: float
    ) -> Dict:
        """
        Compare le PFU et le barème progressif

        Args:
            gross_dividend: Montant brut
            marginal_tax_rate: TMI en %

        Returns:
            Dictionnaire avec la comparaison
        """
        pfu_result = TaxCalculator.calculate_pfu_dividend(gross_dividend)
        progressive_result = TaxCalculator.calculate_progressive_tax_dividend(
            gross_dividend,
            marginal_tax_rate
        )

        diff = pfu_result.tax_amount - progressive_result.tax_amount
        better_option = "PFU" if diff > 0 else "Barème progressif"

        return {
            'pfu': {
                'net': pfu_result.net_amount,
                'tax': pfu_result.tax_amount,
                'rate': 30.0
            },
            'progressive': {
                'net': progressive_result.net_amount,
                'tax': progressive_result.tax_amount,
                'rate': progressive_result.breakdown['taux_effectif']
            },
            'difference': abs(diff),
            'best_option': better_option,
            'savings': abs(diff) if diff != 0 else 0
        }

    @staticmethod
    def calculate_annual_tax_summary(
        total_dividends: float,
        total_capital_gains: float,
        total_capital_losses: float = 0,
        marginal_tax_rate: float = None
    ) -> Dict:
        """
        Calcule un résumé fiscal annuel

        Args:
            total_dividends: Total des dividendes bruts
            total_capital_gains: Total des plus-values
            total_capital_losses: Total des moins-values
            marginal_tax_rate: TMI (optionnel, pour comparaison)

        Returns:
            Résumé fiscal complet
        """
        # Plus-values nettes (gains - pertes)
        net_capital_gains = max(0, total_capital_gains - total_capital_losses)

        # Calcul PFU
        dividend_tax = TaxCalculator.calculate_pfu_dividend(total_dividends)
        capital_gain_tax = TaxCalculator.calculate_pfu_capital_gain(net_capital_gains)

        total_tax_pfu = dividend_tax.tax_amount + capital_gain_tax.tax_amount
        total_net_pfu = dividend_tax.net_amount + capital_gain_tax.net_amount

        summary = {
            'revenus': {
                'dividendes_bruts': total_dividends,
                'plus_values': total_capital_gains,
                'moins_values': total_capital_losses,
                'plus_values_nettes': net_capital_gains,
                'total_brut': total_dividends + net_capital_gains
            },
            'pfu': {
                'impot_dividendes': dividend_tax.tax_amount,
                'impot_pv': capital_gain_tax.tax_amount,
                'total_impot': total_tax_pfu,
                'total_net': total_net_pfu,
                'csg_deductible': dividend_tax.breakdown['csg_deductible'] +
                                 capital_gain_tax.breakdown['csg_deductible']
            }
        }

        # Comparaison avec barème si TMI fourni
        if marginal_tax_rate is not None:
            progressive_div = TaxCalculator.calculate_progressive_tax_dividend(
                total_dividends,
                marginal_tax_rate
            )
            progressive_pv = TaxCalculator.calculate_pfu_capital_gain(net_capital_gains)

            total_tax_progressive = progressive_div.tax_amount + progressive_pv.tax_amount

            summary['bareme_progressif'] = {
                'impot_dividendes': progressive_div.tax_amount,
                'impot_pv': progressive_pv.tax_amount,
                'total_impot': total_tax_progressive,
                'total_net': (total_dividends + net_capital_gains) - total_tax_progressive,
                'tmi': marginal_tax_rate
            }

            summary['comparaison'] = {
                'difference': total_tax_pfu - total_tax_progressive,
                'meilleure_option': 'PFU' if total_tax_pfu < total_tax_progressive else 'Barème',
                'economie': abs(total_tax_pfu - total_tax_progressive)
            }

        return summary

    @staticmethod
    def calculate_tax_bracket(annual_income: float, family_quotient: float = 1) -> Tuple[float, str]:
        """
        Calcule le taux marginal d'imposition (TMI) selon le barème 2024

        Args:
            annual_income: Revenu annuel imposable
            family_quotient: Nombre de parts fiscales

        Returns:
            Tuple (taux marginal %, nom de la tranche)
        """
        # Barème 2024 (par part)
        income_per_part = annual_income / family_quotient

        brackets = [
            (0, 11294, 0, "0%"),
            (11295, 28797, 11, "11%"),
            (28798, 82341, 30, "30%"),
            (82342, 177106, 41, "41%"),
            (177107, float('inf'), 45, "45%")
        ]

        for min_income, max_income, rate, name in brackets:
            if min_income <= income_per_part <= max_income:
                return rate, name

        return 45, "45%"

    @staticmethod
    def estimate_total_tax(
        annual_income: float,
        dividends: float,
        capital_gains: float,
        family_quotient: float = 1
    ) -> Dict:
        """
        Estime l'impôt total (revenus + dividendes + PV)

        Args:
            annual_income: Revenus annuels (salaires, etc.)
            dividends: Dividendes bruts
            capital_gains: Plus-values
            family_quotient: Nombre de parts

        Returns:
            Estimation complète
        """
        # Déterminer le TMI
        tmi, bracket_name = TaxCalculator.calculate_tax_bracket(annual_income, family_quotient)

        # Calcul fiscal sur dividendes et PV
        summary = TaxCalculator.calculate_annual_tax_summary(
            dividends,
            capital_gains,
            0,
            tmi
        )

        return {
            'revenus_annuels': annual_income,
            'tmi': tmi,
            'tranche': bracket_name,
            'parts': family_quotient,
            'fiscal_summary': summary
        }

    @staticmethod
    def calculate_ifu_data(
        dividends_fr: float,
        dividends_foreign: float,
        capital_gains: float,
        capital_losses: float
    ) -> Dict:
        """
        Prépare les données pour l'IFU (Imprimé Fiscal Unique)

        Args:
            dividends_fr: Dividendes source française
            dividends_foreign: Dividendes source étrangère
            capital_gains: Plus-values
            capital_losses: Moins-values

        Returns:
            Données formatées pour déclaration
        """
        # Calcul PFU sur dividendes français
        div_fr_tax = TaxCalculator.calculate_pfu_dividend(dividends_fr)

        # Calcul PFU sur dividendes étrangers
        div_foreign_tax = TaxCalculator.calculate_pfu_dividend(dividends_foreign)

        # Plus-values nettes
        net_gains = max(0, capital_gains - capital_losses)
        pv_tax = TaxCalculator.calculate_pfu_capital_gain(net_gains)

        return {
            'case_2DC': dividends_fr,  # Dividendes français bruts
            'case_2AB': dividends_foreign,  # Dividendes étrangers
            'case_2CG': capital_gains,  # Plus-values mobilières
            'case_2BH': net_gains,  # Plus-values nettes après imputation
            'prelevement_forfaitaire': {
                'dividendes_fr': div_fr_tax.tax_amount,
                'dividendes_etranger': div_foreign_tax.tax_amount,
                'plus_values': pv_tax.tax_amount,
                'total': div_fr_tax.tax_amount + div_foreign_tax.tax_amount + pv_tax.tax_amount
            },
            'csg_deductible': {
                'montant': div_fr_tax.breakdown['csg_deductible'] +
                          div_foreign_tax.breakdown['csg_deductible'] +
                          pv_tax.breakdown['csg_deductible'],
                'case_6DE': div_fr_tax.breakdown['csg_deductible']  # CSG déductible
            }
        }
