# -*- coding: utf-8 -*-
"""
Script pour convertir les fichiers de latin-1 vers UTF-8
"""

import os
from pathlib import Path

def fix_file_encoding(file_path):
    """Convertit un fichier de latin-1 vers UTF-8"""
    try:
        # Essayer de lire en latin-1 (iso-8859-1)
        with open(file_path, 'r', encoding='latin-1') as f:
            content = f.read()

        # Vérifier si l'en-tête d'encodage est déjà présent
        if not content.startswith('# -*- coding: utf-8 -*-'):
            content = '# -*- coding: utf-8 -*-\n' + content

        # Réécrire en UTF-8
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✓ {file_path} - Converti en UTF-8")
        return True
    except Exception as e:
        print(f"✗ {file_path} - Erreur: {e}")
        return False

if __name__ == "__main__":
    files_to_fix = [
        "portfolio_manager/config.py",
        "portfolio_manager/main.py",
        "portfolio_manager/database/db_manager.py",
        "portfolio_manager/database/models.py",
        "portfolio_manager/core/calculator.py"
    ]

    print("Conversion des fichiers en UTF-8...\n")
    for file_path in files_to_fix:
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            fix_file_encoding(full_path)
        else:
            print(f"✗ {file_path} - Fichier non trouvé")

    print("\nTerminé!")
