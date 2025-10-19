# -*- coding: utf-8 -*-
"""
Version Tkinter standard pour compatibilité macOS anciennes versions
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from portfolio_manager.core.portfolio import Portfolio
from portfolio_manager.utils.formatters import format_currency, format_percentage


class PortfolioAppTk(tk.Tk):
    """Application Portfolio Manager avec Tkinter standard"""

    def __init__(self):
        super().__init__()

        self.title("Portfolio Manager - Trade Republic")
        self.geometry("1200x700")

        # Initialiser le portfolio
        self.portfolio = Portfolio()

        # Créer l'interface
        self.create_widgets()

        # Charger les données
        self.load_dashboard()

        # Rafraîchir automatiquement les données si nécessaire
        self.after(500, self.auto_refresh_if_needed)

    def create_widgets(self):
        """Crée l'interface"""
        # Frame principale avec sidebar et contenu
        self.sidebar_frame = tk.Frame(self, bg="#2b2b2b", width=200)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_frame.pack_propagate(False)

        self.main_frame = tk.Frame(self, bg="#1e1e1e")
        self.main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Sidebar
        title_label = tk.Label(
            self.sidebar_frame,
            text="📊 Portfolio\nManager",
            bg="#2b2b2b",
            fg="white",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=30)

        # Bouton Dashboard
        btn_dashboard = tk.Button(
            self.sidebar_frame,
            text="📈 Dashboard",
            command=self.load_dashboard,
            bg="#3b82f6",
            fg="white",
            font=("Arial", 12),
            relief=tk.FLAT,
            cursor="hand2",
            pady=10
        )
        btn_dashboard.pack(pady=5, padx=10, fill=tk.X)

        # Bouton Rafraîchir
        btn_refresh = tk.Button(
            self.sidebar_frame,
            text="🔄 Rafraîchir",
            command=self.refresh_data,
            bg="#2b2b2b",
            fg="white",
            font=("Arial", 11),
            relief=tk.FLAT,
            cursor="hand2",
            pady=8
        )
        btn_refresh.pack(pady=(50, 5), padx=10, fill=tk.X)

        # Info version
        version_label = tk.Label(
            self.sidebar_frame,
            text="Version Tkinter\nCompatibilité macOS",
            bg="#2b2b2b",
            fg="#888888",
            font=("Arial", 9)
        )
        version_label.pack(side=tk.BOTTOM, pady=20)

    def load_dashboard(self):
        """Charge le dashboard"""
        # Nettoyer le contenu
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        try:
            # Récupérer les données
            snapshot = self.portfolio.get_portfolio_snapshot()
            performance = self.portfolio.get_performance_metrics()

            # Frame scrollable
            canvas = tk.Canvas(self.main_frame, bg="#1e1e1e", highlightthickness=0)
            scrollbar = tk.Scrollbar(self.main_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg="#1e1e1e")

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            # Titre
            title = tk.Label(
                scrollable_frame,
                text="📊 Dashboard",
                bg="#1e1e1e",
                fg="white",
                font=("Arial", 24, "bold")
            )
            title.pack(pady=20, anchor="w", padx=20)

            # Frame pour les métriques
            metrics_frame = tk.Frame(scrollable_frame, bg="#1e1e1e")
            metrics_frame.pack(fill=tk.X, padx=20, pady=10)

            # Créer 4 cartes de métriques
            metrics = [
                ("💰 Valeur Totale", format_currency(snapshot.total_invested),
                 format_percentage(snapshot.total_gain_loss_percent)),
                ("📈 Gains Totaux", format_currency(snapshot.total_gain_loss),
                 f"{snapshot.positions_count} positions"),
                ("💵 Dividendes", format_currency(snapshot.dividend_income),
                 f"{format_percentage(performance.dividend_yield)} yield"),
                ("🎯 Performance", format_percentage(performance.total_return_percent),
                 f"Frais: {format_currency(performance.total_fees_paid)}")
            ]

            for i, (title, value, subtitle) in enumerate(metrics):
                card = tk.Frame(metrics_frame, bg="#2b2b2b", relief=tk.RAISED, borderwidth=2)
                card.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
                metrics_frame.columnconfigure(i, weight=1)

                tk.Label(card, text=title, bg="#2b2b2b", fg="white",
                        font=("Arial", 10)).pack(pady=(15, 5))
                tk.Label(card, text=value, bg="#2b2b2b", fg="white",
                        font=("Arial", 16, "bold")).pack(pady=5)
                tk.Label(card, text=subtitle, bg="#2b2b2b", fg="#888888",
                        font=("Arial", 9)).pack(pady=(5, 15))

            # Section Positions
            positions_frame = tk.Frame(scrollable_frame, bg="#2b2b2b", relief=tk.RAISED, borderwidth=2)
            positions_frame.pack(fill=tk.BOTH, padx=20, pady=20, expand=True)

            tk.Label(
                positions_frame,
                text="💼 Top Positions",
                bg="#2b2b2b",
                fg="white",
                font=("Arial", 16, "bold")
            ).pack(anchor="w", padx=15, pady=(15, 10))

            # Tableau des positions
            if snapshot.positions:
                # En-têtes
                header_frame = tk.Frame(positions_frame, bg="#2b2b2b")
                header_frame.pack(fill=tk.X, padx=15, pady=5)

                headers = ["Ticker", "Société", "Valeur", "P&L", "Poids"]
                widths = [10, 25, 15, 15, 10]

                for i, (header, width) in enumerate(zip(headers, widths)):
                    tk.Label(
                        header_frame,
                        text=header,
                        bg="#2b2b2b",
                        fg="white",
                        font=("Arial", 10, "bold"),
                        width=width,
                        anchor="w"
                    ).grid(row=0, column=i, padx=5)

                # Lignes de positions (top 5)
                for idx, pos in enumerate(snapshot.positions[:5]):
                    row_frame = tk.Frame(positions_frame, bg="#2b2b2b")
                    row_frame.pack(fill=tk.X, padx=15, pady=2)

                    # Données
                    company = pos['company_name'][:23] + "..." if len(pos['company_name']) > 23 else pos['company_name']
                    pnl_text = format_percentage(pos['gain_loss_percent'])
                    pnl_color = "#10b981" if pos['gain_loss_percent'] >= 0 else "#ef4444"

                    data = [
                        (pos['ticker'], "white", 10),
                        (company, "white", 25),
                        (format_currency(pos['current_value']), "white", 15),
                        (pnl_text, pnl_color, 15),
                        (f"{pos['weight']:.1f}%", "white", 10)
                    ]

                    for i, (text, color, width) in enumerate(data):
                        tk.Label(
                            row_frame,
                            text=text,
                            bg="#2b2b2b",
                            fg=color,
                            font=("Arial", 10),
                            width=width,
                            anchor="w"
                        ).grid(row=0, column=i, padx=5)

            else:
                tk.Label(
                    positions_frame,
                    text="Aucune position dans le portefeuille",
                    bg="#2b2b2b",
                    fg="#888888",
                    font=("Arial", 12)
                ).pack(pady=30)

            # Pack le canvas et scrollbar
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        except Exception as e:
            error_label = tk.Label(
                self.main_frame,
                text=f"❌ Erreur de chargement:\n{str(e)}",
                bg="#1e1e1e",
                fg="#ef4444",
                font=("Arial", 12)
            )
            error_label.pack(pady=50)

    def refresh_data(self):
        """Rafraîchit les données"""
        try:
            updated = self.portfolio.refresh_market_data_if_needed(force=True)
            messagebox.showinfo("Succès", f"✅ {updated} ticker(s) mis à jour")
            self.load_dashboard()
        except Exception as e:
            messagebox.showerror("Erreur", f"❌ Erreur: {str(e)}")

    def auto_refresh_if_needed(self):
        """Déclenche un rafraîchissement automatique au démarrage si nécessaire."""
        if not self.portfolio.needs_market_refresh_today():
            return

        import threading

        print("⏳ Mise à jour initiale des prix...")

        def worker():
            try:
                updated = self.portfolio.refresh_market_data_if_needed(force=True)
                print(f"✅ Mise à jour automatique: {updated} ticker(s) mis à jour")
                self.after(0, self.load_dashboard)
            except Exception as exc:
                print(f"❌ Rafraîchissement automatique échoué: {exc}")

        threading.Thread(target=worker, daemon=True).start()


def main():
    """Lance l'application"""
    print("🚀 Lancement de Portfolio Manager (version Tkinter)...")
    print("📊 Chargement de l'interface...")

    try:
        app = PortfolioAppTk()
        app.mainloop()
    except Exception as e:
        print(f"❌ Erreur au lancement: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
