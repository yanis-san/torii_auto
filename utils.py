import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def get_supabase_client() -> Client:
    """
    Récupère le client Supabase.
    Lit depuis secrets.toml (Streamlit Cloud) ou .env (local)
    """
    # Essayer d'abord depuis Streamlit secrets (pour Streamlit Cloud)
    if hasattr(st, 'secrets') and 'SUPABASE_URL' in st.secrets:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    else:
        # Sinon, lire depuis .env (pour développement local)
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

    return create_client(url, key)


def get_current_academic_year():
    """
    Récupère l'année académique active depuis Supabase.

    Returns:
        dict: Dictionnaire contenant id, year_label, prefix de l'année active
        None: Si aucune année académique active n'est trouvée
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table('academic_years').select('*').eq('is_current', True).execute()

        if response.data and len(response.data) > 0:
            year_data = response.data[0]
            # Vérifier que toutes les données nécessaires sont présentes
            if year_data.get('id') and year_data.get('year_label') and year_data.get('prefix'):
                return year_data
            else:
                print(f"⚠️ Données incomplètes dans academic_years: {year_data}")
                return None
        else:
            print("⚠️ Aucune année académique avec is_current=True trouvée")
            return None
    except Exception as e:
        print(f"Erreur lors de la récupération de l'année académique: {str(e)}")
        import traceback
        traceback.print_exc()
        return None