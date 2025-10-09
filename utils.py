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