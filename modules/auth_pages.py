"""
Pages d'authentification (connexion, inscription, mot de passe oublié)
"""

import streamlit as st
from auth import sign_in, sign_up, reset_password

def show_login():
    """Affiche la page de connexion"""
    st.title("🎓 Institut Torii - Connexion")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### Connexion")

        with st.form("login_form"):
            email = st.text_input("Email", placeholder="votre.email@exemple.com")
            password = st.text_input("Mot de passe", type="password")

            col_a, col_b = st.columns(2)

            with col_a:
                submit = st.form_submit_button("Se connecter", width="stretch")

            with col_b:
                if st.form_submit_button("Créer un compte", width="stretch"):
                    st.session_state.show_signup = True
                    st.rerun()

            if submit:
                if email and password:
                    with st.spinner("Connexion en cours..."):
                        result = sign_in(email, password)

                        if result["success"]:
                            st.session_state.authenticated = True
                            st.session_state.user_data = result["data"]
                            st.session_state.logged_in = True
                            st.session_state.user_role = result["data"]["role"]
                            st.session_state.user_name = f"{result['data']['first_name']} {result['data']['last_name']}"

                            if result["data"]["teacher_id"]:
                                st.session_state.teacher_id = result["data"]["teacher_id"]

                            st.success("✅ Connexion réussie!")
                            st.rerun()
                        else:
                            st.error(result["message"])
                else:
                    st.warning("Veuillez remplir tous les champs")

        st.divider()

        if st.button("Mot de passe oublié ?"):
            st.session_state.show_reset = True
            st.rerun()

def show_signup():
    """Affiche la page d'inscription"""
    st.title("🎓 Institut Torii - Inscription")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### Créer un compte")

        with st.form("signup_form"):
            first_name = st.text_input("Prénom *")
            last_name = st.text_input("Nom *")
            email = st.text_input("Email *", placeholder="votre.email@exemple.com")

            password = st.text_input("Mot de passe *", type="password",
                                    help="Au moins 6 caractères")
            password_confirm = st.text_input("Confirmer le mot de passe *", type="password")

            role = st.selectbox("Type de compte", ["Enseignant", "Administrateur"])

            st.markdown("*Les champs marqués d'un astérisque sont obligatoires*")

            col_a, col_b = st.columns(2)

            with col_a:
                submit = st.form_submit_button("Créer le compte", width="stretch")

            with col_b:
                if st.form_submit_button("Retour", width="stretch"):
                    st.session_state.show_signup = False
                    st.rerun()

            if submit:
                if not all([first_name, last_name, email, password, password_confirm]):
                    st.warning("Veuillez remplir tous les champs obligatoires")
                elif password != password_confirm:
                    st.error("Les mots de passe ne correspondent pas")
                elif len(password) < 6:
                    st.error("Le mot de passe doit contenir au moins 6 caractères")
                else:
                    with st.spinner("Création du compte..."):
                        role_value = "admin" if role == "Administrateur" else "teacher"
                        result = sign_up(email, password, first_name, last_name, role_value)

                        if result["success"]:
                            st.success(result["message"])
                            st.info("Vous pouvez maintenant vous connecter avec votre email et mot de passe.")

                            # Attendre 3 secondes puis retourner à la page de connexion
                            import time
                            time.sleep(3)
                            st.session_state.show_signup = False
                            st.rerun()
                        else:
                            st.error(result["message"])

def show_reset_password():
    """Affiche la page de réinitialisation de mot de passe"""
    st.title("🎓 Institut Torii - Mot de passe oublié")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### Réinitialiser le mot de passe")
        st.info("Entrez votre email pour recevoir un lien de réinitialisation")

        with st.form("reset_form"):
            email = st.text_input("Email", placeholder="votre.email@exemple.com")

            col_a, col_b = st.columns(2)

            with col_a:
                submit = st.form_submit_button("Envoyer", width="stretch")

            with col_b:
                if st.form_submit_button("Retour", width="stretch"):
                    st.session_state.show_reset = False
                    st.rerun()

            if submit:
                if email:
                    with st.spinner("Envoi en cours..."):
                        result = reset_password(email)

                        if result["success"]:
                            st.success(result["message"])
                        else:
                            st.error(result["message"])
                else:
                    st.warning("Veuillez entrer votre email")
