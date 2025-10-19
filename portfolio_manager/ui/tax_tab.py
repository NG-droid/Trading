# -*- coding: utf-8 -*-
"""
Onglet Fiscalité - Calculs fiscaux et IFU
"""

import customtkinter as ctk
from datetime import datetime
from typing import Optional
from portfolio_manager.core.portfolio import Portfolio
from portfolio_manager.core.tax_calculator import TaxCalculator
from portfolio_manager.utils.formatters import format_currency, format_percentage
from portfolio_manager.ui.components.filters import PeriodFilter


class TaxTab(ctk.CTkScrollableFrame):
    """Onglet fiscalité avec calculs PFU, IFU et comparaisons"""

    def __init__(self, parent, portfolio: Portfolio):
        super().__init__(parent)
        self.portfolio = portfolio
        self.calculator = TaxCalculator

        # Configuration du grid
        self.grid_columnconfigure(0, weight=1)

        # Titre
        self.title_label = ctk.CTkLabel(
            self,
            text="📊 Fiscalité",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Sélecteur d'année
        self._create_year_selector()

        # Frame pour les paramètres fiscaux
        self._create_parameters_frame()

        # Frame pour le résumé annuel
        self.summary_frame = ctk.CTkFrame(self, corner_radius=10)
        self.summary_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # Frame pour la comparaison PFU vs Barème
        self.comparison_frame = ctk.CTkFrame(self, corner_radius=10)
        self.comparison_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        # Frame pour l'IFU
        self.ifu_frame = ctk.CTkFrame(self, corner_radius=10)
        self.ifu_frame.grid(row=5, column=0, padx=20, pady=10, sticky="ew")

        # Charger les données
        self.load_tax_data()

    def _create_year_selector(self):
        """Crée le sélecteur d'année"""
        year_frame = ctk.CTkFrame(self, fg_color="transparent")
        year_frame.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        ctk.CTkLabel(
            year_frame,
            text="Année fiscale:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=(0, 10))

        # Générer les années disponibles
        current_year = datetime.now().year
        years = [str(year) for year in range(current_year, current_year - 5, -1)]

        self.year_var = ctk.StringVar(value=str(current_year))
        self.year_menu = ctk.CTkOptionMenu(
            year_frame,
            values=years,
            variable=self.year_var,
            command=self._on_year_change,
            width=120
        )
        self.year_menu.grid(row=0, column=1)

        # Bouton rafraîchir
        ctk.CTkButton(
            year_frame,
            text="🔄 Rafraîchir",
            command=self.load_tax_data,
            width=120
        ).grid(row=0, column=2, padx=10)

    def _create_parameters_frame(self):
        """Crée le frame des paramètres fiscaux"""
        param_frame = ctk.CTkFrame(self, corner_radius=10)
        param_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        param_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Titre
        title = ctk.CTkLabel(
            param_frame,
            text="Paramètres fiscaux",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.grid(row=0, column=0, columnspan=4, padx=20, pady=(20, 10), sticky="w")

        # TMI (Taux Marginal d'Imposition)
        ctk.CTkLabel(
            param_frame,
            text="TMI (Taux Marginal):",
            font=ctk.CTkFont(size=12)
        ).grid(row=1, column=0, padx=20, pady=10, sticky="w")

        self.tmi_var = ctk.StringVar(value="30")
        tmi_values = ["0", "11", "30", "41", "45"]
        self.tmi_menu = ctk.CTkOptionMenu(
            param_frame,
            values=tmi_values,
            variable=self.tmi_var,
            command=self._on_parameter_change,
            width=100
        )
        self.tmi_menu.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # Nombre de parts fiscales
        ctk.CTkLabel(
            param_frame,
            text="Nombre de parts:",
            font=ctk.CTkFont(size=12)
        ).grid(row=1, column=2, padx=20, pady=10, sticky="w")

        self.parts_var = ctk.StringVar(value="1")
        self.parts_entry = ctk.CTkEntry(
            param_frame,
            textvariable=self.parts_var,
            width=80
        )
        self.parts_entry.grid(row=1, column=3, padx=10, pady=10, sticky="w")

    def _on_year_change(self, selected_year):
        """Appelé quand l'année change"""
        self.load_tax_data()

    def _on_parameter_change(self, *args):
        """Appelé quand les paramètres changent"""
        self.load_tax_data()

    def load_tax_data(self):
        """Charge les données fiscales"""
        try:
            # Récupérer l'année sélectionnée
            year = int(self.year_var.get())
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"

            # Récupérer les dividendes de l'année
            dividends = self.portfolio.dividends_api.get_received_dividends()
            dividends_filtered = [
                div for div in dividends
                if div.received_date and start_date <= div.received_date <= end_date
            ]
            total_dividends_gross = sum(div.gross_amount for div in dividends_filtered)
            total_dividends_net = sum(div.net_amount for div in dividends_filtered)

            # Récupérer les ventes de l'année (plus-values)
            sell_transactions = self.portfolio.db.get_transactions_by_type('VENTE')
            sell_filtered = [
                tx for tx in sell_transactions
                if start_date <= tx.transaction_date <= end_date
            ]

            # Calculer les plus-values réalisées
            total_pv = 0
            total_mv = 0
            all_transactions = self.portfolio.get_all_transactions()

            for sell_tx in sell_filtered:
                sell_date = datetime.strptime(sell_tx.transaction_date, "%Y-%m-%d")
                buys = [
                    tx for tx in all_transactions
                    if tx.ticker == sell_tx.ticker
                    and tx.transaction_type == 'ACHAT'
                    and datetime.strptime(tx.transaction_date, "%Y-%m-%d") <= sell_date
                ]
                buys.sort(key=lambda x: x.transaction_date)

                from portfolio_manager.core.calculator import FinancialCalculator
                pnl_result = FinancialCalculator.calculate_realized_pv_fifo(buys, sell_tx)

                if pnl_result.total_gain_loss > 0:
                    total_pv += pnl_result.total_gain_loss
                else:
                    total_mv += abs(pnl_result.total_gain_loss)

            # Calculer le résumé fiscal
            tmi = float(self.tmi_var.get())
            summary = self.calculator.calculate_annual_tax_summary(
                total_dividends_gross,
                total_pv,
                total_mv,
                tmi
            )

            # Calculer les données IFU
            ifu_data = self.calculator.calculate_ifu_data(
                total_dividends_gross,  # Dividendes français (simplification)
                0,  # Dividendes étrangers
                total_pv,
                total_mv
            )

            # Afficher les résultats
            self._display_summary(summary, year)
            self._display_comparison(summary)
            self._display_ifu(ifu_data, year)

        except Exception as e:
            print(f"Erreur lors du chargement des données fiscales: {e}")
            import traceback
            traceback.print_exc()

    def _display_summary(self, summary, year):
        """Affiche le résumé fiscal"""
        # Nettoyer le frame
        for widget in self.summary_frame.winfo_children():
            widget.destroy()

        # Titre
        title = ctk.CTkLabel(
            self.summary_frame,
            text=f"Résumé Fiscal {year} - PFU (Flat Tax 30%)",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(padx=20, pady=(20, 10), anchor="w")

        # Grille pour les cartes
        cards_frame = ctk.CTkFrame(self.summary_frame, fg_color="transparent")
        cards_frame.pack(padx=20, pady=10, fill="x")
        cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Cartes de statistiques
        revenus = summary['revenus']
        pfu = summary['pfu']

        # Carte 1: Dividendes bruts
        self._create_info_card(
            cards_frame,
            "💵 Dividendes Bruts",
            format_currency(revenus['dividendes_bruts']),
            column=0
        )

        # Carte 2: Plus-values nettes
        self._create_info_card(
            cards_frame,
            "📈 Plus-values Nettes",
            format_currency(revenus['plus_values_nettes']),
            column=1,
            value_color="#10b981" if revenus['plus_values_nettes'] >= 0 else "#ef4444"
        )

        # Carte 3: Total brut
        self._create_info_card(
            cards_frame,
            "💰 Total Brut",
            format_currency(revenus['total_brut']),
            column=2
        )

        # Carte 4: Impôt PFU
        self._create_info_card(
            cards_frame,
            "🏛️ Impôt PFU (30%)",
            format_currency(pfu['total_impot']),
            column=3,
            value_color="#ef4444"
        )

        # Détails
        details_frame = ctk.CTkFrame(self.summary_frame)
        details_frame.pack(padx=20, pady=(10, 20), fill="x")

        details_text = f"""
Détail des revenus:
  • Dividendes bruts: {format_currency(revenus['dividendes_bruts'])}
  • Plus-values: {format_currency(revenus['plus_values'])}
  • Moins-values: {format_currency(revenus['moins_values'])}
  • Plus-values nettes: {format_currency(revenus['plus_values_nettes'])}

Détail de l'impôt PFU:
  • Impôt sur dividendes (30%): {format_currency(pfu['impot_dividendes'])}
  • Impôt sur PV (30%): {format_currency(pfu['impot_pv'])}
  • Total impôt: {format_currency(pfu['total_impot'])}
  • CSG déductible: {format_currency(pfu['csg_deductible'])}

Net après impôt: {format_currency(pfu['total_net'])}
        """

        details_label = ctk.CTkLabel(
            details_frame,
            text=details_text,
            font=ctk.CTkFont(size=12, family="Courier"),
            justify="left",
            anchor="w"
        )
        details_label.pack(padx=20, pady=20, anchor="w")

    def _display_comparison(self, summary):
        """Affiche la comparaison PFU vs Barème"""
        # Nettoyer le frame
        for widget in self.comparison_frame.winfo_children():
            widget.destroy()

        if 'comparaison' not in summary:
            # Pas de comparaison disponible
            ctk.CTkLabel(
                self.comparison_frame,
                text="Configurez votre TMI pour comparer PFU et Barème progressif",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            ).pack(pady=30)
            return

        # Titre
        title = ctk.CTkLabel(
            self.comparison_frame,
            text="Comparaison PFU vs Barème Progressif",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(padx=20, pady=(20, 10), anchor="w")

        comp = summary['comparaison']
        pfu = summary['pfu']
        bareme = summary['bareme_progressif']

        # Tableau comparatif
        table_frame = ctk.CTkFrame(self.comparison_frame, fg_color="transparent")
        table_frame.pack(padx=20, pady=10, fill="x")

        # En-têtes
        headers = ["", "PFU (30%)", f"Barème (TMI {bareme['tmi']}%)"]
        for col, header in enumerate(headers):
            label = ctk.CTkLabel(
                table_frame,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=150
            )
            label.grid(row=0, column=col, padx=10, pady=5)

        # Lignes de comparaison
        rows = [
            ("Impôt dividendes", format_currency(pfu['impot_dividendes']), format_currency(bareme['impot_dividendes'])),
            ("Impôt PV", format_currency(pfu['impot_pv']), format_currency(bareme['impot_pv'])),
            ("Total impôt", format_currency(pfu['total_impot']), format_currency(bareme['total_impot'])),
            ("Net après impôt", format_currency(pfu['total_net']), format_currency(bareme['total_net']))
        ]

        for i, (label_text, pfu_value, bareme_value) in enumerate(rows, start=1):
            ctk.CTkLabel(table_frame, text=label_text, width=150, anchor="w").grid(row=i, column=0, padx=10, pady=3)
            ctk.CTkLabel(table_frame, text=pfu_value, width=150).grid(row=i, column=1, padx=10, pady=3)
            ctk.CTkLabel(table_frame, text=bareme_value, width=150).grid(row=i, column=2, padx=10, pady=3)

        # Résultat
        best_option = comp['meilleure_option']
        economie = comp['economie']

        result_color = "#10b981" if best_option == "PFU" else "#3b82f6"
        result_text = f"\n✅ Meilleure option: {best_option}\n💰 Économie: {format_currency(economie)}"

        result_label = ctk.CTkLabel(
            self.comparison_frame,
            text=result_text,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=result_color
        )
        result_label.pack(padx=20, pady=20)

    def _display_ifu(self, ifu_data, year):
        """Affiche les données IFU"""
        # Nettoyer le frame
        for widget in self.ifu_frame.winfo_children():
            widget.destroy()

        # Titre
        title = ctk.CTkLabel(
            self.ifu_frame,
            text=f"IFU (Imprimé Fiscal Unique) {year}",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(padx=20, pady=(20, 10), anchor="w")

        # Tableau IFU
        ifu_text = f"""
Cases à remplir sur la déclaration d'impôts:

REVENUS DE CAPITAUX MOBILIERS:
  • Case 2DC - Dividendes français: {format_currency(ifu_data['case_2DC'])}
  • Case 2AB - Dividendes étrangers: {format_currency(ifu_data['case_2AB'])}

PLUS-VALUES:
  • Case 2CG - Plus-values mobilières: {format_currency(ifu_data['case_2CG'])}
  • Case 2BH - Plus-values nettes: {format_currency(ifu_data['case_2BH'])}

PRÉLÈVEMENT FORFAITAIRE UNIQUE (PFU):
  • Dividendes français: {format_currency(ifu_data['prelevement_forfaitaire']['dividendes_fr'])}
  • Dividendes étrangers: {format_currency(ifu_data['prelevement_forfaitaire']['dividendes_etranger'])}
  • Plus-values: {format_currency(ifu_data['prelevement_forfaitaire']['plus_values'])}
  • Total PFU: {format_currency(ifu_data['prelevement_forfaitaire']['total'])}

CSG DÉDUCTIBLE:
  • Case 6DE - CSG déductible: {format_currency(ifu_data['csg_deductible']['case_6DE'])}
  • Montant total: {format_currency(ifu_data['csg_deductible']['montant'])}

Note: Ces montants sont pré-remplis automatiquement par votre courtier (Trade Republic).
Vérifiez qu'ils correspondent à votre IFU officiel.
        """

        ifu_label = ctk.CTkLabel(
            self.ifu_frame,
            text=ifu_text,
            font=ctk.CTkFont(size=12, family="Courier"),
            justify="left",
            anchor="w"
        )
        ifu_label.pack(padx=20, pady=20, anchor="w")

    def _create_info_card(self, parent, title, value, column=0, value_color=None):
        """Crée une carte d'information"""
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.grid(row=0, column=column, padx=10, pady=10, sticky="nsew")

        # Titre
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        title_label.pack(padx=20, pady=(15, 5))

        # Valeur
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=value_color
        )
        value_label.pack(padx=20, pady=(0, 15))
