"""
Script d'initialisation de la base de données
À exécuter une seule fois pour insérer les langues de base
"""

from utils import get_supabase_client

def init_languages():
    """Initialise les langues dans la base de données"""
    supabase = get_supabase_client()

    languages = ['Japonais', 'Chinois', 'Coréen']

    try:
        # Vérifier si les langues existent déjà
        existing = supabase.table('languages').select('name').execute()
        existing_names = [lang['name'] for lang in existing.data] if existing.data else []

        for lang in languages:
            if lang not in existing_names:
                supabase.table('languages').insert({'name': lang}).execute()
                print(f"OK - Langue ajoutee : {lang}")
            else:
                print(f"INFO - Langue deja presente : {lang}")

        print("\nOK - Initialisation terminee!")

    except Exception as e:
        print(f"ERREUR - Lors de l'initialisation : {str(e)}")

if __name__ == "__main__":
    init_languages()
