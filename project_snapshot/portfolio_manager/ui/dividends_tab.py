# -*- coding: utf-8 -*-
"""Onglet Dividendes - suivi des dividendes à venir et reçus."""

from __future__ import annotations

import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import customtkinter as ctk

from portfolio_manager.core.portfolio import Portfolio
from portfolio_manager.database.models import Dividend
from portfolio_manager.utils.formatters import format_currency, format_date
from portfolio_manager.config import CAC40_TICKERS, FLAT_TAX_RATE


class DividendsTab(ctk.CTkScrollableFrame):
    """Affichage et gestion des dividendes."""

    def __init__(self, parent, portfolio: Portfolio):
        super().__init__(parent)
        self.portfolio = portfolio

        self._is_loading = False
        self._last_message: Optional[str] = None
        self._received_all: List[Dividend] = []
        self._upcoming: List[Dividend] = []
        self._upcoming_summary: Dict[str, object] = {
            'totals': {'gross_total': 0.0, 'net_total': 0.0, 'count': 0},
            'per_ticker': []
        }

        self._init_widgets()
        self.after(100, self._setup_mousewheel)
        self.sync_and_load(force_sync=True)

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _init_widgets(self):
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(header, text="💵 Dividendes", font=ctk.CTkFont(size=28, weight="bold"))
        title.grid(row=0, column=0, sticky="w")

        self.sync_button = ctk.CTkButton(
            header,
            text="🔄 Synchroniser",
            command=lambda: self.sync_and_load(force_sync=True),
            width=170,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.sync_button.grid(row=0, column=1, padx=(10, 0))

        self.reload_button = ctk.CTkButton(
            header,
            text="⟳ Rafraîchir",
            command=lambda: self.sync_and_load(force_sync=False),
            width=150
        )
        self.reload_button.grid(row=0, column=2, padx=(10, 0))

        self.add_manual_button = ctk.CTkButton(
            header,
            text="➕ Ajouter dividende",
            command=self._open_manual_dividend_dialog,
            width=190
        )
        self.add_manual_button.grid(row=0, column=3, padx=(10, 0))

        self.status_label = ctk.CTkLabel(header, text="", text_color="#ef4444")
        self.status_label.grid(row=1, column=0, columnspan=4, sticky="w", pady=(8, 0))

        self.stats_frame = ctk.CTkFrame(self, corner_radius=10)
        self.stats_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.stats_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.upcoming_frame = ctk.CTkFrame(self, corner_radius=10)
        self.upcoming_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.upcoming_frame.grid_columnconfigure(0, weight=1)

        self.upcoming_title = ctk.CTkLabel(
            self.upcoming_frame,
            text="Dividendes à venir",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.upcoming_title.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

        self.upcoming_table = ctk.CTkFrame(self.upcoming_frame, fg_color="transparent")
        self.upcoming_table.grid(row=1, column=0, padx=10, pady=(0, 15), sticky="ew")

        self.summary_frame = ctk.CTkFrame(self, corner_radius=10)
        self.summary_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.summary_frame.grid_columnconfigure(0, weight=1)

        self.summary_title = ctk.CTkLabel(
            self.summary_frame,
            text="Totaux par entreprise",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.summary_title.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

        self.summary_table = ctk.CTkFrame(self.summary_frame, fg_color="transparent")
        self.summary_table.grid(row=1, column=0, padx=10, pady=(0, 15), sticky="ew")

        self.received_frame = ctk.CTkFrame(self, corner_radius=10)
        self.received_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        self.received_frame.grid_columnconfigure(0, weight=1)

        received_header = ctk.CTkFrame(self.received_frame, fg_color="transparent")
        received_header.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="ew")
        received_header.grid_columnconfigure(0, weight=1)

        self.received_title = ctk.CTkLabel(
            received_header,
            text="Historique des dividendes reçus",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.received_title.grid(row=0, column=0, sticky="w")

        self.received_year_var = ctk.StringVar(value="Tout")
        self.received_year_menu = ctk.CTkOptionMenu(
            received_header,
            values=["Tout"],
            variable=self.received_year_var,
            command=self._on_received_year_change,
            width=140
        )
        self.received_year_menu.grid(row=0, column=1, padx=(10, 0))

        self.received_table = ctk.CTkFrame(self.received_frame, fg_color="transparent")
        self.received_table.grid(row=1, column=0, padx=10, pady=(0, 15), sticky="ew")

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def sync_and_load(self, force_sync: bool = False):
        if self._is_loading:
            return

        self._set_loading(True)
        self._show_loading()

        def worker():
            error_message: Optional[str] = None

            if force_sync:
                try:
                    self.portfolio.sync_all_dividends()
                except Exception as exc:  # noqa: BLE001
                    error_message = f"Synchronisation incomplète ({exc})"

            try:
                upcoming = self.portfolio.get_upcoming_dividends(days_ahead=365)
                summary = self.portfolio.get_upcoming_dividends_summary(days_ahead=365)
                received_all = self.portfolio.dividends_api.get_received_dividends()
            except Exception as exc:  # noqa: BLE001
                error_message = f"Impossible de charger les dividendes ({exc})"
                upcoming = []
                summary = {
                    'totals': {'gross_total': 0.0, 'net_total': 0.0, 'count': 0},
                    'per_ticker': []
                }
                received_all = []

            self.after(0, lambda: self._render(upcoming, summary, received_all, error_message))

        threading.Thread(target=worker, daemon=True).start()

    def _render(
        self,
        upcoming: List[Dividend],
        summary: Dict[str, object],
        received_all: List[Dividend],
        error: Optional[str]
    ):
        self._set_loading(False)
        message = f"⚠️ {error}" if error else (self._last_message or "")
        self.status_label.configure(text=message)
        self._last_message = None

        self._upcoming = upcoming
        self._upcoming_summary = summary
        self._received_all = received_all

        self._update_received_year_options(received_all)
        filtered_received = self._filter_received_by_year(received_all)

        self._update_stats(upcoming, summary, filtered_received)
        self._populate_upcoming(upcoming)
        self._populate_summary(summary)
        self._populate_received(filtered_received)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _show_loading(self):
        for frame in (self.upcoming_table, self.summary_table, self.received_table):
            for widget in frame.winfo_children():
                widget.destroy()

        loading = ctk.CTkLabel(
            self.upcoming_table,
            text="⏳ Chargement des dividendes...",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        loading.pack(pady=40)

    def _set_loading(self, is_loading: bool):
        self._is_loading = is_loading
        state = "disabled" if is_loading else "normal"
        self.sync_button.configure(state=state)
        self.reload_button.configure(state=state)
        self.add_manual_button.configure(state=state)

    def _setup_mousewheel(self):
        canvas = getattr(self, "_parent_canvas", None)
        if not canvas:
            self.after(100, self._setup_mousewheel)
            return

        if getattr(self, "_mousewheel_bound", False):
            return

        canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        canvas.bind_all("<Button-4>", self._on_mousewheel)
        canvas.bind_all("<Button-5>", self._on_mousewheel)
        self._mousewheel_bound = True

    def _on_mousewheel(self, event):
        canvas = getattr(self, "_parent_canvas", None)
        if not canvas:
            return

        if event.num == 4:
            delta = -1
        elif event.num == 5:
            delta = 1
        else:
            if event.delta > 0:
                delta = -1
            elif event.delta < 0:
                delta = 1
            else:
                delta = 0

        if delta:
            canvas.yview_scroll(delta, "units")

    def _update_stats(
        self,
        upcoming: List[Dividend],
        summary: Dict[str, object],
        received: List[Dividend]
    ):
        for widget in self.stats_frame.winfo_children():
            widget.destroy()

        totals = summary.get('totals', {})
        gross_total = totals.get('gross_total', 0.0)
        net_total = totals.get('net_total', 0.0)
        count = totals.get('count', 0)

        next_dates = [div.ex_dividend_date for div in upcoming if div.ex_dividend_date]
        next_date_text = format_date(min(next_dates)) if next_dates else "-"

        received_net = sum(div.net_amount for div in received)
        received_label = "Net reçu"
        if self.received_year_var.get() != "Tout":
            received_label = f"Net reçu {self.received_year_var.get()}"

        cards = [
            ("Brut à venir", format_currency(gross_total), "#10b981" if gross_total >= 0 else None),
            ("Net à venir", format_currency(net_total), "#10b981" if net_total >= 0 else None),
            ("Événements", str(count), None),
            ("Prochaine date ex", next_date_text, None),
            (received_label, format_currency(received_net), "#10b981" if received_net >= 0 else None),
        ]

        for idx, (label, value, color) in enumerate(cards):
            card = ctk.CTkFrame(self.stats_frame, corner_radius=10)
            card.grid(row=0, column=idx, padx=10, pady=10, sticky="nsew")

            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=12), text_color="gray").pack(pady=(15, 5))
            ctk.CTkLabel(
                card,
                text=value,
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=color
            ).pack(pady=(0, 15))

    def _populate_upcoming(self, dividends: List[Dividend]):
        for widget in self.upcoming_table.winfo_children():
            widget.destroy()

        if not dividends:
            ctk.CTkLabel(
                self.upcoming_table,
                text="Aucun dividende prévu pour le moment.",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            ).pack(pady=40)
            return

        headers = [
            ("Ex-date", 100),
            ("Paiement", 100),
            ("Ticker", 90),
            ("Entreprise", 220),
            ("Montant/Action", 130),
            ("Quantité", 90),
            ("Brut", 120),
            ("Net", 120),
        ]

        header_frame = ctk.CTkFrame(self.upcoming_table, fg_color="transparent")
        header_frame.pack(fill="x", padx=5, pady=(5, 10))

        for idx, (text, width) in enumerate(headers):
            ctk.CTkLabel(
                header_frame,
                text=text,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=width
            ).grid(row=0, column=idx, padx=5, pady=5)

        ctk.CTkLabel(
            header_frame,
            text="Actions",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=150
        ).grid(row=0, column=len(headers), padx=5, pady=5)

        for div in dividends:
            row = ctk.CTkFrame(self.upcoming_table)
            row.pack(fill="x", padx=5, pady=2)

            values = [
                format_date(div.ex_dividend_date),
                format_date(div.payment_date),
                div.ticker,
                div.company_name[:28] + '...' if len(div.company_name) > 28 else div.company_name,
                format_currency(div.amount_per_share),
                f"{div.quantity_owned:.2f}",
                format_currency(div.gross_amount),
                format_currency(div.net_amount),
            ]

            for idx, (value, (_, width)) in enumerate(zip(values, headers)):
                ctk.CTkLabel(row, text=value, width=width).grid(row=0, column=idx, padx=5, pady=6)

            actions_frame = ctk.CTkFrame(row, fg_color="transparent")
            actions_frame.grid(row=0, column=len(headers), padx=5, pady=4)

            mark_btn = ctk.CTkButton(
                actions_frame,
                text="Marquer reçu",
                width=120,
                command=lambda d=div: self._open_received_dialog(d)
            )
            mark_btn.pack(side="left")

    def _populate_summary(self, summary: Dict[str, object]):
        for widget in self.summary_table.winfo_children():
            widget.destroy()

        per_ticker = summary.get('per_ticker', [])
        if not per_ticker:
            ctk.CTkLabel(
                self.summary_table,
                text="Aucun total disponible.",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            ).pack(pady=30)
            return

        headers = [
            ("Ticker", 90),
            ("Entreprise", 220),
            ("Prochaine ex-date", 140),
            ("Paiement", 120),
            ("Montant/Action", 130),
            ("Quantité", 90),
            ("Total brut", 130),
            ("Total net", 130),
        ]

        header_frame = ctk.CTkFrame(self.summary_table, fg_color="transparent")
        header_frame.pack(fill="x", padx=5, pady=(5, 10))

        for idx, (text, width) in enumerate(headers):
            ctk.CTkLabel(
                header_frame,
                text=text,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=width
            ).grid(row=0, column=idx, padx=5, pady=5)

        for info in per_ticker:
            row = ctk.CTkFrame(self.summary_table)
            row.pack(fill="x", padx=5, pady=2)

            values = [
                info['ticker'],
                info['company_name'][:28] + '...' if len(info['company_name']) > 28 else info['company_name'],
                format_date(info.get('next_ex_date')),
                format_date(info.get('next_payment_date')),
                format_currency(info.get('amount_per_share', 0.0)),
                f"{info.get('quantity_owned', 0.0):.2f}",
                format_currency(info.get('gross_total', 0.0)),
                format_currency(info.get('net_total', 0.0)),
            ]

            for idx, (value, (_, width)) in enumerate(zip(values, headers)):
                ctk.CTkLabel(row, text=value, width=width).grid(row=0, column=idx, padx=5, pady=6)

    def _update_received_year_options(self, dividends: List[Dividend]):
        years = sorted({
            (self._parse_date_str(d.received_date)
             or self._parse_date_str(d.payment_date)
             or self._parse_date_str(d.ex_dividend_date)).year
            for d in dividends
            if self._parse_date_str(d.received_date)
            or self._parse_date_str(d.payment_date)
            or self._parse_date_str(d.ex_dividend_date)
        }, reverse=True)

        options = ["Tout"] + [str(year) for year in years]
        current = self.received_year_var.get()

        self.received_year_menu.configure(values=options)
        if current not in options:
            self.received_year_var.set("Tout")

    def _filter_received_by_year(self, dividends: List[Dividend]) -> List[Dividend]:
        selection = self.received_year_var.get()
        if selection == "Tout":
            return dividends

        try:
            year = int(selection)
        except ValueError:
            return dividends

        filtered: List[Dividend] = []
        for div in dividends:
            date = self._parse_date_str(div.received_date) or \
                self._parse_date_str(div.payment_date) or \
                self._parse_date_str(div.ex_dividend_date)
            if date and date.year == year:
                filtered.append(div)
        return filtered

    def _on_received_year_change(self, _value: str):
        filtered = self._filter_received_by_year(self._received_all)
        self._populate_received(filtered)
        self._update_stats(self._upcoming, self._upcoming_summary, filtered)

    def _populate_received(self, dividends: List[Dividend]):
        for widget in self.received_table.winfo_children():
            widget.destroy()

        if not dividends:
            ctk.CTkLabel(
                self.received_table,
                text="Aucun dividende reçu pour la période sélectionnée.",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            ).pack(pady=30)
            return

        headers = [
            ("Réception", 120),
            ("Paiement", 120),
            ("Ticker", 80),
            ("Entreprise", 220),
            ("Brut", 120),
            ("Net", 120),
        ]

        header_frame = ctk.CTkFrame(self.received_table, fg_color="transparent")
        header_frame.pack(fill="x", padx=5, pady=(5, 10))

        for idx, (text, width) in enumerate(headers):
            ctk.CTkLabel(
                header_frame,
                text=text,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=width
            ).grid(row=0, column=idx, padx=5, pady=5)

        ctk.CTkLabel(
            header_frame,
            text="Actions",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=190
        ).grid(row=0, column=len(headers), padx=5, pady=5)

        for div in dividends:
            row = ctk.CTkFrame(self.received_table)
            row.pack(fill="x", padx=5, pady=2)

            values = [
                format_date(div.received_date) or format_date(div.payment_date),
                format_date(div.payment_date),
                div.ticker,
                div.company_name[:28] + '...' if len(div.company_name) > 28 else div.company_name,
                format_currency(div.gross_amount),
                format_currency(div.net_amount),
            ]

            for idx, (value, (_, width)) in enumerate(zip(values, headers)):
                ctk.CTkLabel(row, text=value, width=width).grid(row=0, column=idx, padx=5, pady=6)

            actions = ctk.CTkFrame(row, fg_color="transparent")
            actions.grid(row=0, column=len(headers), padx=5, pady=4)

            edit_btn = ctk.CTkButton(
                actions,
                text="Modifier",
                width=90,
                command=lambda d=div: self._open_received_dialog(d, edit_mode=True)
            )
            edit_btn.pack(side="left", padx=4)

            revert_btn = ctk.CTkButton(
                actions,
                text="Replanifier",
                width=90,
                command=lambda d=div: self._revert_dividend(d)
            )
            revert_btn.pack(side="left", padx=4)

    def _open_received_dialog(self, dividend: Dividend, edit_mode: bool = False):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Dividende reçu" if edit_mode else "Marquer comme reçu")
        dialog.geometry("460x360")
        dialog.minsize(460, 360)
        dialog.resizable(False, False)
        dialog.grab_set()

        content = ctk.CTkFrame(dialog, corner_radius=10)
        content.pack(fill="both", expand=True, padx=20, pady=20)
        content.grid_columnconfigure(0, weight=1)

        info_text = (
            f"{dividend.ticker} – {dividend.company_name}\n"
            f"Ex-date: {format_date(dividend.ex_dividend_date)}\n"
            f"Paiement prévu: {format_date(dividend.payment_date)}\n"
            f"Quantité: {dividend.quantity_owned:.2f}"
        )
        ctk.CTkLabel(content, text=info_text, justify="left", anchor="w").grid(row=0, column=0, sticky="ew", pady=(10, 8))

        ctk.CTkLabel(content, text="Montant net reçu (€):", anchor="w").grid(row=1, column=0, sticky="ew", pady=(4, 2))
        net_var = ctk.StringVar(value=f"{dividend.net_amount:.2f}")
        net_entry = ctk.CTkEntry(content, textvariable=net_var)
        net_entry.grid(row=2, column=0, sticky="ew", pady=(0, 6))

        ctk.CTkLabel(content, text="Date de réception (YYYY-MM-DD):", anchor="w").grid(row=3, column=0, sticky="ew", pady=(4, 2))
        default_date = dividend.received_date or dividend.payment_date or datetime.now().strftime("%Y-%m-%d")
        date_var = ctk.StringVar(value=default_date or "")
        date_entry = ctk.CTkEntry(content, textvariable=date_var)
        date_entry.grid(row=4, column=0, sticky="ew", pady=(0, 6))

        feedback = ctk.CTkLabel(content, text="", text_color="#ef4444", anchor="w")
        feedback.grid(row=5, column=0, sticky="ew", pady=(6, 4))
        content.grid_rowconfigure(6, weight=1)

        def on_confirm():
            try:
                net_value = self._parse_amount_input(net_var.get())
            except ValueError:
                feedback.configure(text="Montant net invalide")
                return

            date_str = date_var.get().strip()
            if date_str:
                parsed_date = self._parse_date_str(date_str)
                if not parsed_date:
                    feedback.configure(text="Date invalide (format YYYY-MM-DD)")
                    return
                date_str = parsed_date.strftime("%Y-%m-%d")
            else:
                date_str = datetime.now().strftime("%Y-%m-%d")

            try:
                ok = self.portfolio.dividends_api.mark_dividend_as_received(
                    dividend.id,
                    received_date=date_str,
                    actual_net_amount=net_value
                )
                if ok:
                    self._last_message = "Dividende enregistré"
                    dialog.destroy()
                    self.sync_and_load(force_sync=False)
                else:
                    feedback.configure(text="Mise à jour impossible")
            except Exception as exc:  # noqa: BLE001
                feedback.configure(text=str(exc))

        def on_cancel():
            dialog.destroy()

        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.grid(row=7, column=0, pady=(10, 0))
        ctk.CTkButton(btn_frame, text="Valider", width=140, command=on_confirm).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="Annuler", width=140, command=on_cancel, fg_color="gray").pack(side="left", padx=8)

    def _revert_dividend(self, dividend: Dividend):
        try:
            ok = self.portfolio.dividends_api.mark_dividend_as_planned(dividend.id)
            if ok:
                self._last_message = "Dividende replanifié"
                self.sync_and_load(force_sync=False)
            else:
                self.status_label.configure(text="⚠️ Impossible de replanifier ce dividende")
        except Exception as exc:  # noqa: BLE001
            self.status_label.configure(text=f"⚠️ {exc}")

    # ------------------------------------------------------------------
    # Ajout manuel
    # ------------------------------------------------------------------

    def _open_manual_dividend_dialog(self):
        transactions = self.portfolio.get_all_transactions()
        available_tickers = sorted({tx.ticker for tx in transactions}) or sorted(CAC40_TICKERS.keys())

        dialog = ctk.CTkToplevel(self)
        dialog.title("Ajouter un dividende")
        dialog.geometry("540x640")
        dialog.minsize(540, 640)
        dialog.resizable(False, False)
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        frame.grid_columnconfigure(1, weight=1)

        year_options = [str(datetime.now().year - i) for i in range(0, 6)]
        schedule_cache: List[Dict[str, object]] = []

        row = 0
        ctk.CTkLabel(frame, text="Ticker:").grid(row=row, column=0, sticky="w", padx=(12, 6), pady=6)
        ticker_var = ctk.StringVar(value=available_tickers[0] if available_tickers else "")
        ticker_menu = ctk.CTkOptionMenu(frame, values=available_tickers, variable=ticker_var, width=180)
        ticker_menu.grid(row=row, column=1, sticky="ew", padx=(0, 12), pady=6)

        row += 1
        ctk.CTkLabel(frame, text="Année").grid(row=row, column=0, sticky="w", padx=(12, 6), pady=6)
        year_var = ctk.StringVar(value=year_options[0])
        year_menu = ctk.CTkOptionMenu(frame, values=year_options, variable=year_var, width=120)
        year_menu.grid(row=row, column=1, sticky="w", padx=(0, 12), pady=6)

        row += 1
        ctk.CTkLabel(frame, text="Échéance (fallback)").grid(row=row, column=0, sticky="w", padx=(12, 6), pady=6)
        event_var = ctk.StringVar(value="Manuelle")
        event_menu = ctk.CTkOptionMenu(frame, values=["Manuelle"], variable=event_var, width=300)
        event_menu.grid(row=row, column=1, columnspan=2, sticky="ew", padx=(0, 12), pady=6)

        row += 1
        ctk.CTkLabel(frame, text="Entreprise:").grid(row=row, column=0, sticky="w", padx=(12, 6), pady=6)
        company_var = ctk.StringVar(value=self._guess_company_name(ticker_var.get()))
        company_entry = ctk.CTkEntry(frame, textvariable=company_var)
        company_entry.grid(row=row, column=1, columnspan=2, sticky="ew", padx=(0, 12), pady=6)

        row += 1
        ctk.CTkLabel(frame, text="Ex-date (YYYY-MM-DD):").grid(row=row, column=0, sticky="w", padx=(12, 6), pady=6)
        ex_var = ctk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ex_entry = ctk.CTkEntry(frame, textvariable=ex_var)
        ex_entry.grid(row=row, column=1, columnspan=2, sticky="ew", padx=(0, 12), pady=6)

        row += 1
        ctk.CTkLabel(frame, text="Date paiement (YYYY-MM-DD):").grid(row=row, column=0, sticky="w", padx=(12, 6), pady=6)
        payment_var = ctk.StringVar(value=(datetime.now() + timedelta(days=20)).strftime("%Y-%m-%d"))
        payment_entry = ctk.CTkEntry(frame, textvariable=payment_var)
        payment_entry.grid(row=row, column=1, columnspan=2, sticky="ew", padx=(0, 12), pady=6)

        row += 1
        ctk.CTkLabel(frame, text="Montant par action (€):").grid(row=row, column=0, sticky="w", padx=(12, 6), pady=6)
        amount_var = ctk.StringVar(value="1.00")
        amount_entry = ctk.CTkEntry(frame, textvariable=amount_var)
        amount_entry.grid(row=row, column=1, sticky="ew", padx=(0, 12), pady=6)

        row += 1
        ctk.CTkLabel(frame, text="Quantité détenue:").grid(row=row, column=0, sticky="w", padx=(12, 6), pady=6)
        quantity_var = ctk.StringVar(value="0")
        quantity_entry = ctk.CTkEntry(frame, textvariable=quantity_var)
        quantity_entry.grid(row=row, column=1, sticky="ew", padx=(0, 12), pady=6)

        def estimate_quantity():
            ticker = ticker_var.get().strip()
            ex_date = ex_var.get().strip()
            qty = self.portfolio.dividends_api.get_quantity_on_date(ticker, ex_date)
            quantity_var.set(f"{qty:.2f}")
            update_totals()

        estimate_btn = ctk.CTkButton(frame, text="Estimer", width=100, command=estimate_quantity)
        estimate_btn.grid(row=row, column=2, padx=(0, 12), pady=6)

        row += 1
        gross_preview = ctk.CTkLabel(frame, text="Brut estimé : 0,00€", anchor="w")
        gross_preview.grid(row=row, column=0, columnspan=2, sticky="w", padx=(12, 6), pady=4)
        net_preview = ctk.CTkLabel(frame, text="Net estimé : 0,00€", anchor="w")
        net_preview.grid(row=row, column=1, columnspan=2, sticky="e", padx=(0, 12), pady=4)

        row += 1
        ctk.CTkLabel(frame, text="Statut:").grid(row=row, column=0, sticky="w", padx=(12, 6), pady=6)
        status_var = ctk.StringVar(value="REÇU")
        status_menu = ctk.CTkOptionMenu(frame, values=["REÇU", "PRÉVU"], variable=status_var, width=120)
        status_menu.grid(row=row, column=1, sticky="w", padx=(0, 12), pady=6)

        row += 1
        ctk.CTkLabel(frame, text="Montant net (€):").grid(row=row, column=0, sticky="w", padx=(12, 6), pady=6)
        net_var = ctk.StringVar(value="")
        net_entry = ctk.CTkEntry(frame, textvariable=net_var)
        net_entry.grid(row=row, column=1, sticky="ew", padx=(0, 12), pady=6)

        row += 1
        ctk.CTkLabel(frame, text="Date réception (YYYY-MM-DD):").grid(row=row, column=0, sticky="w", padx=(12, 6), pady=6)
        received_var = ctk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        received_entry = ctk.CTkEntry(frame, textvariable=received_var)
        received_entry.grid(row=row, column=1, sticky="ew", padx=(0, 12), pady=6)

        row += 1
        ctk.CTkLabel(frame, text="Notes (optionnel):").grid(row=row, column=0, sticky="w", padx=(12, 6), pady=6)
        notes_var = ctk.StringVar(value="")
        notes_entry = ctk.CTkEntry(frame, textvariable=notes_var)
        notes_entry.grid(row=row, column=1, columnspan=2, sticky="ew", padx=(0, 12), pady=6)

        row += 1
        feedback = ctk.CTkLabel(frame, text="", text_color="#ef4444")
        feedback.grid(row=row, column=0, columnspan=3, sticky="w", padx=(12, 12), pady=(6, 6))

        def refresh_schedule(*_):
            schedule_cache.clear()
            ticker = ticker_var.get().strip()
            try:
                year = int(year_var.get())
            except ValueError:
                year = datetime.now().year

            company_var.set(self._guess_company_name(ticker))

            schedule = self.portfolio.dividends_api.get_fallback_schedule(ticker, year)
            if schedule:
                event_values = ["Manuelle"]
                for item in schedule:
                    label = (
                        f"{item['ex_dividend_date']} → {item['payment_date']} "
                        f"({item['amount_per_share']:.2f}€)"
                    )
                    event_values.append(label)
                schedule_cache.extend(schedule)
                event_menu.configure(values=event_values)
                event_var.set(event_values[1])
                apply_schedule(0)
            else:
                event_menu.configure(values=["Manuelle"])
                event_var.set("Manuelle")

        def apply_schedule(index: int):
            if index >= len(schedule_cache):
                return
            item = schedule_cache[index]
            ex_var.set(item['ex_dividend_date'])
            payment_var.set(item['payment_date'])
            amount_var.set(f"{item['amount_per_share']:.2f}")
            update_totals()

        def on_event_change(choice: str):
            if choice == "Manuelle":
                return
            try:
                idx = event_menu.cget("values").index(choice) - 1
            except ValueError:
                return
            if idx >= 0:
                apply_schedule(idx)

        def toggle_received_fields(*_):
            is_received = status_var.get() == "REÇU"
            net_entry.configure(state="normal" if is_received else "disabled")
            received_entry.configure(state="normal" if is_received else "disabled")
            if is_received and not net_var.get().strip():
                update_totals()

        def update_totals(*_):
            try:
                amount = self._parse_amount_input(amount_var.get())
                quantity = self._parse_amount_input(quantity_var.get())
            except ValueError:
                gross = net = 0.0
            else:
                gross = amount * quantity
                net = gross * (1 - FLAT_TAX_RATE)

            gross_preview.configure(text=f"Brut estimé : {format_currency(gross)}")
            net_preview.configure(text=f"Net estimé : {format_currency(net)}")

            if status_var.get() == "REÇU" and net > 0 and not net_var.get().strip():
                net_var.set(f"{net:.2f}")

        def on_submit():
            ticker = ticker_var.get().strip()
            company = company_var.get().strip() or self._guess_company_name(ticker)
            ex_date = ex_var.get().strip()
            payment_date = payment_var.get().strip() or None
            status = status_var.get()

            if not ticker or not ex_date:
                feedback.configure(text="Ticker et ex-date sont requis")
                return

            try:
                amount = self._parse_amount_input(amount_var.get())
                quantity = self._parse_amount_input(quantity_var.get())
            except ValueError:
                feedback.configure(text="Montant/quantité invalides")
                return

            if quantity <= 0:
                feedback.configure(text="Quantité doit être positive")
                return

            try:
                net_override = None
                received_date = None
                if status == "REÇU":
                    net_value = net_var.get().strip()
                    if net_value:
                        net_override = self._parse_amount_input(net_value)
                    received_date = received_var.get().strip() or None

                self.portfolio.dividends_api.add_manual_dividend(
                    ticker=ticker,
                    company_name=company,
                    amount_per_share=amount,
                    ex_dividend_date=ex_date,
                    payment_date=payment_date,
                    quantity_owned=quantity,
                    status=status,
                    received_date=received_date,
                    net_amount_override=net_override,
                    notes=notes_var.get().strip() or None
                )

                self._last_message = "Dividende ajouté"
                dialog.destroy()
                self.sync_and_load(force_sync=False)
            except Exception as exc:  # noqa: BLE001
                feedback.configure(text=str(exc))

        def on_cancel():
            dialog.destroy()

        ticker_var.trace_add("write", refresh_schedule)
        year_var.trace_add("write", refresh_schedule)
        event_var.trace_add("write", lambda *_: on_event_change(event_var.get()))
        amount_var.trace_add("write", update_totals)
        quantity_var.trace_add("write", update_totals)
        status_var.trace_add("write", toggle_received_fields)

        toggle_received_fields()
        update_totals()
        refresh_schedule()

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=row, column=0, columnspan=3, pady=(12, 0))
        ctk.CTkButton(btn_frame, text="Ajouter", width=140, command=on_submit).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="Annuler", width=140, command=on_cancel, fg_color="gray").pack(side="left", padx=8)

    @staticmethod
    def _parse_amount_input(value: str) -> float:
        cleaned = value.replace('€', '').replace(' ', '').replace(',', '.').strip()
        return float(cleaned)

    @staticmethod
    def _parse_date_str(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _guess_company_name(ticker: str) -> str:
        return CAC40_TICKERS.get(ticker, ticker)
