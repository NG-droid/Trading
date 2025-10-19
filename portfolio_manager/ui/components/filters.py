# -*- coding: utf-8 -*-
"""
Composant réutilisable de filtres pour les transactions, ventes et dividendes
"""

import customtkinter as ctk
from datetime import datetime, timedelta
from typing import Callable, Optional, List


class PeriodFilter(ctk.CTkFrame):
    """Composant de filtres par période avec menu déroulant et sélecteurs de dates"""

    def __init__(
        self,
        parent,
        on_filter_change: Callable,
        show_transaction_type: bool = True,
        transaction_types: Optional[List[str]] = None
    ):
        """
        Args:
            parent: Widget parent
            on_filter_change: Callback appelé quand les filtres changent
            show_transaction_type: Afficher le filtre par type de transaction
            transaction_types: Liste des types de transaction (ex: ["Tout", "ACHAT", "VENTE"])
        """
        super().__init__(parent, corner_radius=10)

        self.on_filter_change = on_filter_change
        self.show_transaction_type = show_transaction_type

        # Configuration du grid
        self.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=0)
        self.grid_columnconfigure(6, weight=1)

        # Variables
        self.period_var = ctk.StringVar(value="Tout")
        self.type_var = ctk.StringVar(value="Tout")

        # Créer les widgets
        self._create_widgets(transaction_types or ["Tout", "ACHAT", "VENTE"])

    def _create_widgets(self, transaction_types):
        """Crée les widgets de filtrage"""
        row = 0
        col = 0

        # Label titre
        title_label = ctk.CTkLabel(
            self,
            text="🔍 Filtres",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=row, column=col, padx=10, pady=10, sticky="w")
        col += 1

        # Menu déroulant Période
        ctk.CTkLabel(self, text="Période:").grid(row=row, column=col, padx=(20, 5), pady=10)
        col += 1

        periods = [
            "Tout",
            "2025",
            "2024",
            "2023",
            "Ce mois",
            "Mois dernier",
            "3 derniers mois",
            "6 derniers mois",
            "Cette année",
            "Année dernière",
            "Période personnalisée"
        ]

        self.period_menu = ctk.CTkOptionMenu(
            self,
            values=periods,
            variable=self.period_var,
            command=self._on_period_change,
            width=180
        )
        self.period_menu.grid(row=row, column=col, padx=5, pady=10)
        col += 1

        # Filtre par type de transaction (si activé)
        if self.show_transaction_type:
            ctk.CTkLabel(self, text="Type:").grid(row=row, column=col, padx=(20, 5), pady=10)
            col += 1

            self.type_menu = ctk.CTkOptionMenu(
                self,
                values=transaction_types,
                variable=self.type_var,
                command=self._on_filter_apply,
                width=120
            )
            self.type_menu.grid(row=row, column=col, padx=5, pady=10)
            col += 1

        # Frame pour les dates personnalisées (masqué par défaut)
        self.custom_dates_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.custom_dates_frame.grid(row=row, column=col, padx=20, pady=10, sticky="w")
        self.custom_dates_frame.grid_remove()  # Masqué au départ

        # Date début (Entry simple)
        ctk.CTkLabel(self.custom_dates_frame, text="Du:").grid(row=0, column=0, padx=5)
        self.start_date_entry = ctk.CTkEntry(
            self.custom_dates_frame,
            width=100,
            placeholder_text="JJ/MM/AAAA"
        )
        self.start_date_entry.grid(row=0, column=1, padx=5)
        # Initialiser avec une date par défaut
        default_start = (datetime.now() - timedelta(days=30)).strftime("%d/%m/%Y")
        self.start_date_entry.insert(0, default_start)

        # Date fin (Entry simple)
        ctk.CTkLabel(self.custom_dates_frame, text="Au:").grid(row=0, column=2, padx=5)
        self.end_date_entry = ctk.CTkEntry(
            self.custom_dates_frame,
            width=100,
            placeholder_text="JJ/MM/AAAA"
        )
        self.end_date_entry.grid(row=0, column=3, padx=5)
        # Initialiser avec aujourd'hui
        self.end_date_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))

        # Bouton Appliquer
        col += 1
        self.apply_btn = ctk.CTkButton(
            self,
            text="📊 Appliquer",
            command=self._on_filter_apply,
            width=120,
            font=ctk.CTkFont(weight="bold")
        )
        self.apply_btn.grid(row=row, column=col, padx=10, pady=10)

    def _on_period_change(self, selected_period):
        """Appelé quand la période change"""
        if selected_period == "Période personnalisée":
            self.custom_dates_frame.grid()  # Afficher les sélecteurs de dates
        else:
            self.custom_dates_frame.grid_remove()  # Masquer les sélecteurs de dates
            self._on_filter_apply()

    def _on_filter_apply(self, *args):
        """Applique les filtres et appelle le callback"""
        start_date, end_date = self.get_date_range()
        transaction_type = self.get_transaction_type() if self.show_transaction_type else None

        self.on_filter_change(start_date, end_date, transaction_type)

    def get_date_range(self) -> tuple:
        """
        Retourne le tuple (start_date, end_date) selon la période sélectionnée

        Returns:
            (str, str): Dates au format YYYY-MM-DD ou (None, None) pour tout
        """
        period = self.period_var.get()
        today = datetime.now()

        if period == "Tout":
            return None, None

        elif period == "2025":
            return "2025-01-01", "2025-12-31"

        elif period == "2024":
            return "2024-01-01", "2024-12-31"

        elif period == "2023":
            return "2023-01-01", "2023-12-31"

        elif period == "Ce mois":
            start = today.replace(day=1)
            # Dernier jour du mois
            if today.month == 12:
                end = today.replace(day=31)
            else:
                end = (today.replace(month=today.month + 1, day=1) - timedelta(days=1))
            return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

        elif period == "Mois dernier":
            # Premier jour du mois dernier
            first_current_month = today.replace(day=1)
            last_month = first_current_month - timedelta(days=1)
            start = last_month.replace(day=1)
            end = last_month
            return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

        elif period == "3 derniers mois":
            start = today - timedelta(days=90)
            return start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")

        elif period == "6 derniers mois":
            start = today - timedelta(days=180)
            return start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")

        elif period == "Cette année":
            start = today.replace(month=1, day=1)
            return start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")

        elif period == "Année dernière":
            year = today.year - 1
            return f"{year}-01-01", f"{year}-12-31"

        elif period == "Période personnalisée":
            # Récupérer les dates des Entry (format JJ/MM/AAAA)
            try:
                start_str = self.start_date_entry.get()
                end_str = self.end_date_entry.get()

                # Parser les dates au format JJ/MM/AAAA
                start = datetime.strptime(start_str, "%d/%m/%Y")
                end = datetime.strptime(end_str, "%d/%m/%Y")

                return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
            except ValueError:
                # Si erreur de format, retourner tout
                print(f"Erreur format date: {start_str} ou {end_str}")
                return None, None

        return None, None

    def get_transaction_type(self) -> Optional[str]:
        """Retourne le type de transaction sélectionné"""
        if not self.show_transaction_type:
            return None

        tx_type = self.type_var.get()
        return None if tx_type == "Tout" else tx_type
