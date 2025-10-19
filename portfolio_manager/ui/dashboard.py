# -*- coding: utf-8 -*-
"""
Dashboard - Vue d'ensemble du portefeuille
"""

import customtkinter as ctk
from portfolio_manager.core.portfolio import Portfolio
from portfolio_manager.utils.formatters import format_currency, format_percentage


class DashboardTab(ctk.CTkScrollableFrame):
    """Onglet Dashboard avec métriques principales"""

    def __init__(self, parent, portfolio: Portfolio):
        super().__init__(parent)
        self.portfolio = portfolio

        # Configuration du grid pour layout responsive
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)  # Métriques
        self.grid_rowconfigure(2, weight=1)  # Positions (s'étend)

        # Charger les données
        self.load_data()

    def load_data(self):
        """Charge et affiche les données du dashboard"""
        try:
            # Récupérer le snapshot (avec gestion d'erreur pour l'API)
            try:
                snapshot = self.portfolio.get_portfolio_snapshot()
                performance = self.portfolio.get_performance_metrics()
            except Exception as api_error:
                print(f"Erreur API lors du chargement du snapshot: {api_error}")
                import traceback
                traceback.print_exc()

                # Afficher un message d'erreur à l'utilisateur
                error_label = ctk.CTkLabel(
                    self,
                    text="⚠️ Impossible de charger les données de marché.\nVérifiez votre connexion internet ou essayez de rafraîchir plus tard.\n\nUtilisez l'onglet Portfolio pour voir vos positions sans prix actuels.",
                    font=ctk.CTkFont(size=14),
                    text_color="orange",
                    justify="center"
                )
                error_label.grid(row=1, column=0, padx=20, pady=50)
                return

            # Titre
            title = ctk.CTkLabel(
                self,
                text="📊 Dashboard",
                font=ctk.CTkFont(size=28, weight="bold")
            )
            title.grid(row=0, column=0, padx=20, pady=(20, 30), sticky="w")

            # Section Métriques Principales
            self.create_metrics_section(snapshot, performance)

            # Section Top Positions
            self.create_positions_section(snapshot)

        except Exception as e:
            error_label = ctk.CTkLabel(
                self,
                text=f"❌ Erreur de chargement: {str(e)}",
                text_color="red"
            )
            error_label.grid(row=0, column=0, padx=20, pady=20)

    def create_metrics_section(self, snapshot, performance):
        """Crée la section des métriques principales"""
        metrics_frame = ctk.CTkFrame(self)
        metrics_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        metrics_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Métrique 1: Valeur totale
        self.create_metric_card(
            metrics_frame, 0,
            "💰 Valeur Totale",
            format_currency(snapshot.current_value),
            format_percentage(snapshot.total_gain_loss_percent)
        )

        # Métrique 2: Gains totaux
        self.create_metric_card(
            metrics_frame, 1,
            "📈 Gains Totaux",
            format_currency(snapshot.total_gain_loss),
            f"{snapshot.positions_count} positions"
        )

        # Métrique 3: Dividendes
        self.create_metric_card(
            metrics_frame, 2,
            "💵 Dividendes",
            format_currency(snapshot.dividend_income),
            f"{format_percentage(performance.dividend_yield)} yield"
        )

        # Métrique 4: Performance
        self.create_metric_card(
            metrics_frame, 3,
            "🎯 Performance",
            format_percentage(performance.total_return_percent),
            f"Frais: {format_currency(performance.total_fees_paid)}"
        )

    def create_metric_card(self, parent, col, title, value, subtitle):
        """Crée une carte de métrique"""
        card = ctk.CTkFrame(parent)
        card.grid(row=0, column=col, padx=10, pady=10, sticky="nsew")

        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=12)
        )
        title_label.pack(pady=(15, 5))

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=20, weight="bold")
        )
        value_label.pack(pady=5)

        subtitle_label = ctk.CTkLabel(
            card,
            text=subtitle,
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        subtitle_label.pack(pady=(5, 15))

    def create_positions_section(self, snapshot):
        """Crée la section des positions principales"""
        positions_frame = ctk.CTkFrame(self)
        positions_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # Titre
        title = ctk.CTkLabel(
            positions_frame,
            text="💼 Top Positions",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(anchor="w", padx=15, pady=(15, 10))

        # En-têtes
        header_frame = ctk.CTkFrame(positions_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=5)

        headers = ["Ticker", "Société", "Valeur", "P&L", "Poids"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                header_frame,
                text=header,
                font=ctk.CTkFont(weight="bold"),
                width=150
            )
            label.grid(row=0, column=i, padx=5)

        # Lignes de positions (top 5)
        for i, pos in enumerate(snapshot.positions[:5]):
            row_frame = ctk.CTkFrame(positions_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=15, pady=2)

            # Ticker
            ctk.CTkLabel(row_frame, text=pos['ticker'], width=150).grid(row=0, column=0, padx=5)

            # Société (tronquée)
            company = pos['company_name'][:20] + "..." if len(pos['company_name']) > 20 else pos['company_name']
            ctk.CTkLabel(row_frame, text=company, width=150).grid(row=0, column=1, padx=5)

            # Valeur
            ctk.CTkLabel(row_frame, text=format_currency(pos['current_value']), width=150).grid(row=0, column=2, padx=5)

            # P&L
            pnl_text = format_percentage(pos['gain_loss_percent'])
            pnl_color = "green" if pos['gain_loss_percent'] >= 0 else "red"
            ctk.CTkLabel(row_frame, text=pnl_text, width=150, text_color=pnl_color).grid(row=0, column=3, padx=5)

            # Poids
            ctk.CTkLabel(row_frame, text=f"{pos['weight']:.1f}%", width=150).grid(row=0, column=4, padx=5)

        # Bouton "Voir tout"
        btn_view_all = ctk.CTkButton(
            positions_frame,
            text="Voir toutes les positions →",
            width=200
        )
        btn_view_all.pack(pady=15)
