"""
Module d'authentification avec Supabase Auth
"""

import streamlit as st
from utils import get_supabase_client
from typing import Optional, Dict, Any

def sign_up(email: str, password: str, first_name: str, last_name: str, role: str = "teacher") -> Dict[str, Any]:
    """
    Crée un nouveau compte utilisateur

    Args:
        email: Email de l'utilisateur
        password: Mot de passe
        first_name: Prénom
        last_name: Nom
        role: Rôle (admin ou teacher)

    Returns:
        Dict avec success (bool) et message ou data
    """
    supabase = get_supabase_client()

    try:
        # Créer l'utilisateur avec Supabase Auth (sans envoi d'email)
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "first_name": first_name,
                    "last_name": last_name,
                    "role": role
                },
                "email_redirect_to": None  # Pas d'envoi d'email
            }
        })

        if response.user:
            # Créer l'entrée dans la table users avec email_confirmed = False par défaut
            user_data = {
                "id": response.user.id,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "email_confirmed": False  # Désactivé par défaut
            }

            supabase.table('users').insert(user_data).execute()

            # Si c'est un enseignant, créer aussi l'entrée dans teachers
            if role == "teacher":
                teacher_data = {
                    "user_id": response.user.id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email
                }
                supabase.table('teachers').insert(teacher_data).execute()

            return {
                "success": True,
                "message": "Compte créé avec succès! Un administrateur doit activer votre compte avant que vous puissiez vous connecter.",
                "data": response.user
            }
        else:
            return {
                "success": False,
                "message": "Erreur lors de la création du compte"
            }

    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg.lower():
            return {
                "success": False,
                "message": "Cet email est déjà utilisé"
            }
        return {
            "success": False,
            "message": f"Erreur : {error_msg}"
        }

def sign_in(email: str, password: str) -> Dict[str, Any]:
    """
    Connecte un utilisateur

    Args:
        email: Email de l'utilisateur
        password: Mot de passe

    Returns:
        Dict avec success (bool) et message ou data
    """
    supabase = get_supabase_client()

    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if response.user:
            # Récupérer les infos utilisateur depuis la table users
            user_info = supabase.table('users').select('*').eq('id', response.user.id).execute()

            if user_info.data:
                user_data = user_info.data[0]

                # Vérifier si l'email est confirmé
                if not user_data.get('email_confirmed', False):
                    return {
                        "success": False,
                        "message": "Votre compte n'a pas encore été activé par un administrateur. Veuillez patienter."
                    }

                # Si c'est un enseignant, récupérer aussi l'ID enseignant
                teacher_id = None
                if user_data['role'] == 'teacher':
                    teacher_info = supabase.table('teachers').select('id').eq('user_id', response.user.id).execute()
                    if teacher_info.data:
                        teacher_id = teacher_info.data[0]['id']

                return {
                    "success": True,
                    "data": {
                        "user_id": response.user.id,
                        "email": user_data['email'],
                        "first_name": user_data['first_name'],
                        "last_name": user_data['last_name'],
                        "role": user_data['role'],
                        "teacher_id": teacher_id
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "Informations utilisateur non trouvées"
                }
        else:
            return {
                "success": False,
                "message": "Email ou mot de passe incorrect"
            }

    except Exception as e:
        error_msg = str(e)
        if "invalid" in error_msg.lower() or "credentials" in error_msg.lower():
            return {
                "success": False,
                "message": "Email ou mot de passe incorrect"
            }
        return {
            "success": False,
            "message": f"Erreur de connexion : {error_msg}"
        }

def sign_out() -> Dict[str, Any]:
    """
    Déconnecte l'utilisateur

    Returns:
        Dict avec success (bool) et message
    """
    supabase = get_supabase_client()

    try:
        supabase.auth.sign_out()
        return {
            "success": True,
            "message": "Déconnexion réussie"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erreur lors de la déconnexion : {str(e)}"
        }

def reset_password(email: str) -> Dict[str, Any]:
    """
    Envoie un email de réinitialisation de mot de passe

    Args:
        email: Email de l'utilisateur

    Returns:
        Dict avec success (bool) et message
    """
    supabase = get_supabase_client()

    try:
        supabase.auth.reset_password_email(email)
        return {
            "success": True,
            "message": "Email de réinitialisation envoyé! Vérifiez votre boîte mail."
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erreur : {str(e)}"
        }

def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Récupère l'utilisateur actuellement connecté

    Returns:
        Dict avec les infos utilisateur ou None
    """
    supabase = get_supabase_client()

    try:
        user = supabase.auth.get_user()
        if user:
            # Récupérer les infos depuis la table users
            user_info = supabase.table('users').select('*').eq('id', user.user.id).execute()

            if user_info.data:
                user_data = user_info.data[0]

                # Si enseignant, récupérer l'ID
                teacher_id = None
                if user_data['role'] == 'teacher':
                    teacher_info = supabase.table('teachers').select('id').eq('user_id', user.user.id).execute()
                    if teacher_info.data:
                        teacher_id = teacher_info.data[0]['id']

                return {
                    "user_id": user.user.id,
                    "email": user_data['email'],
                    "first_name": user_data['first_name'],
                    "last_name": user_data['last_name'],
                    "role": user_data['role'],
                    "teacher_id": teacher_id
                }

        return None
    except:
        return None

def update_password(new_password: str) -> Dict[str, Any]:
    """
    Met à jour le mot de passe de l'utilisateur connecté

    Args:
        new_password: Nouveau mot de passe

    Returns:
        Dict avec success (bool) et message
    """
    supabase = get_supabase_client()

    try:
        supabase.auth.update_user({"password": new_password})
        return {
            "success": True,
            "message": "Mot de passe mis à jour avec succès"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erreur : {str(e)}"
        }

def init_session_state():
    """Initialise les variables de session pour l'authentification"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
