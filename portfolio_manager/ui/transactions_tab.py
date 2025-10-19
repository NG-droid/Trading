# -*- coding: utf-8 -*-
"""
Onglet Transactions - Historique et ajout de transactions
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from typing import Tuple

from portfolio_manager.core.portfolio import Portfolio
from portfolio_manager.core.calculator import FinancialCalculator
from portfolio_manager.utils.formatters import format_currency, format_date, format_percentage
from portfolio_manager.config import CAC40_TICKERS
from portfolio_manager.ui.components.filters import PeriodFilter


class TransactionsTab(ctk.CTkScrollableFrame):
    """Onglet de gestion des transactions"""

    def __init__(self, parent, portfolio: Portfolio):
        super().__init__(parent)
        self.portfolio = portfolio

        # Configuration du grid pour un layout responsive
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)  # Colonne pour le bouton
        self.grid_rowconfigure(2, weight=1)  # Permettre à la liste de s'étendre

        # Titre
        self.title_label = ctk.CTkLabel(
            self,
            text="📝 Transactions",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Bouton Ajouter en haut à droite
        self.btn_add = ctk.CTkButton(
            self,
            text="➕ Nouvelle Transaction",
            command=self.show_add_form,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.btn_add.grid(row=0, column=1, padx=20, pady=(20, 10), sticky="e")

        # Filtres
        self.filters = PeriodFilter(
            self,
            on_filter_change=self._on_filter_change,
            show_transaction_type=True,
            transaction_types=["Tout", "ACHAT", "VENTE"]
        )
        self.filters.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="ew")

        # Statistiques rapides
        self._create_stats()

        # Liste des transactions
        self._create_transactions_list()

        # Charger les données
        self.load_transactions()

    def _create_stats(self):
        """Crée les statistiques rapides"""
        # Détruire le frame existant s'il existe
        if hasattr(self, 'stats_frame') and self.stats_frame.winfo_exists():
            self.stats_frame.destroy()

        self.stats_frame = ctk.CTkFrame(self)
        self.stats_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        self.stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        try:
            # Récupérer les filtres actuels
            start_date, end_date = self.filters.get_date_range() if hasattr(self, 'filters') else (None, None)
            tx_type = self.filters.get_transaction_type() if hasattr(self, 'filters') else None

            transactions = self.portfolio.get_all_transactions()

            # Appliquer les mêmes filtres que load_transactions
            if start_date and end_date:
                transactions = [
                    t for t in transactions
                    if start_date <= t.transaction_date <= end_date
                ]

            if tx_type:
                transactions = [
                    t for t in transactions
                    if t.transaction_type == tx_type
                ]

            achats = [t for t in transactions if t.transaction_type == "ACHAT"]
            ventes = [t for t in transactions if t.transaction_type == "VENTE"]

            total_achats = sum(t.quantity * t.price_per_share + t.fees for t in achats)
            total_ventes = sum(t.quantity * t.price_per_share - t.fees for t in ventes)

            stats = [
                ("Transactions totales", str(len(transactions))),
                ("Achats", f"{len(achats)} ({format_currency(total_achats)})"),
                ("Ventes", f"{len(ventes)} ({format_currency(total_ventes)})"),
                ("Frais totaux", format_currency(sum(t.fees for t in transactions)))
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

                ctk.CTkLabel(
                    frame,
                    text=value,
                    font=ctk.CTkFont(size=16, weight="bold")
                ).pack(pady=(0, 10))

        except Exception as e:
            print(f"Erreur stats: {e}")

    def _create_transactions_list(self):
        """Crée la liste des transactions"""
        # Frame pour la liste
        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=3, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(2, weight=1)  # Permettre au scroll frame de s'étendre

        # Titre
        title = ctk.CTkLabel(
            list_frame,
            text="Historique des Transactions",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="w")

        # Frame pour les en-têtes FIXES (ne scrolle pas)
        self.headers_frame_container = ctk.CTkFrame(list_frame)
        self.headers_frame_container.grid(row=1, column=0, padx=10, pady=(0, 0), sticky="ew")

        # Frame scrollable pour les transactions (hauteur optimisée à 450px)
        self.transactions_scroll = ctk.CTkScrollableFrame(list_frame, height=450)
        self.transactions_scroll.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.transactions_scroll.grid_columnconfigure(0, weight=1)

    def load_transactions(self, start_date=None, end_date=None, transaction_type=None):
        """Charge et affiche toutes les transactions avec filtres optionnels"""
        # Effacer le contenu précédent du scroll
        for widget in self.transactions_scroll.winfo_children():
            widget.destroy()

        # Effacer les en-têtes précédents
        for widget in self.headers_frame_container.winfo_children():
            widget.destroy()

        try:
            transactions = self.portfolio.get_all_transactions()

            # Appliquer les filtres
            if start_date and end_date:
                transactions = [
                    t for t in transactions
                    if start_date <= t.transaction_date <= end_date
                ]

            if transaction_type:
                transactions = [
                    t for t in transactions
                    if t.transaction_type == transaction_type
                ]

            # Créer les en-têtes FIXES (hors du scroll)
            headers = [
                ("Date", 100),
                ("Type", 80),
                ("Ticker", 100),
                ("Société", 200),
                ("Qté", 80),
                ("Prix", 100),
                ("Total", 120),
                ("Frais", 80),
                ("P&L", 120),
                ("P&L %", 100),
                ("Actions", 150)
            ]

            headers_frame = ctk.CTkFrame(self.headers_frame_container)
            headers_frame.pack(fill="x", padx=5, pady=(5, 5))

            for i, (header, width) in enumerate(headers):
                label = ctk.CTkLabel(
                    headers_frame,
                    text=header,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    width=width
                )
                label.grid(row=0, column=i, padx=5, pady=5)

            # Si aucune transaction
            if not transactions:
                no_data = ctk.CTkLabel(
                    self.transactions_scroll,
                    text="Aucune transaction enregistrée.\nCliquez sur '➕ Nouvelle Transaction' pour commencer.",
                    font=ctk.CTkFont(size=14),
                    text_color="gray"
                )
                no_data.pack(pady=50)
                return

            # Transactions (les plus récentes en premier)
            for idx, tx in enumerate(reversed(transactions)):
                self._create_transaction_row(tx, idx)

        except Exception as e:
            error_label = ctk.CTkLabel(
                self.transactions_scroll,
                text=f"❌ Erreur: {str(e)}",
                font=ctk.CTkFont(size=14),
                text_color="red"
            )
            error_label.pack(pady=50)

    def _create_transaction_row(self, tx, idx):
        """Crée une ligne de transaction"""
        row_frame = ctk.CTkFrame(self.transactions_scroll)
        row_frame.pack(fill="x", padx=5, pady=2)

        # Couleur selon le type
        if tx.transaction_type == "ACHAT":
            fg_color = ("gray85", "gray25")
        else:
            fg_color = ("gray90", "gray20")

        row_frame.configure(fg_color=fg_color)

        # Date
        # Convertir la date string (YYYY-MM-DD) en format d'affichage (JJ/MM/AAAA)
        try:
            date_obj = datetime.strptime(tx.transaction_date, "%Y-%m-%d")
            date_str = date_obj.strftime("%d/%m/%Y")
        except:
            date_str = tx.transaction_date  # Afficher tel quel en cas d'erreur
        ctk.CTkLabel(row_frame, text=date_str, width=100).grid(row=0, column=0, padx=5, pady=8)

        # Type
        type_color = "#10b981" if tx.transaction_type == "ACHAT" else "#ef4444"
        ctk.CTkLabel(
            row_frame,
            text=tx.transaction_type,
            width=80,
            text_color=type_color,
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=1, padx=5, pady=8)

        # Ticker
        ctk.CTkLabel(row_frame, text=tx.ticker, width=100).grid(row=0, column=2, padx=5, pady=8)

        # Société
        company = tx.company_name[:25] + "..." if len(tx.company_name) > 25 else tx.company_name
        ctk.CTkLabel(row_frame, text=company, width=200, anchor="w").grid(row=0, column=3, padx=5, pady=8)

        # Quantité
        ctk.CTkLabel(row_frame, text=f"{tx.quantity:.2f}", width=80).grid(row=0, column=4, padx=5, pady=8)

        # Prix
        ctk.CTkLabel(row_frame, text=format_currency(tx.price_per_share), width=100).grid(row=0, column=5, padx=5, pady=8)

        # Total
        total = tx.quantity * tx.price_per_share
        if tx.transaction_type == "ACHAT":
            total += tx.fees
        else:
            total -= tx.fees
        ctk.CTkLabel(
            row_frame,
            text=format_currency(total),
            width=120,
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=6, padx=5, pady=8)

        # Frais
        ctk.CTkLabel(row_frame, text=format_currency(tx.fees), width=80).grid(row=0, column=7, padx=5, pady=8)

        # Gain / perte réalisée (uniquement pour les ventes)
        pnl_text = "-"
        pnl_percent_text = "-"
        pnl_color = "gray"

        if tx.transaction_type == "VENTE":
            try:
                pnl_amount, pnl_percent = self._calculate_realized_pnl(tx)
                pnl_text = format_currency(pnl_amount)
                pnl_percent_text = format_percentage(pnl_percent)
                pnl_color = "#10b981" if pnl_amount >= 0 else "#ef4444"
            except Exception as e:
                print(f"Erreur calcul P&L pour {tx.ticker} ({tx.id}): {e}")

        ctk.CTkLabel(
            row_frame,
            text=pnl_text,
            width=120,
            text_color=pnl_color,
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=8, padx=5, pady=8)

        ctk.CTkLabel(
            row_frame,
            text=pnl_percent_text,
            width=100,
            text_color=pnl_color,
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=9, padx=5, pady=8)

        # Frame pour les boutons d'actions
        actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        actions_frame.grid(row=0, column=10, padx=5, pady=5)

        # Bouton Modifier
        btn_edit = ctk.CTkButton(
            actions_frame,
            text="✏️",
            width=40,
            command=lambda: self.edit_transaction(tx),
            fg_color="transparent",
            hover_color=("#3b82f6", "#2563eb")
        )
        btn_edit.pack(side="left", padx=2)

        # Bouton Supprimer
        btn_delete = ctk.CTkButton(
            actions_frame,
            text="🗑️",
            width=40,
            command=lambda: self.delete_transaction(tx.id),
            fg_color="transparent",
            hover_color=("#ef4444", "#dc2626")
        )
        btn_delete.pack(side="left", padx=2)

    def _calculate_realized_pnl(self, sale_tx) -> Tuple[float, float]:
        """Calcule la plus-value réalisée pour une transaction de vente."""
        transactions = self.portfolio.get_transactions_by_ticker(sale_tx.ticker)
        # Trier par date puis id pour assurer l'ordre
        transactions = sorted(
            transactions,
            key=lambda t: (t.transaction_date, t.id or 0)
        )

        remaining_buys = []
        for tx in transactions:
            if tx.transaction_type == 'ACHAT':
                remaining_buys.append(tx)
            elif tx.transaction_type == 'VENTE':
                if tx.id == sale_tx.id:
                    result = FinancialCalculator.calculate_realized_pv_fifo(remaining_buys, sale_tx)
                    return result.total_gain_loss, result.gain_loss_percent
                remaining_buys = FinancialCalculator._update_remaining_buys(
                    remaining_buys,
                    tx.quantity
                )

        raise ValueError("Transaction de vente introuvable pour le calcul du P&L")

    def show_add_form(self):
        """Affiche le formulaire d'ajout de transaction"""
        # Créer une fenêtre popup
        dialog = ctk.CTkToplevel(self)
        dialog.title("Nouvelle Transaction")
        dialog.geometry("680x820")
        dialog.minsize(660, 800)
        dialog.resizable(False, False)

        # Centrer la fenêtre sur l'écran parent
        dialog.transient(self.master)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.winfo_toplevel().winfo_x() + (self.winfo_toplevel().winfo_width() // 2) - (550 // 2)
        y = self.winfo_toplevel().winfo_y() + (self.winfo_toplevel().winfo_height() // 2) - (680 // 2)
        dialog.geometry(f"+{x}+{y}")

        # Titre
        title = ctk.CTkLabel(
            dialog,
            text="➕ Ajouter une Transaction",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(20, 10))

        form_frame = ctk.CTkFrame(dialog)
        form_frame.pack(padx=30, pady=10, fill="both", expand=True)

        # Type de transaction
        ctk.CTkLabel(form_frame, text="Type de transaction:", anchor="w").pack(pady=(18, 4), padx=20, fill="x")
        type_var = ctk.StringVar(value="ACHAT")
        type_frame = ctk.CTkFrame(form_frame)
        type_frame.pack(pady=5, padx=20, fill="x")

        ctk.CTkRadioButton(
            type_frame,
            text="Achat",
            variable=type_var,
            value="ACHAT"
        ).pack(side="left", padx=20)

        ctk.CTkRadioButton(
            type_frame,
            text="Vente",
            variable=type_var,
            value="VENTE"
        ).pack(side="left", padx=20)

        # Ticker (avec suggestions CAC40)
        ctk.CTkLabel(form_frame, text="Ticker:", anchor="w").pack(pady=(12, 4), padx=20, fill="x")

        # Créer la liste des tickers avec format "Société : TICKER"
        ticker_display_list = [f"{company} : {ticker}" for ticker, company in CAC40_TICKERS.items()]
        ticker_display_list.sort()  # Tri alphabétique

        ticker_var = ctk.StringVar()
        ticker_combo = ctk.CTkComboBox(
            form_frame,
            variable=ticker_var,
            values=ticker_display_list,
            width=360
        )
        ticker_combo.pack(pady=5, padx=20, fill="x")

        # Nom de la société
        ctk.CTkLabel(form_frame, text="Nom de la société:", anchor="w").pack(pady=(12, 4), padx=20, fill="x")
        company_var = ctk.StringVar()
        company_entry = ctk.CTkEntry(form_frame, textvariable=company_var)
        company_entry.pack(pady=5, padx=20, fill="x")

        # Auto-fill company name when ticker is selected
        def on_ticker_change(*args):
            selected = ticker_var.get()
            # Extraire le ticker du format "Société : TICKER"
            if " : " in selected:
                company_name, ticker_code = selected.split(" : ")
                company_var.set(company_name)
            elif selected in CAC40_TICKERS:
                # Si c'est juste le ticker (pour compatibilité)
                company_var.set(CAC40_TICKERS[selected])

        ticker_var.trace_add("write", on_ticker_change)

        # Quantité
        ctk.CTkLabel(form_frame, text="Quantité:", anchor="w").pack(pady=(12, 4), padx=20, fill="x")
        qty_var = ctk.StringVar()
        qty_entry = ctk.CTkEntry(form_frame, textvariable=qty_var, width=360)
        qty_entry.pack(pady=5, padx=20, fill="x")

        # Prix par action
        ctk.CTkLabel(form_frame, text="Prix par action (€):", anchor="w").pack(pady=(12, 4), padx=20, fill="x")
        price_var = ctk.StringVar()
        price_entry = ctk.CTkEntry(form_frame, textvariable=price_var, width=360)
        price_entry.pack(pady=5, padx=20, fill="x")

        # Date
        ctk.CTkLabel(form_frame, text="Date (JJ/MM/AAAA):", anchor="w").pack(pady=(12, 4), padx=20, fill="x")
        date_var = ctk.StringVar(value=datetime.now().strftime("%d/%m/%Y"))
        date_entry = ctk.CTkEntry(form_frame, textvariable=date_var, width=360)
        date_entry.pack(pady=5, padx=20, fill="x")

        # Frais
        ctk.CTkLabel(form_frame, text="Frais de transaction (€):", anchor="w").pack(pady=(12, 4), padx=20, fill="x")
        fees_var = ctk.StringVar(value="1.00")
        fees_entry = ctk.CTkEntry(form_frame, textvariable=fees_var, width=360)
        fees_entry.pack(pady=5, padx=20, fill="x")

        # Notes (optionnel)
        ctk.CTkLabel(form_frame, text="Notes (optionnel):", anchor="w").pack(pady=(12, 4), padx=20, fill="x")
        notes_var = ctk.StringVar()
        notes_entry = ctk.CTkEntry(form_frame, textvariable=notes_var, width=360)
        notes_entry.pack(pady=5, padx=20, fill="x")

        # Boutons
        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.pack(pady=20)

        def add_transaction():
            try:
                # Validation
                ticker_input = ticker_var.get().strip()

                # Extraire le ticker du format "Société : TICKER"
                if " : " in ticker_input:
                    company_from_ticker, ticker = ticker_input.split(" : ")
                    ticker = ticker.upper()
                else:
                    ticker = ticker_input.upper()

                company = company_var.get().strip()
                quantity = float(qty_var.get().strip())
                price = float(price_var.get().strip())
                date_str = date_var.get().strip()
                fees = float(fees_var.get().strip())
                tx_type = type_var.get()
                notes = notes_var.get().strip()

                if not ticker or not company:
                    messagebox.showerror("Erreur", "Veuillez remplir le ticker et le nom de la société")
                    return

                # Convertir la date
                date_parts = date_str.split("/")
                if len(date_parts) == 3:
                    date_formatted = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"
                else:
                    date_formatted = date_str

                # Ajouter la transaction
                self.portfolio.add_transaction(
                    ticker=ticker,
                    company_name=company,
                    transaction_type=tx_type,
                    quantity=quantity,
                    price_per_share=price,
                    transaction_date=date_formatted,
                    notes=notes if notes else None
                )

                # Fermer la fenêtre
                dialog.destroy()

                # Recharger les transactions
                self.load_transactions()
                self._create_stats()

                # Message de succès
                messagebox.showinfo("Succès", f"✅ Transaction ajoutée: {tx_type} de {quantity} {ticker}")

            except ValueError as e:
                messagebox.showerror("Erreur de saisie", f"Veuillez vérifier les valeurs numériques:\n{str(e)}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'ajout:\n{str(e)}")

        ctk.CTkButton(
            btn_frame,
            text="✅ Ajouter",
            command=add_transaction,
            width=200,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="❌ Annuler",
            command=dialog.destroy,
            width=200,
            height=40,
            fg_color="gray",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=10)

    def edit_transaction(self, tx):
        """Affiche le formulaire de modification de transaction"""
        # Créer une fenêtre popup
        dialog = ctk.CTkToplevel(self)
        dialog.title("Modifier la Transaction")
        dialog.geometry("700x850")
        dialog.resizable(True, True)
        dialog.minsize(600, 700)

        # Centrer la fenêtre sur l'écran parent
        dialog.transient(self.master)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.winfo_toplevel().winfo_x() + (self.winfo_toplevel().winfo_width() // 2) - (700 // 2)
        y = self.winfo_toplevel().winfo_y() + (self.winfo_toplevel().winfo_height() // 2) - (850 // 2)
        dialog.geometry(f"+{x}+{y}")

        # Titre
        title = ctk.CTkLabel(
            dialog,
            text="✏️ Modifier la Transaction",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)

        # Frame scrollable pour le formulaire
        scroll_frame = ctk.CTkScrollableFrame(dialog)
        scroll_frame.pack(padx=20, pady=10, fill="both", expand=True)

        # Frame du formulaire
        form_frame = ctk.CTkFrame(scroll_frame)
        form_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Type de transaction
        ctk.CTkLabel(form_frame, text="Type de transaction:", anchor="w").pack(pady=(20, 5), padx=20, fill="x")
        type_var = ctk.StringVar(value=tx.transaction_type)
        type_frame = ctk.CTkFrame(form_frame)
        type_frame.pack(pady=5, padx=20, fill="x")

        ctk.CTkRadioButton(
            type_frame,
            text="Achat",
            variable=type_var,
            value="ACHAT"
        ).pack(side="left", padx=20)

        ctk.CTkRadioButton(
            type_frame,
            text="Vente",
            variable=type_var,
            value="VENTE"
        ).pack(side="left", padx=20)

        # Ticker (avec suggestions CAC40)
        ctk.CTkLabel(form_frame, text="Ticker:", anchor="w").pack(pady=(15, 5), padx=20, fill="x")

        # Créer la liste des tickers avec format "Société : TICKER"
        ticker_display_list = [f"{company} : {ticker}" for ticker, company in CAC40_TICKERS.items()]
        ticker_display_list.sort()

        # Pré-remplir avec le format "Société : TICKER"
        current_ticker_display = f"{tx.company_name} : {tx.ticker}"
        ticker_var = ctk.StringVar(value=current_ticker_display)
        ticker_combo = ctk.CTkComboBox(
            form_frame,
            variable=ticker_var,
            values=ticker_display_list
        )
        ticker_combo.pack(pady=5, padx=20, fill="x")

        # Nom de la société
        ctk.CTkLabel(form_frame, text="Nom de la société:", anchor="w").pack(pady=(15, 5), padx=20, fill="x")
        company_var = ctk.StringVar(value=tx.company_name)
        company_entry = ctk.CTkEntry(form_frame, textvariable=company_var)
        company_entry.pack(pady=5, padx=20, fill="x")

        # Auto-fill company name when ticker is selected
        def on_ticker_change(*args):
            selected = ticker_var.get()
            if " : " in selected:
                company_name, ticker_code = selected.split(" : ")
                company_var.set(company_name)
            elif selected in CAC40_TICKERS:
                company_var.set(CAC40_TICKERS[selected])

        ticker_var.trace_add("write", on_ticker_change)

        # Quantité
        ctk.CTkLabel(form_frame, text="Quantité:", anchor="w").pack(pady=(15, 5), padx=20, fill="x")
        qty_var = ctk.StringVar(value=str(tx.quantity))
        qty_entry = ctk.CTkEntry(form_frame, textvariable=qty_var)
        qty_entry.pack(pady=5, padx=20, fill="x")

        # Prix par action
        ctk.CTkLabel(form_frame, text="Prix par action (€):", anchor="w").pack(pady=(15, 5), padx=20, fill="x")
        price_var = ctk.StringVar(value=str(tx.price_per_share))
        price_entry = ctk.CTkEntry(form_frame, textvariable=price_var)
        price_entry.pack(pady=5, padx=20, fill="x")

        # Date
        ctk.CTkLabel(form_frame, text="Date (JJ/MM/AAAA):", anchor="w").pack(pady=(15, 5), padx=20, fill="x")
        # Convertir la date de YYYY-MM-DD en JJ/MM/AAAA pour l'affichage
        try:
            date_obj = datetime.strptime(tx.transaction_date, "%Y-%m-%d")
            date_display = date_obj.strftime("%d/%m/%Y")
        except:
            date_display = tx.transaction_date
        date_var = ctk.StringVar(value=date_display)
        date_entry = ctk.CTkEntry(form_frame, textvariable=date_var)
        date_entry.pack(pady=5, padx=20, fill="x")

        # Frais (lecture seule, information)
        ctk.CTkLabel(form_frame, text="Frais de transaction (€):", anchor="w").pack(pady=(15, 5), padx=20, fill="x")
        fees_var = ctk.StringVar(value=str(tx.fees))
        fees_entry = ctk.CTkEntry(form_frame, textvariable=fees_var)
        fees_entry.pack(pady=5, padx=20, fill="x")

        # Notes (optionnel)
        ctk.CTkLabel(form_frame, text="Notes (optionnel):", anchor="w").pack(pady=(15, 5), padx=20, fill="x")
        notes_var = ctk.StringVar(value=tx.notes if tx.notes else "")
        notes_entry = ctk.CTkEntry(form_frame, textvariable=notes_var)
        notes_entry.pack(pady=5, padx=20, fill="x")

        # Boutons
        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.pack(pady=20)

        def update_transaction():
            try:
                # Validation
                ticker_input = ticker_var.get().strip()

                # Extraire le ticker du format "Société : TICKER"
                if " : " in ticker_input:
                    company_from_ticker, ticker = ticker_input.split(" : ")
                    ticker = ticker.upper()
                else:
                    ticker = ticker_input.upper()

                company = company_var.get().strip()
                quantity = float(qty_var.get().strip())
                price = float(price_var.get().strip())
                date_str = date_var.get().strip()
                fees = float(fees_var.get().strip())
                tx_type = type_var.get()
                notes = notes_var.get().strip()

                if not ticker or not company:
                    messagebox.showerror("Erreur", "Veuillez remplir le ticker et le nom de la société")
                    return

                # Convertir la date
                date_parts = date_str.split("/")
                if len(date_parts) == 3:
                    date_formatted = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"
                else:
                    date_formatted = date_str

                # Calculer le nouveau total_cost
                if tx_type.upper() == 'ACHAT':
                    total_cost = (quantity * price) + fees
                else:
                    total_cost = (quantity * price) - fees

                # Créer l'objet Transaction modifié
                from portfolio_manager.database.models import Transaction
                updated_tx = Transaction(
                    id=tx.id,
                    ticker=ticker,
                    company_name=company,
                    transaction_type=tx_type,
                    quantity=quantity,
                    price_per_share=price,
                    transaction_date=date_formatted,
                    total_cost=total_cost,
                    fees=fees,
                    notes=notes if notes else None
                )

                # Mettre à jour dans la base de données
                self.portfolio.db.update_transaction(updated_tx)

                # Fermer la fenêtre
                dialog.destroy()

                # Recharger les transactions
                self.load_transactions()
                self._create_stats()

                # Message de succès
                messagebox.showinfo("Succès", f"✅ Transaction modifiée: {tx_type} de {quantity} {ticker}")

            except ValueError as e:
                messagebox.showerror("Erreur de saisie", f"Veuillez vérifier les valeurs numériques:\n{str(e)}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la modification:\n{str(e)}")

        ctk.CTkButton(
            btn_frame,
            text="✅ Enregistrer",
            command=update_transaction,
            width=200,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="❌ Annuler",
            command=dialog.destroy,
            width=200,
            height=40,
            fg_color="gray",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=10)

    def _on_filter_change(self, start_date, end_date, transaction_type):
        """Appelé quand les filtres changent"""
        self.load_transactions(start_date, end_date, transaction_type)
        self._create_stats()  # Recalculer les stats avec les filtres

    def delete_transaction(self, transaction_id):
        """Supprime une transaction"""
        result = messagebox.askyesno(
            "Confirmer la suppression",
            "Êtes-vous sûr de vouloir supprimer cette transaction ?\nCette action est irréversible."
        )

        if result:
            try:
                self.portfolio.db.delete_transaction(transaction_id)
                # Recharger avec les filtres actuels
                start_date, end_date = self.filters.get_date_range()
                tx_type = self.filters.get_transaction_type()
                self.load_transactions(start_date, end_date, tx_type)
                self._create_stats()
                messagebox.showinfo("Succès", "✅ Transaction supprimée")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la suppression:\n{str(e)}")
