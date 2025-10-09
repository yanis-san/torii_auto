import streamlit as st
from utils import get_supabase_client
from auth import update_password

def show():
    st.title("👤 Mon Profil")

    if not st.session_state.authenticated or not st.session_state.user_data:
        st.error("Vous devez être connecté pour accéder à cette page")
        return

    supabase = get_supabase_client()
    user_data = st.session_state.user_data

    tab1, tab2 = st.tabs(["📋 Informations", "🔒 Sécurité"])

    with tab1:
        st.subheader("Informations du compte")

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Prénom :** {user_data['first_name']}")
            st.write(f"**Nom :** {user_data['last_name']}")

        with col2:
            st.write(f"**Email :** {user_data['email']}")
            st.write(f"**Rôle :** {user_data['role'].capitalize()}")

        st.divider()

        # Formulaire de modification du profil
        st.subheader("Modifier mes informations")

        with st.form("update_profile_form"):
            first_name = st.text_input("Prénom", value=user_data['first_name'])
            last_name = st.text_input("Nom", value=user_data['last_name'])

            submitted = st.form_submit_button("Enregistrer les modifications", width="stretch")

            if submitted:
                try:
                    # Mettre à jour dans la table users
                    update_data = {
                        'first_name': first_name,
                        'last_name': last_name,
                        'updated_at': 'NOW()'
                    }

                    supabase.table('users').update(update_data).eq('id', user_data['user_id']).execute()

                    # Si enseignant, mettre à jour aussi dans teachers
                    if user_data['role'] == 'teacher' and user_data.get('teacher_id'):
                        teacher_update = {
                            'first_name': first_name,
                            'last_name': last_name
                        }
                        supabase.table('teachers').update(teacher_update).eq('id', user_data['teacher_id']).execute()

                    # Mettre à jour la session
                    st.session_state.user_data['first_name'] = first_name
                    st.session_state.user_data['last_name'] = last_name
                    st.session_state.user_name = f"{first_name} {last_name}"

                    st.success("✅ Profil mis à jour avec succès!")
                    st.rerun()

                except Exception as e:
                    st.error(f"Erreur lors de la mise à jour : {str(e)}")

        # Afficher les statistiques pour les enseignants
        if user_data['role'] == 'teacher' and user_data.get('teacher_id'):
            st.divider()
            st.subheader("📊 Mes statistiques")

            try:
                # Nombre de groupes assignés
                groups = supabase.table('group_teacher').select('*, groups(name, languages(name))').eq('teacher_id', user_data['teacher_id']).execute()

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Groupes assignés", len(groups.data) if groups.data else 0)

                with col2:
                    # Nombre de cours au planning
                    if groups.data:
                        group_ids = [g['group_id'] for g in groups.data]
                        schedules = supabase.table('schedule').select('*', count='exact').in_('group_id', group_ids).execute()
                        st.metric("Cours planifiés", schedules.count)
                    else:
                        st.metric("Cours planifiés", 0)

                with col3:
                    # Nombre total d'étudiants
                    if groups.data:
                        group_ids = [g['group_id'] for g in groups.data]
                        enrollments = supabase.table('enrollments').select('*', count='exact').in_('group_id', group_ids).eq('enrollment_active', True).execute()
                        st.metric("Étudiants actifs", enrollments.count)
                    else:
                        st.metric("Étudiants actifs", 0)

                # Liste des groupes
                if groups.data:
                    st.markdown("**Mes groupes :**")
                    for g in groups.data:
                        group = g.get('groups', {})
                        lang_name = group.get('languages', {}).get('name', 'N/A') if group.get('languages') else 'N/A'
                        st.write(f"- {group.get('name', 'N/A')} ({lang_name})")

            except Exception as e:
                st.error(f"Erreur lors du chargement des statistiques : {str(e)}")

    with tab2:
        st.subheader("Changer le mot de passe")

        with st.form("change_password_form"):
            new_password = st.text_input("Nouveau mot de passe", type="password",
                                        help="Au moins 6 caractères")
            confirm_password = st.text_input("Confirmer le mot de passe", type="password")

            submitted = st.form_submit_button("Changer le mot de passe", width="stretch")

            if submitted:
                if not new_password or not confirm_password:
                    st.warning("Veuillez remplir tous les champs")
                elif new_password != confirm_password:
                    st.error("Les mots de passe ne correspondent pas")
                elif len(new_password) < 6:
                    st.error("Le mot de passe doit contenir au moins 6 caractères")
                else:
                    result = update_password(new_password)

                    if result["success"]:
                        st.success(result["message"])
                    else:
                        st.error(result["message"])

        st.divider()
        st.subheader("🗑️ Supprimer mon compte")
        st.warning("⚠️ Cette action est irréversible. Toutes vos données seront supprimées.")

        if st.button("Supprimer mon compte", type="primary"):
            st.error("Fonctionnalité à venir. Contactez un administrateur pour supprimer votre compte.")
