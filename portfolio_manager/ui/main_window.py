# -*- coding: utf-8 -*-
"""
Fenêtre principale de l'application Portfolio Manager
"""

import customtkinter as ctk
from typing import Optional
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from portfolio_manager.core.portfolio import Portfolio
from portfolio_manager.config import (
    WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT,
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_SUCCESS, COLOR_DANGER
)


class PortfolioApp(ctk.CTk):
    """
    Application principale Portfolio Manager
    """

    def __init__(self, db_path: str = None):
        super().__init__()

        print("=== Initialisation de l'application ===")

        try:
            # Configuration de la fenêtre
            print("Configuration de la fenêtre...")
            self.title(WINDOW_TITLE)
            self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

            # Taille minimale pour éviter une interface cassée
            from portfolio_manager.config import WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT
            self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

            # Rendre la fenêtre responsive (plein écran optionnel)
            # Sur Mac: permettre le plein écran natif
            try:
                self.state('zoomed')  # Windows
            except:
                pass  # Mac/Linux gérera via le bouton natif

            # Initialiser le portfolio
            print("Initialisation du portfolio...")
            self.portfolio = Portfolio(db_path)

            # Thème
            print("Configuration du thème...")
            ctk.set_appearance_mode("dark")  # dark, light, system
            ctk.set_default_color_theme("blue")  # blue, green, dark-blue

            # Variables
            self.current_tab = None

            # Créer l'interface
            print("Création du layout...")
            self._create_layout()

            print("Création de la sidebar...")
            self._create_sidebar()

            print("Création du contenu principal...")
            self._create_main_content()

            # Charger le dashboard par défaut
            print("Chargement du Dashboard...")
            self.show_dashboard()

            # Rafraîchir automatiquement les données si nécessaire
            self.after(500, self._auto_refresh_if_needed)

            print("=== Application initialisée avec succès ===")

        except Exception as e:
            print(f"ERREUR lors de l'initialisation: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _create_layout(self):
        """Crée la structure principale (grid)"""
        # Configuration du grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def _create_sidebar(self):
        """Crée la barre latérale de navigation"""
        # Frame sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        # Logo / Titre
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="📊 Portfolio\nManager",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        # Boutons de navigation
        self.btn_dashboard = ctk.CTkButton(
            self.sidebar,
            text="📈 Dashboard",
            command=self.show_dashboard,
            width=160
        )
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10)

        self.btn_portfolio = ctk.CTkButton(
            self.sidebar,
            text="💼 Portfolio",
            command=self.show_portfolio,
            width=160
        )
        self.btn_portfolio.grid(row=2, column=0, padx=20, pady=10)

        self.btn_transactions = ctk.CTkButton(
            self.sidebar,
            text="📝 Transactions",
            command=self.show_transactions,
            width=160
        )
        self.btn_transactions.grid(row=3, column=0, padx=20, pady=10)

        self.btn_dividends = ctk.CTkButton(
            self.sidebar,
            text="💵 Dividendes",
            command=self.show_dividends,
            width=160
        )
        self.btn_dividends.grid(row=4, column=0, padx=20, pady=10)

        self.btn_sales = ctk.CTkButton(
            self.sidebar,
            text="💸 Historique Ventes",
            command=self.show_sales_history,
            width=160
        )
        self.btn_sales.grid(row=5, column=0, padx=20, pady=10)

        self.btn_tax = ctk.CTkButton(
            self.sidebar,
            text="📊 Fiscalité",
            command=self.show_tax,
            width=160
        )
        self.btn_tax.grid(row=6, column=0, padx=20, pady=10)

        # Séparateur
        self.separator = ctk.CTkFrame(self.sidebar, height=2)
        self.separator.grid(row=7, column=0, padx=20, pady=20, sticky="ew")

        # Options
        self.btn_refresh = ctk.CTkButton(
            self.sidebar,
            text="🔄 Rafraîchir",
            command=self.refresh_data,
            width=160,
            fg_color="transparent",
            border_width=2
        )
        self.btn_refresh.grid(row=8, column=0, padx=20, pady=10)

        self.btn_export = ctk.CTkButton(
            self.sidebar,
            text="📤 Export Excel",
            command=self.export_excel,
            width=160,
            fg_color="transparent",
            border_width=2
        )
        self.btn_export.grid(row=9, column=0, padx=20, pady=10)

        # Mode d'apparence (en bas)
        self.appearance_label = ctk.CTkLabel(
            self.sidebar,
            text="Thème:",
            anchor="w"
        )
        self.appearance_label.grid(row=11, column=0, padx=20, pady=(10, 0))

        self.appearance_mode = ctk.CTkOptionMenu(
            self.sidebar,
            values=["Dark", "Light", "System"],
            command=self.change_appearance_mode,
            width=160
        )
        self.appearance_mode.grid(row=12, column=0, padx=20, pady=(0, 20))
        self.appearance_mode.set("Dark")

    def _create_main_content(self):
        """Crée la zone de contenu principale"""
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

    def clear_main_content(self):
        """Efface le contenu principal"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    # ========================
    # NAVIGATION
    # ========================

    def show_dashboard(self):
        """Affiche le dashboard"""
        self.clear_main_content()
        self.current_tab = "dashboard"

        from .dashboard_tab import DashboardTab
        dashboard_tab = DashboardTab(self.main_frame, self.portfolio)
        dashboard_tab.grid(row=0, column=0, sticky="nsew")

    def show_portfolio(self):
        """Affiche l'onglet Portfolio"""
        self.clear_main_content()
        self.current_tab = "portfolio"

        from .portfolio_tab import PortfolioTab
        portfolio_tab = PortfolioTab(self.main_frame, self.portfolio)
        portfolio_tab.grid(row=0, column=0, sticky="nsew")

    def show_transactions(self):
        """Affiche l'onglet Transactions"""
        self.clear_main_content()
        self.current_tab = "transactions"

        from .transactions_tab import TransactionsTab
        transactions_tab = TransactionsTab(self.main_frame, self.portfolio)
        transactions_tab.grid(row=0, column=0, sticky="nsew")

    def show_dividends(self):
        """Affiche l'onglet Dividendes"""
        self.clear_main_content()
        self.current_tab = "dividends"

        from .dividends_tab import DividendsTab
        dividends_tab = DividendsTab(self.main_frame, self.portfolio)
        dividends_tab.grid(row=0, column=0, sticky="nsew")

    def show_sales_history(self):
        """Affiche l'onglet Historique des Ventes"""
        self.clear_main_content()
        self.current_tab = "sales_history"

        from .sales_history_tab import SalesHistoryTab
        sales_tab = SalesHistoryTab(self.main_frame, self.portfolio)
        sales_tab.grid(row=0, column=0, sticky="nsew")

    def show_tax(self):
        """Affiche l'onglet Fiscalité"""
        self.clear_main_content()
        self.current_tab = "tax"

        from .tax_tab import TaxTab
        tax_tab = TaxTab(self.main_frame, self.portfolio)
        tax_tab.grid(row=0, column=0, sticky="nsew")

    # ========================
    # ACTIONS
    # ========================

    def refresh_data(self):
        """Rafraîchit les données du marché"""
        import threading

        # Afficher un message d'information
        self.show_message(
            "⏳ Rafraîchissement en cours...\n"
            "Cela peut prendre jusqu'à 2 minutes (limite API Alpha Vantage).\n"
            "L'interface peut sembler figée, c'est normal.",
            "info"
        )

        def do_refresh():
            try:
                # Rafraîchir le cache de prix
                updated = self.portfolio.refresh_market_data_if_needed(force=True)

                # Afficher un message de succès dans le thread principal
                self.after(0, lambda: self.show_message(f"✅ {updated} ticker(s) mis à jour", "success"))

                # Recharger l'onglet actuel dans le thread principal
                self.after(0, self._reload_current_tab)

            except Exception as e:
                self.after(0, lambda: self.show_message(f"❌ Erreur: {str(e)}", "error"))

        # Lancer le rafraîchissement dans un thread séparé
        thread = threading.Thread(target=do_refresh, daemon=True)
        thread.start()

    def _auto_refresh_if_needed(self):
        """Déclenche un rafraîchissement automatique au démarrage si nécessaire."""
        if not self.portfolio.needs_market_refresh_today():
            return

        import threading

        self.show_message(
            "⏳ Mise à jour initiale des prix...\n"
            "Les données seront rechargées automatiquement.",
            "info"
        )

        def do_auto_refresh():
            try:
                updated = self.portfolio.refresh_market_data_if_needed(force=True)
                self.after(0, lambda: self.show_message(f"✅ {updated} ticker(s) mis à jour", "success"))
                self.after(0, self._reload_current_tab)
            except Exception as e:
                self.after(0, lambda: self.show_message(f"❌ Rafraîchissement automatique échoué: {str(e)}", "error"))

        thread = threading.Thread(target=do_auto_refresh, daemon=True)
        thread.start()

    def _reload_current_tab(self):
        """Recharge l'onglet actuel"""
        if self.current_tab == "dashboard":
            self.show_dashboard()
        elif self.current_tab == "portfolio":
            self.show_portfolio()
        elif self.current_tab == "transactions":
            self.show_transactions()
        elif self.current_tab == "dividends":
            self.show_dividends()
        elif self.current_tab == "sales_history":
            self.show_sales_history()
        elif self.current_tab == "tax":
            self.show_tax()

    def export_excel(self):
        """Exporte le portefeuille vers Excel"""
        try:
            from tkinter import filedialog
            import datetime

            # Demander le chemin de sauvegarde
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=f"portfolio_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx"
            )

            if filename:
                # Appeler la fonction d'export (à implémenter)
                from .excel_export import export_to_excel
                export_to_excel(self.portfolio, filename)
                self.show_message("✅ Export Excel réussi", "success")

        except Exception as e:
            self.show_message(f"❌ Erreur export: {str(e)}", "error")

    def change_appearance_mode(self, new_mode: str):
        """Change le mode d'apparence"""
        ctk.set_appearance_mode(new_mode.lower())

    def show_message(self, message: str, type: str = "info"):
        """Affiche un message temporaire"""
        # Créer un toplevel pour le message
        msg_window = ctk.CTkToplevel(self)
        msg_window.title("Message")

        # Dimensions et position
        msg_width = 400
        msg_height = 150
        x = self.winfo_x() + (self.winfo_width() // 2) - (msg_width // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (msg_height // 2)
        msg_window.geometry(f"{msg_width}x{msg_height}+{x}+{y}")

        # Désactiver redimensionnement
        msg_window.resizable(False, False)

        # Message
        label = ctk.CTkLabel(
            msg_window,
            text=message,
            font=ctk.CTkFont(size=14),
            wraplength=350
        )
        label.pack(pady=30, padx=20)

        # Bouton OK
        btn = ctk.CTkButton(
            msg_window,
            text="OK",
            command=msg_window.destroy,
            width=100
        )
        btn.pack(pady=10)

        # Auto-fermer après 3 secondes
        msg_window.after(3000, msg_window.destroy)

    def on_closing(self):
        """Gestionnaire de fermeture"""
        self.destroy()


def main():
    """Point d'entrée principal"""
    app = PortfolioApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
