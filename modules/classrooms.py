import streamlit as st
import pandas as pd
from utils import get_supabase_client

def show():
    st.title("🏫 Gestion des Salles")

    supabase = get_supabase_client()

    tab1, tab2 = st.tabs(["📋 Liste", "➕ Ajouter"])

    with tab1:
        st.subheader("Liste des Salles")

        try:
            classrooms_response = supabase.table('classrooms').select('*').order('name').execute()

            if classrooms_response.data:
                classrooms_list = []
                for classroom in classrooms_response.data:
                    # Compter les cours assignés
                    schedules = supabase.table('schedule').select('*', count='exact').eq('classroom_id', classroom['id']).execute()

                    classrooms_list.append({
                        'ID': classroom['id'],
                        'Nom': classroom['name'],
                        'Localisation': classroom.get('location', 'N/A'),
                        'Capacité': classroom.get('capacity', 'N/A'),
                        'Équipements': classroom.get('equipments', 'N/A'),
                        'Cours': schedules.count
                    })

                df = pd.DataFrame(classrooms_list)
                st.dataframe(df, width="stretch", hide_index=True)

                st.metric("Total Salles", len(classrooms_list))

                # Détails des salles
                st.divider()
                st.subheader("Détails et Actions")

                for classroom in classrooms_response.data:
                    with st.expander(f"{classroom['name']} - {classroom.get('location', 'N/A')}"):
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            st.write(f"**Localisation:** {classroom.get('location', 'N/A')}")
                            st.write(f"**Capacité:** {classroom.get('capacity', 'N/A')} personnes")
                            st.write(f"**Équipements:** {classroom.get('equipments', 'N/A')}")

                            # Afficher le planning
                            schedules = supabase.table('schedule').select('*, groups(name, languages(name))').eq('classroom_id', classroom['id']).execute()

                            if schedules.data:
                                st.markdown("**Planning:**")
                                for sch in schedules.data:
                                    group = sch.get('groups', {})
                                    lang_name = group.get('languages', {}).get('name', 'N/A') if group.get('languages') else 'N/A'
                                    st.write(f"- {sch['day_of_week']}: {sch['start_time']} - {sch['end_time']} | {group.get('name', 'N/A')} ({lang_name})")
                            else:
                                st.info("Aucun cours planifié")

                        with col2:
                            if st.button("Supprimer", key=f"delete_{classroom['id']}", type="primary"):
                                try:
                                    supabase.table('classrooms').delete().eq('id', classroom['id']).execute()
                                    st.success("Salle supprimée")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erreur : {str(e)}")

            else:
                st.info("Aucune salle enregistrée")

        except Exception as e:
            st.error(f"Erreur lors du chargement des salles : {str(e)}")

    with tab2:
        st.subheader("Ajouter une Nouvelle Salle")

        with st.form("add_classroom_form"):
            name = st.text_input("Nom de la salle *")
            location = st.text_input("Localisation")
            capacity = st.number_input("Capacité (nombre de places)", min_value=1, value=20)
            equipments = st.text_area("Équipements (ex: projecteur, tableau blanc, wifi...)")

            st.markdown("*Les champs marqués d'un astérisque sont obligatoires*")

            submitted = st.form_submit_button("Ajouter la salle", width="stretch")

            if submitted:
                if name:
                    try:
                        # Vérifier si le nom existe déjà
                        existing = supabase.table('classrooms').select('*').eq('name', name).execute()

                        if existing.data:
                            st.error("Une salle avec ce nom existe déjà")
                        else:
                            # Insérer la nouvelle salle
                            new_classroom = {
                                'name': name,
                                'location': location if location else None,
                                'capacity': capacity,
                                'equipments': equipments if equipments else None
                            }

                            response = supabase.table('classrooms').insert(new_classroom).execute()

                            if response.data:
                                st.success("✅ Salle ajoutée avec succès!")
                                st.rerun()
                            else:
                                st.error("Erreur lors de l'ajout de la salle")

                    except Exception as e:
                        st.error(f"Erreur : {str(e)}")
                else:
                    st.warning("Veuillez remplir le nom de la salle")
