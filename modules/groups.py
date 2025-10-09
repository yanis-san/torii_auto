import streamlit as st
import pandas as pd
from utils import get_supabase_client

def show():
    st.title("📚 Gestion des Groupes")

    supabase = get_supabase_client()

    tab1, tab2 = st.tabs(["📋 Liste", "➕ Ajouter"])

    with tab1:
        st.subheader("Liste des Groupes")

        try:
            groups_response = supabase.table('groups').select('*, languages(name)').order('name').execute()

            if groups_response.data:
                groups_list = []
                for group in groups_response.data:
                    # Compter les étudiants inscrits
                    enrollments = supabase.table('enrollments').select('*', count='exact').eq('group_id', group['id']).eq('enrollment_active', True).execute()

                    # Compter les enseignants
                    teachers = supabase.table('group_teacher').select('*', count='exact').eq('group_id', group['id']).execute()

                    lang_name = group.get('languages', {}).get('name', 'N/A') if group.get('languages') else 'N/A'
                    status = "✅ Prêt" if enrollments.count >= group['min_students'] else f"⏳ {enrollments.count}/{group['min_students']}"

                    groups_list.append({
                        'ID': group['id'],
                        'Nom': group['name'],
                        'Langue': lang_name,
                        'Niveau': group['level'],
                        'Mode': group['mode'],
                        'Durée': f"{group['duration_months']} mois",
                        'Étudiants': f"{enrollments.count}/{group['min_students']}",
                        'Enseignants': teachers.count,
                        'Statut': status
                    })

                df = pd.DataFrame(groups_list)
                st.dataframe(df, width="stretch", hide_index=True)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Groupes", len(groups_list))
                with col2:
                    ready = len([g for g in groups_list if '✅' in g['Statut']])
                    st.metric("Groupes Prêts", ready)
                with col3:
                    total_students = sum([int(g['Étudiants'].split('/')[0]) for g in groups_list])
                    st.metric("Total Inscrits", total_students)

                # Détails des groupes
                st.divider()
                st.subheader("Détails et Actions")

                for group in groups_response.data:
                    lang_name = group.get('languages', {}).get('name', 'N/A') if group.get('languages') else 'N/A'
                    with st.expander(f"{group['name']} - {lang_name} (Niveau {group['level']})"):
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            st.write(f"**Langue:** {lang_name}")
                            st.write(f"**Niveau:** {group['level']}")
                            st.write(f"**Mode:** {group['mode']}")
                            st.write(f"**Durée:** {group['duration_months']} mois")
                            st.write(f"**Minimum d'étudiants:** {group['min_students']}")
                            if group.get('start_date'):
                                st.write(f"**Date de début:** {group['start_date']}")

                            # Afficher les enseignants
                            group_teachers = supabase.table('group_teacher').select('*, teachers(first_name, last_name, email)').eq('group_id', group['id']).execute()

                            if group_teachers.data:
                                st.markdown("**Enseignants:**")
                                for gt in group_teachers.data:
                                    teacher = gt.get('teachers', {})
                                    st.write(f"- {teacher.get('first_name', 'N/A')} {teacher.get('last_name', 'N/A')} ({teacher.get('email', 'N/A')})")

                                    # Bouton pour retirer l'enseignant
                                    if st.button(f"Retirer {teacher.get('first_name', '')} {teacher.get('last_name', '')}", key=f"remove_teacher_{group['id']}_{gt['teacher_id']}"):
                                        try:
                                            supabase.table('group_teacher').delete().eq('group_id', group['id']).eq('teacher_id', gt['teacher_id']).execute()
                                            st.success("Enseignant retiré")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erreur : {str(e)}")
                            else:
                                st.info("Aucun enseignant assigné")

                            # Ajouter un enseignant
                            st.markdown("**Ajouter un enseignant:**")
                            teachers_all = supabase.table('teachers').select('*').execute()
                            if teachers_all.data:
                                teacher_options = {f"{t['first_name']} {t['last_name']}": t['id'] for t in teachers_all.data}
                                selected_teacher = st.selectbox("Sélectionner un enseignant", list(teacher_options.keys()), key=f"add_teacher_{group['id']}")

                                if st.button("Ajouter l'enseignant", key=f"add_teacher_btn_{group['id']}"):
                                    try:
                                        # Vérifier si déjà assigné
                                        existing = supabase.table('group_teacher').select('*').eq('group_id', group['id']).eq('teacher_id', teacher_options[selected_teacher]).execute()
                                        if existing.data:
                                            st.warning("Cet enseignant est déjà assigné à ce groupe")
                                        else:
                                            supabase.table('group_teacher').insert({'group_id': group['id'], 'teacher_id': teacher_options[selected_teacher]}).execute()
                                            st.success("Enseignant ajouté")
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"Erreur : {str(e)}")

                            # Afficher les étudiants
                            st.divider()
                            enrollments = supabase.table('enrollments').select('*, students(first_name, last_name, email, student_code)').eq('group_id', group['id']).execute()

                            if enrollments.data:
                                st.markdown("**Étudiants inscrits:**")
                                for enr in enrollments.data:
                                    student = enr.get('students', {})
                                    status_icon = "✅" if enr['enrollment_active'] else "❌"
                                    st.write(f"{status_icon} {student.get('first_name', 'N/A')} {student.get('last_name', 'N/A')} - {student.get('student_code', 'N/A')} (Niveau {enr['level']})")
                            else:
                                st.info("Aucun étudiant inscrit")

                        with col2:
                            if st.button("Supprimer", key=f"delete_{group['id']}", type="primary"):
                                try:
                                    supabase.table('groups').delete().eq('id', group['id']).execute()
                                    st.success("Groupe supprimé")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erreur : {str(e)}")

            else:
                st.info("Aucun groupe enregistré")

        except Exception as e:
            st.error(f"Erreur lors du chargement des groupes : {str(e)}")

    with tab2:
        st.subheader("Ajouter un Nouveau Groupe")

        with st.form("add_group_form"):
            name = st.text_input("Nom du groupe *")

            # Récupérer les langues
            try:
                languages = supabase.table('languages').select('*').execute()
                if languages.data:
                    lang_options = {lang['name']: lang['id'] for lang in languages.data}
                    selected_language = st.selectbox("Langue *", list(lang_options.keys()))
                else:
                    st.error("Aucune langue disponible. Veuillez d'abord ajouter des langues.")
                    selected_language = None
            except Exception as e:
                st.error(f"Erreur lors du chargement des langues : {str(e)}")
                selected_language = None

            level = st.text_input("Niveau *", placeholder="Ex: 1, 2, A1, B2, etc.")
            min_students = st.number_input("Nombre minimum d'étudiants *", min_value=1, value=5)
            mode = st.selectbox("Mode *", [
                "online_group",
                "online_individual",
                "presential_group",
                "presential_individual",
                "online_group_old",
                "online_individual_old",
                "presential_group_old",
                "presential_individual_old"
            ])
            duration_months = st.number_input("Durée (en mois) *", min_value=1, value=3)
            start_date = st.date_input("Date de début", value=None, help="Date de début du groupe (optionnel)")

            st.markdown("*Les champs marqués d'un astérisque sont obligatoires*")

            submitted = st.form_submit_button("Ajouter le groupe", width="stretch")

            if submitted:
                if name and selected_language and level:
                    try:
                        # Insérer le nouveau groupe
                        new_group = {
                            'name': name,
                            'language_id': lang_options[selected_language],
                            'level': level,
                            'min_students': min_students,
                            'mode': mode,
                            'duration_months': duration_months
                        }

                        # Ajouter la date de début si elle est spécifiée
                        if start_date:
                            new_group['start_date'] = start_date.isoformat()

                        response = supabase.table('groups').insert(new_group).execute()

                        if response.data:
                            st.success("✅ Groupe ajouté avec succès!")
                            st.rerun()
                        else:
                            st.error("Erreur lors de l'ajout du groupe")

                    except Exception as e:
                        st.error(f"Erreur : {str(e)}")
                else:
                    st.warning("Veuillez remplir tous les champs obligatoires")
