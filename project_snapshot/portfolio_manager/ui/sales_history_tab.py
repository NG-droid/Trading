# -*- coding: utf-8 -*-
"""
Onglet Historique des Ventes - Affiche toutes les ventes réalisées avec PNL
"""

import customtkinter as ctk
from datetime import datetime
from portfolio_manager.core.portfolio import Portfolio
from portfolio_manager.core.calculator import FinancialCalculator
from portfolio_manager.utils.formatters import format_currency, format_percentage
from portfolio_manager.ui.components.filters import PeriodFilter


class SalesHistoryTab(ctk.CTkScrollableFrame):
    """Onglet affichant l'historique des ventes avec les plus-values réalisées"""

    def __init__(self, parent, portfolio: Portfolio):
        super().__init__(parent)
        self.portfolio = portfolio
        self.calculator = FinancialCalculator

        # Configuration du grid
        self.grid_columnconfigure(0, weight=1)

        # Titre
        self.title_label = ctk.CTkLabel(
            self,
            text="📊 Historique des Ventes",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Filtres
        self.filters = PeriodFilter(
            self,
            on_filter_change=self._on_filter_change,
            show_transaction_type=False  # Pas de filtre par type pour les ventes (toujours VENTE)
        )
        self.filters.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        # Frame pour les statistiques globales
        self._create_stats_frame()

        # Frame pour la liste des ventes
        self.sales_frame = ctk.CTkFrame(self, corner_radius=10)
        self.sales_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")

        # Charger les données
        self.load_sales()

    def _create_stats_frame(self):
        """Crée le frame des statistiques globales"""
        stats_frame = ctk.CTkFrame(self, corner_radius=10)
        stats_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Statistiques globales (sera rempli lors du chargement)
        self.stats_cards_frame = stats_frame

    def _on_filter_change(self, start_date, end_date, transaction_type):
        """Appelé quand les filtres changent"""
        self.load_sales(start_date, end_date)

    def load_sales(self, start_date=None, end_date=None):
        """Charge toutes les ventes et calcule les PNL"""
        try:
            # Récupérer toutes les transactions de vente
            sell_transactions = self.portfolio.db.get_transactions_by_type('VENTE')

            # Appliquer les filtres de date
            if start_date and end_date:
                sell_transactions = [
                    tx for tx in sell_transactions
                    if start_date <= tx.transaction_date <= end_date
                ]

            if not sell_transactions:
                self._show_no_sales_message()
                return

            # Récupérer toutes les transactions (achats inclus pour calcul FIFO)
            all_transactions = self.portfolio.get_all_transactions()

            # Calculer les statistiques globales
            total_pnl = 0
            total_gains = 0
            total_losses = 0
            sales_with_pnl = []

            for sell_tx in sell_transactions:
                # Récupérer les achats correspondants (avant la vente)
                sell_date = datetime.strptime(sell_tx.transaction_date, "%Y-%m-%d")
                buys = [
                    tx for tx in all_transactions
                    if tx.ticker == sell_tx.ticker
                    and tx.transaction_type == 'ACHAT'
                    and datetime.strptime(tx.transaction_date, "%Y-%m-%d") <= sell_date
                ]

                # Trier les achats par date (FIFO)
                buys.sort(key=lambda x: x.transaction_date)

                # Calculer le PNL avec FIFO
                pnl_result = self.calculator.calculate_realized_pv_fifo(buys, sell_tx)

                # Ajouter aux totaux
                total_pnl += pnl_result.total_gain_loss
                if pnl_result.total_gain_loss > 0:
                    total_gains += pnl_result.total_gain_loss
                else:
                    total_losses += abs(pnl_result.total_gain_loss)

                # Stocker pour affichage
                sales_with_pnl.append({
                    'transaction': sell_tx,
                    'pnl': pnl_result
                })

            # Afficher les statistiques globales
            self._update_stats(total_pnl, total_gains, total_losses, len(sell_transactions))

            # Afficher les ventes
            self._display_sales(sales_with_pnl)

        except Exception as e:
            print(f"Erreur lors du chargement des ventes: {e}")
            import traceback
            traceback.print_exc()

    def _show_no_sales_message(self):
        """Affiche un message si aucune vente"""
        no_sales_label = ctk.CTkLabel(
            self.sales_frame,
            text="Aucune vente enregistrée.\n\nLes ventes que vous effectuerez apparaîtront ici avec le calcul automatique des plus-values.",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        no_sales_label.pack(pady=50)

    def _update_stats(self, total_pnl, total_gains, total_losses, num_sales):
        """Met à jour les cartes de statistiques"""
        # Nettoyer les widgets existants
        for widget in self.stats_cards_frame.winfo_children():
            widget.destroy()

        # Carte 1: PNL Total
        pnl_color = "#10b981" if total_pnl >= 0 else "#ef4444"
        self._create_stat_card(
            self.stats_cards_frame,
            "💰 PNL Total Réalisé",
            format_currency(total_pnl),
            value_color=pnl_color,
            column=0
        )

        # Carte 2: Total Gains
        self._create_stat_card(
            self.stats_cards_frame,
            "📈 Total Gains",
            format_currency(total_gains),
            value_color="#10b981",
            column=1
        )

        # Carte 3: Total Pertes
        self._create_stat_card(
            self.stats_cards_frame,
            "📉 Total Pertes",
            format_currency(total_losses),
            value_color="#ef4444",
            column=2
        )

        # Carte 4: Nombre de ventes
        self._create_stat_card(
            self.stats_cards_frame,
            "🔢 Nombre de Ventes",
            str(num_sales),
            column=3
        )

    def _create_stat_card(self, parent, title, value, value_color=None, column=0):
        """Crée une carte de statistique"""
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.grid(row=0, column=column, padx=10, pady=10, sticky="nsew")

        # Titre
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        title_label.pack(padx=20, pady=(20, 5))

        # Valeur
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=value_color
        )
        value_label.pack(padx=20, pady=(5, 20))

    def _display_sales(self, sales_with_pnl):
        """Affiche la liste des ventes"""
        # Nettoyer le frame
        for widget in self.sales_frame.winfo_children():
            widget.destroy()

        # Titre du tableau
        title = ctk.CTkLabel(
            self.sales_frame,
            text="Détail des Ventes",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(padx=20, pady=(20, 10), anchor="w")

        # Frame pour le tableau
        table_frame = ctk.CTkFrame(self.sales_frame, fg_color="transparent")
        table_frame.pack(padx=20, pady=(0, 20), fill="both", expand=True)

        # En-têtes
        headers = [
            ("Date", 100),
            ("Ticker", 100),
            ("Société", 200),
            ("Quantité", 80),
            ("Prix Vente", 100),
            ("Prix Achat Moy.", 120),
            ("Montant Vente", 120),
            ("PNL Réalisé", 120),
            ("PNL %", 100)
        ]

        headers_frame = ctk.CTkFrame(table_frame)
        headers_frame.pack(fill="x", padx=5, pady=(5, 10))

        for i, (header, width) in enumerate(headers):
            label = ctk.CTkLabel(
                headers_frame,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=width
            )
            label.grid(row=0, column=i, padx=5, pady=5)

        # Trier les ventes par date décroissante (plus récentes en premier)
        sales_with_pnl.sort(
            key=lambda x: x['transaction'].transaction_date,
            reverse=True
        )

        # Lignes de ventes
        for sale_data in sales_with_pnl:
            self._create_sale_row(table_frame, sale_data)

    def _create_sale_row(self, parent, sale_data):
        """Crée une ligne de vente"""
        tx = sale_data['transaction']
        pnl = sale_data['pnl']

        row_frame = ctk.CTkFrame(parent)
        row_frame.pack(fill="x", padx=5, pady=2)

        # Couleur selon gain/perte
        if pnl.total_gain_loss >= 0:
            fg_color = ("gray85", "gray25")
        else:
            fg_color = ("gray90", "gray20")

        row_frame.configure(fg_color=fg_color)

        # Date
        date_str = datetime.strptime(tx.transaction_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        ctk.CTkLabel(row_frame, text=date_str, width=100).grid(row=0, column=0, padx=5, pady=8)

        # Ticker
        ctk.CTkLabel(
            row_frame,
            text=tx.ticker,
            width=100,
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=1, padx=5, pady=8)

        # Société (tronquée)
        company = tx.company_name[:20] + "..." if len(tx.company_name) > 20 else tx.company_name
        ctk.CTkLabel(row_frame, text=company, width=200, anchor="w").grid(row=0, column=2, padx=5, pady=8)

        # Quantité
        ctk.CTkLabel(row_frame, text=f"{tx.quantity:.2f}", width=80).grid(row=0, column=3, padx=5, pady=8)

        # Prix de vente
        ctk.CTkLabel(
            row_frame,
            text=format_currency(tx.price_per_share),
            width=100
        ).grid(row=0, column=4, padx=5, pady=8)

        # Prix d'achat moyen (calculé)
        avg_buy_price = pnl.average_buy_price
        ctk.CTkLabel(
            row_frame,
            text=format_currency(avg_buy_price),
            width=120
        ).grid(row=0, column=5, padx=5, pady=8)

        # Montant total de la vente
        sale_amount = tx.quantity * tx.price_per_share - tx.fees
        ctk.CTkLabel(
            row_frame,
            text=format_currency(sale_amount),
            width=120,
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=6, padx=5, pady=8)

        # PNL Réalisé
        pnl_color = "#10b981" if pnl.total_gain_loss >= 0 else "#ef4444"
        ctk.CTkLabel(
            row_frame,
            text=format_currency(pnl.total_gain_loss),
            width=120,
            text_color=pnl_color,
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=7, padx=5, pady=8)

        # PNL %
        total_buy_cost = pnl.average_buy_price * pnl.quantity_sold
        pnl_percent = (pnl.total_gain_loss / total_buy_cost * 100) if total_buy_cost > 0 else 0
        ctk.CTkLabel(
            row_frame,
            text=format_percentage(pnl_percent),
            width=100,
            text_color=pnl_color,
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=8, padx=5, pady=8)
