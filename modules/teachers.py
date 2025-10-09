import streamlit as st
import pandas as pd
from utils import get_supabase_client

def show():
    st.title("👨‍🏫 Gestion des Enseignants")

    supabase = get_supabase_client()

    tab1, tab2 = st.tabs(["📋 Liste", "➕ Ajouter"])

    with tab1:
        st.subheader("Liste des Enseignants")

        try:
            teachers_response = supabase.table('teachers').select('*').order('last_name').execute()

            if teachers_response.data:
                teachers_list = []
                for teacher in teachers_response.data:
                    # Compter les groupes assignés
                    groups = supabase.table('group_teacher').select('*', count='exact').eq('teacher_id', teacher['id']).execute()

                    teachers_list.append({
                        'ID': teacher['id'],
                        'Prénom': teacher['first_name'],
                        'Nom': teacher['last_name'],
                        'Email': teacher['email'],
                        'Groupes': groups.count
                    })

                df = pd.DataFrame(teachers_list)
                st.dataframe(df, width="stretch", hide_index=True)

                st.metric("Total Enseignants", len(teachers_list))

                # Détails des enseignants
                st.divider()
                st.subheader("Détails et Actions")

                for teacher in teachers_response.data:
                    with st.expander(f"{teacher['first_name']} {teacher['last_name']}"):
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            st.write(f"**Email:** {teacher['email']}")

                            # Afficher les groupes
                            group_teacher = supabase.table('group_teacher').select('*, groups(name, level, mode, languages(name))').eq('teacher_id', teacher['id']).execute()

                            if group_teacher.data:
                                st.markdown("**Groupes assignés:**")
                                for gt in group_teacher.data:
                                    group = gt.get('groups', {})
                                    lang_name = group.get('languages', {}).get('name', 'N/A') if group.get('languages') else 'N/A'
                                    st.write(f"- {group.get('name', 'N/A')} ({lang_name}, Niveau {group.get('level', 'N/A')}, {group.get('mode', 'N/A')})")
                            else:
                                st.info("Aucun groupe assigné")

                        with col2:
                            if st.button("Supprimer", key=f"delete_{teacher['id']}", type="primary"):
                                try:
                                    supabase.table('teachers').delete().eq('id', teacher['id']).execute()
                                    st.success("Enseignant supprimé")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erreur : {str(e)}")

            else:
                st.info("Aucun enseignant enregistré")

        except Exception as e:
            st.error(f"Erreur lors du chargement des enseignants : {str(e)}")

    with tab2:
        st.subheader("Ajouter un Nouvel Enseignant")

        with st.form("add_teacher_form"):
            first_name = st.text_input("Prénom *")
            last_name = st.text_input("Nom *")
            email = st.text_input("Email *")

            st.markdown("*Les champs marqués d'un astérisque sont obligatoires*")

            submitted = st.form_submit_button("Ajouter l'enseignant", width="stretch")

            if submitted:
                if first_name and last_name and email:
                    try:
                        # Vérifier si l'email existe déjà
                        existing = supabase.table('teachers').select('*').eq('email', email).execute()

                        if existing.data:
                            st.error("Un enseignant avec cet email existe déjà")
                        else:
                            # Insérer le nouvel enseignant
                            new_teacher = {
                                'first_name': first_name,
                                'last_name': last_name,
                                'email': email
                            }

                            response = supabase.table('teachers').insert(new_teacher).execute()

                            if response.data:
                                st.success("✅ Enseignant ajouté avec succès!")
                                st.rerun()
                            else:
                                st.error("Erreur lors de l'ajout de l'enseignant")

                    except Exception as e:
                        st.error(f"Erreur : {str(e)}")
                else:
                    st.warning("Veuillez remplir tous les champs obligatoires")
