# -*- coding: utf-8 -*-
"""
Onglet Dashboard - Vue d'ensemble avec statistiques et graphiques
"""

import customtkinter as ctk
import threading
from portfolio_manager.core.portfolio import Portfolio
from portfolio_manager.utils.formatters import format_currency, format_percentage


class DashboardTab(ctk.CTkScrollableFrame):
    """Dashboard avec vue d'ensemble du portefeuille"""

    def __init__(self, parent, portfolio: Portfolio):
        super().__init__(parent)
        self.portfolio = portfolio

        # Configuration du grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Titre
        self.title_label = ctk.CTkLabel(
            self,
            text="📈 Dashboard",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="w")

        # Charger les données de manière asynchrone
        self.load_data()

    def load_data(self):
        """Charge toutes les données (stats + positions) de manière asynchrone"""
        self._show_loading_message()

        def do_load():
            try:
                snapshot = self.portfolio.get_portfolio_snapshot()
                performance = self.portfolio.get_performance_metrics()
                self.after(0, lambda: self._create_dashboard(snapshot, performance))
            except Exception as e:
                print(f"Erreur load_data dashboard: {e}")
                import traceback
                traceback.print_exc()
                self.after(0, lambda: self._show_error(str(e)))

        thread = threading.Thread(target=do_load, daemon=True)
        thread.start()

    def _show_loading_message(self):
        """Affiche un message de chargement"""
        loading_label = ctk.CTkLabel(
            self,
            text="⏳ Chargement du dashboard...\n\nSi c'est la première fois, cela peut prendre quelques secondes.",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        loading_label.grid(row=1, column=0, columnspan=2, pady=50)

    def _show_error(self, error_message: str):
        """Affiche un message d'erreur"""
        for widget in self.winfo_children():
            if widget != self.title_label:
                widget.destroy()

        error_label = ctk.CTkLabel(
            self,
            text=f"❌ Erreur lors du chargement:\n{error_message}",
            font=ctk.CTkFont(size=14),
            text_color="red"
        )
        error_label.grid(row=1, column=0, columnspan=2, pady=50)

    def _create_dashboard(self, snapshot, performance):
        """Crée le dashboard complet"""
        # Nettoyer les widgets existants (sauf le titre)
        for widget in self.winfo_children():
            if widget != self.title_label:
                widget.destroy()

        # Ligne 1: Cartes de statistiques principales
        self._create_main_stats_cards(snapshot)

        # Ligne 2: Performance et métriques
        self._create_performance_section(performance)

        # Ligne 3: Top positions
        self._create_top_positions(snapshot.positions)

    def _create_main_stats_cards(self, snapshot):
        """Crée les cartes de statistiques principales"""
        # Frame pour les cartes
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=20, sticky="ew")
        cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Carte 1: Valeur totale
        self._create_stat_card(
            cards_frame,
            "💰 Valeur Totale",
            format_currency(snapshot.current_value),
            row=0, column=0
        )

        # Carte 2: Capital investi
        self._create_stat_card(
            cards_frame,
            "📊 Capital Investi",
            format_currency(snapshot.total_invested),
            row=0, column=1
        )

        # Carte 3: Gains/Pertes
        gain_color = "#10b981" if snapshot.total_gain_loss >= 0 else "#ef4444"
        self._create_stat_card(
            cards_frame,
            "📈 Gains/Pertes",
            format_currency(snapshot.total_gain_loss),
            subtitle=format_percentage(snapshot.total_gain_loss_percent),
            value_color=gain_color,
            row=0, column=2
        )

        # Carte 4: Dividendes
        self._create_stat_card(
            cards_frame,
            "💵 Dividendes",
            format_currency(snapshot.dividend_income),
            row=0, column=3
        )

    def _create_stat_card(self, parent, title, value, subtitle="", value_color=None, row=0, column=0):
        """Crée une carte de statistique"""
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")

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
        value_label.pack(padx=20, pady=5)

        # Sous-titre (optionnel)
        if subtitle:
            subtitle_label = ctk.CTkLabel(
                card,
                text=subtitle,
                font=ctk.CTkFont(size=16),
                text_color=value_color
            )
            subtitle_label.pack(padx=20, pady=(0, 20))
        else:
            # Padding pour aligner toutes les cartes
            ctk.CTkLabel(card, text="").pack(pady=(0, 20))

    def _create_performance_section(self, performance):
        """Crée la section des métriques de performance"""
        perf_frame = ctk.CTkFrame(self, corner_radius=10)
        perf_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=10, sticky="ew")

        # Titre
        title = ctk.CTkLabel(
            perf_frame,
            text="📊 Métriques de Performance",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(padx=20, pady=(20, 10), anchor="w")

        # Grille de métriques
        metrics_grid = ctk.CTkFrame(perf_frame, fg_color="transparent")
        metrics_grid.pack(padx=20, pady=(0, 20), fill="x")
        metrics_grid.grid_columnconfigure((0, 1, 2), weight=1)

        # Rendement annualisé
        self._create_metric_row(
            metrics_grid,
            "📈 Rendement annualisé:",
            format_percentage(performance.annualized_return),
            row=0
        )

        # Dividend Yield
        self._create_metric_row(
            metrics_grid,
            "💵 Dividend Yield:",
            format_percentage(performance.dividend_yield),
            row=1
        )

        # Frais totaux
        self._create_metric_row(
            metrics_grid,
            "💸 Frais totaux:",
            format_currency(performance.total_fees_paid),
            row=2
        )

        # PRU moyen
        self._create_metric_row(
            metrics_grid,
            "📊 PRU moyen pondéré:",
            format_currency(performance.average_pru),
            row=3
        )

    def _create_metric_row(self, parent, label, value, row=0):
        """Crée une ligne de métrique"""
        label_widget = ctk.CTkLabel(
            parent,
            text=label,
            font=ctk.CTkFont(size=14),
            anchor="w"
        )
        label_widget.grid(row=row, column=0, padx=10, pady=8, sticky="w")

        value_widget = ctk.CTkLabel(
            parent,
            text=value,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="e"
        )
        value_widget.grid(row=row, column=1, padx=10, pady=8, sticky="e")

    def _create_top_positions(self, positions):
        """Crée la section des meilleures/pires positions"""
        if not positions:
            return

        # Trier par gain/perte en %
        sorted_positions = sorted(positions, key=lambda p: p['gain_loss_percent'], reverse=True)

        # Frame principal
        top_frame = ctk.CTkFrame(self, corner_radius=10)
        top_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")

        # Titre
        title = ctk.CTkLabel(
            top_frame,
            text="🏆 Top 3 Performers",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#10b981"
        )
        title.pack(padx=20, pady=(20, 10), anchor="w")

        # Top 3
        for i, pos in enumerate(sorted_positions[:3]):
            self._create_position_row(top_frame, pos, i + 1, is_top=True)

        # Frame pires positions
        bottom_frame = ctk.CTkFrame(self, corner_radius=10)
        bottom_frame.grid(row=3, column=1, padx=20, pady=10, sticky="nsew")

        # Titre
        title = ctk.CTkLabel(
            bottom_frame,
            text="📉 Bottom 3 Performers",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ef4444"
        )
        title.pack(padx=20, pady=(20, 10), anchor="w")

        # Bottom 3
        for i, pos in enumerate(sorted_positions[-3:][::-1]):
            self._create_position_row(bottom_frame, pos, i + 1, is_top=False)

    def _create_position_row(self, parent, position, rank, is_top=True):
        """Crée une ligne de position"""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(padx=20, pady=5, fill="x")

        # Rang
        rank_label = ctk.CTkLabel(
            row_frame,
            text=f"#{rank}",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=40
        )
        rank_label.pack(side="left", padx=(0, 10))

        # Ticker
        ticker_label = ctk.CTkLabel(
            row_frame,
            text=position['ticker'],
            font=ctk.CTkFont(size=14, weight="bold"),
            width=80,
            anchor="w"
        )
        ticker_label.pack(side="left")

        # Nom
        name_label = ctk.CTkLabel(
            row_frame,
            text=position['company_name'][:20],
            font=ctk.CTkFont(size=12),
            width=150,
            anchor="w"
        )
        name_label.pack(side="left", padx=10)

        # Gain/Perte
        gain_loss_percent = position['gain_loss_percent']
        color = "#10b981" if gain_loss_percent >= 0 else "#ef4444"

        gain_label = ctk.CTkLabel(
            row_frame,
            text=format_percentage(gain_loss_percent),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=color,
            anchor="e"
        )
        gain_label.pack(side="right", padx=10)

        amount_label = ctk.CTkLabel(
            row_frame,
            text=format_currency(position['gain_loss']),
            font=ctk.CTkFont(size=12),
            text_color=color,
            anchor="e"
        )
        amount_label.pack(side="right")
