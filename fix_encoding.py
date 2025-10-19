# -*- coding: utf-8 -*-
"""
Script pour ajouter l'encodage UTF-8 aux fichiers Python
"""

import os
from pathlib import Path

def add_encoding_header(file_path):
    """Ajoute l'en-tête d'encodage UTF-8 si nécessaire"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Vérifier si l'en-tête d'encodage est déjà présent
    if content.startswith('# -*- coding: utf-8 -*-'):
        print(f"✓ {file_path} - Encodage déjà présent")
        return

    # Ajouter l'en-tête
    new_content = '# -*- coding: utf-8 -*-\n' + content

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✓ {file_path} - Encodage ajouté")

def process_directory(directory):
    """Traite tous les fichiers .py dans un répertoire"""
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    add_encoding_header(file_path)
                except Exception as e:
                    print(f"✗ {file_path} - Erreur: {e}")

if __name__ == "__main__":
    portfolio_dir = Path(__file__).parent / "portfolio_manager"
    print(f"Ajout de l'encodage UTF-8 aux fichiers Python dans {portfolio_dir}...\n")
    process_directory(portfolio_dir)
    print("\nTerminé!")
