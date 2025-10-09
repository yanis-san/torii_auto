import streamlit as st
from auth import init_session_state, sign_out
from modules import auth_pages, dashboard, students, teachers, classrooms, groups, payments, schedule, attendance, profile

# Configuration de la page
st.set_page_config(
    page_title="Institut Torii",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation de la session
init_session_state()

if 'show_signup' not in st.session_state:
    st.session_state.show_signup = False
if 'show_reset' not in st.session_state:
    st.session_state.show_reset = False

# Compatibilité avec l'ancien système
if st.session_state.authenticated and st.session_state.user_data:
    # Synchroniser les variables de session
    st.session_state.logged_in = True
    st.session_state.user_role = st.session_state.user_data.get('role')
    user_data = st.session_state.user_data
    st.session_state.user_name = f"{user_data.get('first_name')} {user_data.get('last_name')}"
    if user_data.get('teacher_id'):
        st.session_state.teacher_id = user_data['teacher_id']
elif 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Page de connexion/inscription
if not st.session_state.authenticated:
    if st.session_state.show_signup:
        auth_pages.show_signup()
    elif st.session_state.show_reset:
        auth_pages.show_reset_password()
    else:
        auth_pages.show_login()
else:
    # Sidebar avec navigation
    with st.sidebar:
        st.title("🎓 Institut Torii")
        st.markdown(f"**Bienvenue** {st.session_state.user_name}")
        st.markdown(f"*Rôle: {st.session_state.user_role}*")
        st.divider()

        # Menu de navigation selon le rôle
        if st.session_state.user_role == "admin":
            page = st.radio(
                "Navigation",
                [
                    "📊 Dashboard",
                    "👥 Étudiants",
                    "💰 Paiements",
                    "📚 Groupes",
                    "👨‍🏫 Enseignants",
                    "🏫 Salles",
                    "📅 Planning",
                    "✅ Présences",
                    "👤 Mon Profil"
                ],
                index=0  # Dashboard par défaut
            )
        else:
            page = st.radio(
                "Navigation",
                [
                    "📅 Mon Planning",
                    "✅ Présences",
                    "👤 Mon Profil"
                ],
                index=0  # Mon Planning par défaut
            )

        st.divider()
        if st.button("Déconnexion", width="stretch"):
            sign_out()
            st.session_state.authenticated = False
            st.session_state.user_data = None
            st.session_state.logged_in = False
            st.session_state.user_role = None
            st.session_state.user_name = None
            if 'teacher_id' in st.session_state:
                del st.session_state.teacher_id
            st.rerun()

    # Contenu principal selon la page sélectionnée
    try:
        if page == "📊 Dashboard":
            dashboard.show()
        elif page == "👥 Étudiants":
            students.show()
        elif page == "💰 Paiements":
            payments.show()
        elif page == "📚 Groupes":
            groups.show()
        elif page == "👨‍🏫 Enseignants":
            teachers.show()
        elif page == "🏫 Salles":
            classrooms.show()
        elif page == "📅 Planning" or page == "📅 Mon Planning":
            schedule.show()
        elif page == "✅ Présences":
            attendance.show()
        elif page == "👤 Mon Profil":
            profile.show()
        else:
            st.info("Sélectionnez une page dans le menu de gauche")
    except Exception as e:
        st.error(f"❌ Erreur : {str(e)}")
        import traceback
        st.code(traceback.format_exc())
