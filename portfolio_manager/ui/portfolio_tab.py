# -*- coding: utf-8 -*-
"""
Onglet Portfolio - Vue d'ensemble des positions
"""

import customtkinter as ctk
from tkinter import messagebox
import threading
from portfolio_manager.core.portfolio import Portfolio
from portfolio_manager.utils.formatters import format_currency, format_percentage


class PortfolioTab(ctk.CTkScrollableFrame):
    """Onglet de gestion du portefeuille"""

    def __init__(self, parent, portfolio: Portfolio):
        super().__init__(parent)
        self.portfolio = portfolio

        # Configuration du grid pour layout responsive
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # Permettre à la liste de s'étendre

        # Titre
        self.title_label = ctk.CTkLabel(
            self,
            text="💼 Portfolio",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Bouton Rafraîchir en haut à droite
        self.btn_refresh = ctk.CTkButton(
            self,
            text="🔄 Rafraîchir les prix",
            command=self.refresh_prices,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.btn_refresh.grid(row=0, column=1, padx=20, pady=(20, 10), sticky="e")

        # Créer la structure des statistiques et de la liste
        self.stats_frame = None
        self._create_stats_frame()

        # Liste des positions
        self._create_positions_list()

        # Charger les données (cela remplira les stats et les positions)
        self.load_data()

    def _create_stats_frame(self):
        """Crée le frame pour les statistiques"""
        self.stats_frame = ctk.CTkFrame(self)
        self.stats_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        self.stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

    def _update_stats(self, snapshot):
        """Met à jour les statistiques avec les données du snapshot"""
        try:
            # Effacer les anciens widgets
            for widget in self.stats_frame.winfo_children():
                widget.destroy()

            stats = [
                ("Valeur Totale", format_currency(snapshot.current_value)),
                ("Capital Investi", format_currency(snapshot.total_invested)),
                ("Gain/Perte Total", f"{format_currency(snapshot.total_gain_loss)} ({format_percentage(snapshot.total_gain_loss_percent)})"),
                ("Positions", str(snapshot.positions_count))
            ]

            for i, (label, value) in enumerate(stats):
                frame = ctk.CTkFrame(self.stats_frame)
                frame.grid(row=0, column=i, padx=5, pady=10, sticky="ew")

                ctk.CTkLabel(
                    frame,
                    text=label,
                    font=ctk.CTkFont(size=11),
                    text_color="gray"
                ).pack(pady=(10, 5))

                # Couleur selon gain/perte
                text_color = None
                if "Gain/Perte" in label:
                    text_color = "#10b981" if snapshot.total_gain_loss >= 0 else "#ef4444"

                ctk.CTkLabel(
                    frame,
                    text=value,
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color=text_color
                ).pack(pady=(0, 10))

        except Exception as e:
            print(f"Erreur stats: {e}")
            import traceback
            traceback.print_exc()

    def _create_positions_list(self):
        """Crée la liste des positions"""
        # Frame pour la liste
        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(1, weight=1)  # Permettre au scroll frame de s'étendre

        # Titre
        title = ctk.CTkLabel(
            list_frame,
            text="Mes Positions",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="w")

        # Frame scrollable pour les positions
        self.positions_scroll = ctk.CTkScrollableFrame(list_frame, height=500)
        self.positions_scroll.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.positions_scroll.grid_columnconfigure(0, weight=1)

    def load_data(self):
        """Charge toutes les données (stats + positions) de manière asynchrone"""
        # Afficher un message de chargement
        self._show_loading_message()

        def do_load():
            try:
                # Charger le snapshot pour les stats
                snapshot = self.portfolio.get_portfolio_snapshot()

                # Mettre à jour l'interface dans le thread principal
                self.after(0, lambda: self._update_stats(snapshot))
                self.after(0, self.load_positions)

            except Exception as e:
                print(f"Erreur load_data: {e}")
                import traceback
                traceback.print_exc()
                self.after(0, lambda: self._show_error(str(e)))

        # Lancer le chargement dans un thread
        thread = threading.Thread(target=do_load, daemon=True)
        thread.start()

    def _show_loading_message(self):
        """Affiche un message de chargement"""
        # Effacer les positions
        for widget in self.positions_scroll.winfo_children():
            widget.destroy()

        loading_label = ctk.CTkLabel(
            self.positions_scroll,
            text="⏳ Chargement des données...\n\nSi c'est la première fois, cela peut prendre 1-2 minutes.",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        loading_label.pack(pady=50)

    def _show_error(self, error_msg):
        """Affiche un message d'erreur"""
        for widget in self.positions_scroll.winfo_children():
            widget.destroy()

        error_label = ctk.CTkLabel(
            self.positions_scroll,
            text=f"❌ Erreur lors du chargement:\n{error_msg}",
            font=ctk.CTkFont(size=14),
            text_color="red"
        )
        error_label.pack(pady=50)

    def load_positions(self):
        """Charge et affiche toutes les positions"""
        # Effacer le contenu précédent
        for widget in self.positions_scroll.winfo_children():
            widget.destroy()

        try:
            # Essayer de charger les positions avec prix actuels
            try:
                positions = self.portfolio.get_current_positions()
                print(f"DEBUG: Nombre de positions chargées: {len(positions)}")
            except Exception as e:
                print(f"Erreur lors du chargement des prix: {e}")
                # Si ça échoue, charger les positions de base sans prix actuels
                positions = self.portfolio.db.get_current_positions()
                print(f"DEBUG: Positions chargées sans prix (base de données): {len(positions)}")

            if not positions:
                no_data = ctk.CTkLabel(
                    self.positions_scroll,
                    text="Aucune position dans le portefeuille.\nAjoutez des transactions pour voir vos positions ici.",
                    font=ctk.CTkFont(size=14),
                    text_color="gray"
                )
                no_data.pack(pady=50)
                return

            # En-têtes
            headers_frame = ctk.CTkFrame(self.positions_scroll)
            headers_frame.pack(fill="x", padx=5, pady=(5, 10))

            headers = [
                ("Ticker", 100),
                ("Société", 200),
                ("Qté", 80),
                ("PRU", 100),
                ("Val. investie", 120),
                ("Prix actuel", 100),
                ("Val. actuelle", 120),
                ("+/- valeur", 120),
                ("+/- %", 100),
                ("Répartition", 100),
                ("Actions", 100)
            ]

            for i, (header, width) in enumerate(headers):
                label = ctk.CTkLabel(
                    headers_frame,
                    text=header,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    width=width
                )
                label.grid(row=0, column=i, padx=5, pady=5)

            # Calculer la valeur totale pour le poids
            total_value = sum(p.current_value for p in positions)

            # Lignes de positions
            for idx, pos in enumerate(positions):
                self._create_position_row(pos, idx, total_value)

        except Exception as e:
            error_label = ctk.CTkLabel(
                self.positions_scroll,
                text=f"❌ Erreur: {str(e)}",
                font=ctk.CTkFont(size=14),
                text_color="red"
            )
            error_label.pack(pady=50)

    def _create_position_row(self, pos, idx, total_value):
        """Crée une ligne de position"""
        row_frame = ctk.CTkFrame(self.positions_scroll)
        row_frame.pack(fill="x", padx=5, pady=2)

        # Couleur selon gain/perte
        if pos.unrealized_gain_loss >= 0:
            fg_color = ("gray85", "gray25")
        else:
            fg_color = ("gray90", "gray20")

        row_frame.configure(fg_color=fg_color)

        # Ticker
        ctk.CTkLabel(row_frame, text=pos.ticker, width=100, font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=5, pady=8)

        # Société (tronquée si trop longue)
        company = pos.company_name[:20] + "..." if len(pos.company_name) > 20 else pos.company_name
        ctk.CTkLabel(row_frame, text=company, width=200, anchor="w").grid(row=0, column=1, padx=5, pady=8)

        # Quantité
        ctk.CTkLabel(row_frame, text=f"{pos.quantity:.2f}", width=80).grid(row=0, column=2, padx=5, pady=8)

        # PRU (Prix de Revient Unitaire)
        ctk.CTkLabel(row_frame, text=format_currency(pos.pru), width=100).grid(row=0, column=3, padx=5, pady=8)

        # Valeur Investie
        ctk.CTkLabel(
            row_frame,
            text=format_currency(pos.total_invested),
            width=120,
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=4, padx=5, pady=8)

        # Prix Actuel
        if pos.current_price > 0:
            price_color = "#10b981" if pos.current_price > pos.pru else "#ef4444" if pos.current_price < pos.pru else None
            price_text = format_currency(pos.current_price)
        else:
            price_color = "gray"
            price_text = "N/A"

        ctk.CTkLabel(
            row_frame,
            text=price_text,
            width=100,
            text_color=price_color,
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=5, padx=5, pady=8)

        # Valeur actuelle
        value_text = format_currency(pos.current_value)
        ctk.CTkLabel(
            row_frame,
            text=value_text,
            width=120,
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=6, padx=5, pady=8)

        # Gain/Perte en valeur
        gain_loss_color = "#10b981" if pos.unrealized_gain_loss >= 0 else "#ef4444"
        gain_text = format_currency(pos.unrealized_gain_loss)
        percent_text = format_percentage(pos.unrealized_gain_loss_percent)

        ctk.CTkLabel(
            row_frame,
            text=gain_text,
            width=120,
            text_color=gain_loss_color,
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=7, padx=5, pady=8)

        # Gain/Perte en %
        ctk.CTkLabel(
            row_frame,
            text=percent_text,
            width=100,
            text_color=gain_loss_color,
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=8, padx=5, pady=8)

        # Poids dans le portefeuille
        weight = (pos.current_value / total_value * 100) if total_value > 0 else 0
        ctk.CTkLabel(
            row_frame,
            text=format_percentage(weight, decimals=1, show_sign=False),
            width=100
        ).grid(row=0, column=9, padx=5, pady=8)

        # Bouton Détails
        btn_details = ctk.CTkButton(
            row_frame,
            text="👁️",
            width=40,
            command=lambda: self.show_position_details(pos.ticker),
            fg_color="transparent",
            hover_color=("#3b82f6", "#2563eb")
        )
        btn_details.grid(row=0, column=10, padx=5, pady=5)

    def show_position_details(self, ticker: str):
        """Affiche les détails d'une position"""
        try:
            details = self.portfolio.get_position_details(ticker)

            if not details:
                messagebox.showerror("Erreur", f"Impossible de récupérer les détails pour {ticker}")
                return

            # Créer une fenêtre popup pour les détails
            dialog = ctk.CTkToplevel(self)
            dialog.title(f"Détails - {ticker}")
            dialog.geometry("800x700")
            dialog.resizable(True, True)
            dialog.minsize(700, 600)

            # Centrer la fenêtre
            dialog.transient(self.master)
            dialog.grab_set()

            dialog.update_idletasks()
            x = self.winfo_toplevel().winfo_x() + (self.winfo_toplevel().winfo_width() // 2) - (800 // 2)
            y = self.winfo_toplevel().winfo_y() + (self.winfo_toplevel().winfo_height() // 2) - (700 // 2)
            dialog.geometry(f"+{x}+{y}")

            # Frame scrollable
            scroll_frame = ctk.CTkScrollableFrame(dialog)
            scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

            pos = details['position']

            # Titre
            title = ctk.CTkLabel(
                scroll_frame,
                text=f"{pos.ticker} - {pos.company_name}",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title.pack(pady=(10, 20))

            # Informations principales
            info_frame = ctk.CTkFrame(scroll_frame)
            info_frame.pack(fill="x", pady=10)
            info_frame.grid_columnconfigure((0, 1), weight=1)

            info_data = [
                ("Quantité détenue", f"{pos.quantity:.2f}"),
                ("Prix de Revient Unitaire (PRU)", format_currency(pos.pru)),
                ("Capital investi", format_currency(pos.total_invested)),
                ("Prix actuel", format_currency(pos.current_price)),
                ("Valeur actuelle", format_currency(pos.current_value)),
                ("Gain/Perte", f"{format_currency(pos.unrealized_gain_loss)} ({format_percentage(pos.unrealized_gain_loss_percent)})"),
                ("Dividend Yield", format_percentage(details['dividend_yield'])),
                ("Dividendes reçus", format_currency(details['total_dividends_received']))
            ]

            for i, (label, value) in enumerate(info_data):
                row = i // 2
                col = i % 2

                item_frame = ctk.CTkFrame(info_frame)
                item_frame.grid(row=row, column=col, padx=10, pady=5, sticky="ew")

                ctk.CTkLabel(
                    item_frame,
                    text=label,
                    font=ctk.CTkFont(size=11),
                    text_color="gray"
                ).pack(pady=(10, 2), anchor="w", padx=10)

                text_color = None
                if "Gain/Perte" in label:
                    text_color = "#10b981" if pos.unrealized_gain_loss >= 0 else "#ef4444"

                ctk.CTkLabel(
                    item_frame,
                    text=value,
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color=text_color
                ).pack(pady=(2, 10), anchor="w", padx=10)

            # Historique des transactions
            trans_title = ctk.CTkLabel(
                scroll_frame,
                text="Historique des Transactions",
                font=ctk.CTkFont(size=18, weight="bold")
            )
            trans_title.pack(pady=(20, 10), anchor="w")

            transactions = details['transactions']
            if transactions:
                for tx in transactions:
                    tx_frame = ctk.CTkFrame(scroll_frame)
                    tx_frame.pack(fill="x", pady=2)

                    tx_type_color = "#10b981" if tx.transaction_type == "ACHAT" else "#ef4444"

                    tx_text = f"{tx.transaction_date} - {tx.transaction_type}: {tx.quantity} × {format_currency(tx.price_per_share)} = {format_currency(tx.total_cost)}"

                    ctk.CTkLabel(
                        tx_frame,
                        text=tx_text,
                        font=ctk.CTkFont(size=12),
                        text_color=tx_type_color
                    ).pack(pady=8, padx=10, anchor="w")
            else:
                ctk.CTkLabel(
                    scroll_frame,
                    text="Aucune transaction",
                    text_color="gray"
                ).pack(pady=5, anchor="w")

            # Bouton Fermer
            btn_close = ctk.CTkButton(
                dialog,
                text="Fermer",
                command=dialog.destroy,
                width=200,
                height=40
            )
            btn_close.pack(pady=20)

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des détails:\n{str(e)}")

    def refresh_prices(self):
        """Rafraîchit les prix du marché de manière asynchrone"""
        # Désactiver le bouton pendant le rafraîchissement
        self.btn_refresh.configure(state="disabled", text="⏳ Rafraîchissement...")

        def do_refresh():
            try:
                count = self.portfolio.refresh_market_data_if_needed(force=True)

                # Réactiver le bouton et recharger dans le thread principal
                self.after(0, lambda: self.btn_refresh.configure(state="normal", text="🔄 Rafraîchir les prix"))
                self.after(0, self.load_data)
                self.after(0, lambda: messagebox.showinfo("Succès", f"✅ {count} ticker(s) mis à jour"))

            except Exception as e:
                self.after(0, lambda: self.btn_refresh.configure(state="normal", text="🔄 Rafraîchir les prix"))
                self.after(0, lambda: messagebox.showerror("Erreur", f"Erreur lors du rafraîchissement:\n{str(e)}"))
                import traceback
                traceback.print_exc()

        # Lancer dans un thread
        thread = threading.Thread(target=do_refresh, daemon=True)
        thread.start()
