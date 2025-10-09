import streamlit as st
import pandas as pd
from utils import get_supabase_client
from datetime import datetime, time

DAYS_OF_WEEK = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']

def show():
    st.title("📅 Gestion du Planning")

    supabase = get_supabase_client()

    # Affichage différent selon le rôle
    if st.session_state.user_role == "teacher":
        show_teacher_schedule(supabase)
    else:
        show_admin_schedule(supabase)

def show_teacher_schedule(supabase):
    """Planning pour les enseignants"""
    st.subheader(f"Mon Planning - {st.session_state.user_name}")

    try:
        teacher_id = st.session_state.get('teacher_id')

        if not teacher_id:
            st.error("Impossible de récupérer votre identifiant enseignant")
            return

        # Récupérer les groupes de l'enseignant
        group_teacher = supabase.table('group_teacher').select('group_id').eq('teacher_id', teacher_id).execute()

        if group_teacher.data:
            group_ids = [gt['group_id'] for gt in group_teacher.data]

            # Récupérer les plannings
            schedules = supabase.table('schedule').select(
                '*, groups(name, level, mode, languages(name)), classrooms(name, location)'
            ).in_('group_id', group_ids).execute()

            if schedules.data:
                # Créer un planning par jour
                for day in DAYS_OF_WEEK:
                    day_schedules = [s for s in schedules.data if s['day_of_week'] == day]

                    if day_schedules:
                        with st.expander(f"**{day}** ({len(day_schedules)} cours)", expanded=True):
                            for sch in sorted(day_schedules, key=lambda x: x['start_time']):
                                group = sch.get('groups', {})
                                classroom = sch.get('classrooms', {})
                                lang_name = group.get('languages', {}).get('name', 'N/A') if group.get('languages') else 'N/A'

                                col1, col2, col3 = st.columns([2, 2, 1])

                                with col1:
                                    st.write(f"**{sch['start_time']} - {sch['end_time']}**")
                                    st.write(f"{group.get('name', 'N/A')} ({lang_name})")

                                with col2:
                                    st.write(f"📍 {classroom.get('name', 'N/A')}")
                                    st.write(f"Mode: {group.get('mode', 'N/A')}")

                                with col3:
                                    st.write(f"Niveau {group.get('level', 'N/A')}")

                                st.divider()
            else:
                st.info("Aucun cours planifié pour le moment")
        else:
            st.info("Vous n'êtes assigné à aucun groupe")

    except Exception as e:
        st.error(f"Erreur : {str(e)}")

def show_admin_schedule(supabase):
    """Planning pour les administrateurs"""
    tab1, tab2, tab3 = st.tabs(["📋 Vue Générale", "➕ Ajouter un Cours", "🔍 Filtrer"])

    with tab1:
        st.subheader("Planning Général")

        try:
            schedules_response = supabase.table('schedule').select(
                '*, groups(name, level, mode, languages(name)), classrooms(name, location)'
            ).execute()

            if schedules_response.data:
                # Organiser par jour
                for day in DAYS_OF_WEEK:
                    day_schedules = [s for s in schedules_response.data if s['day_of_week'] == day]

                    if day_schedules:
                        with st.expander(f"**{day}** ({len(day_schedules)} cours)", expanded=False):
                            for sch in sorted(day_schedules, key=lambda x: x['start_time']):
                                group = sch.get('groups', {})
                                classroom = sch.get('classrooms', {})
                                lang_name = group.get('languages', {}).get('name', 'N/A') if group.get('languages') else 'N/A'

                                col1, col2, col3, col4 = st.columns([1, 2, 2, 1])

                                with col1:
                                    st.write(f"**{sch['start_time']} - {sch['end_time']}**")

                                with col2:
                                    st.write(f"{group.get('name', 'N/A')} ({lang_name}, Niveau {group.get('level', 'N/A')})")

                                with col3:
                                    st.write(f"📍 {classroom.get('name', 'N/A')} - {classroom.get('location', 'N/A')}")

                                with col4:
                                    if st.button("🗑️", key=f"delete_{sch['id']}"):
                                        try:
                                            supabase.table('schedule').delete().eq('id', sch['id']).execute()
                                            st.success("Cours supprimé")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erreur : {str(e)}")

                                st.divider()

                # Statistiques
                st.divider()
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Total Cours Planifiés", len(schedules_response.data))

                with col2:
                    groups = set([s['group_id'] for s in schedules_response.data])
                    st.metric("Groupes avec Planning", len(groups))

                with col3:
                    classrooms = set([s['classroom_id'] for s in schedules_response.data if s.get('classroom_id')])
                    st.metric("Salles Utilisées", len(classrooms))

            else:
                st.info("Aucun cours planifié")

        except Exception as e:
            st.error(f"Erreur : {str(e)}")

    with tab2:
        st.subheader("Ajouter un Cours au Planning")

        with st.form("add_schedule_form"):
            # Sélectionner le groupe
            try:
                groups = supabase.table('groups').select('*, languages(name)').execute()
                if groups.data:
                    group_options = {f"{g['name']} ({g['languages']['name'] if g.get('languages') else 'N/A'}, Niveau {g['level']})": g for g in groups.data}
                    selected_group = st.selectbox("Groupe *", list(group_options.keys()))
                else:
                    st.error("Aucun groupe disponible")
                    selected_group = None
            except Exception as e:
                st.error(f"Erreur : {str(e)}")
                selected_group = None

            # Sélectionner la salle
            try:
                classrooms = supabase.table('classrooms').select('*').execute()
                if classrooms.data:
                    classroom_options = {f"{c['name']} ({c.get('location', 'N/A')}) - Capacité: {c.get('capacity', 'N/A')}": c for c in classrooms.data}
                    selected_classroom = st.selectbox("Salle *", list(classroom_options.keys()))
                else:
                    st.error("Aucune salle disponible")
                    selected_classroom = None
            except Exception as e:
                st.error(f"Erreur : {str(e)}")
                selected_classroom = None

            day_of_week = st.selectbox("Jour de la semaine *", DAYS_OF_WEEK)

            col1, col2 = st.columns(2)

            with col1:
                start_time = st.time_input("Heure de début *", value=time(9, 0))

            with col2:
                end_time = st.time_input("Heure de fin *", value=time(11, 0))

            st.markdown("*Les champs marqués d'un astérisque sont obligatoires*")

            submitted = st.form_submit_button("Ajouter au planning", width="stretch")

            if submitted:
                if selected_group and selected_classroom and day_of_week and start_time and end_time:
                    if end_time <= start_time:
                        st.error("L'heure de fin doit être après l'heure de début")
                    else:
                        try:
                            group_data = group_options[selected_group]
                            classroom_data = classroom_options[selected_classroom]

                            # Vérifier les conflits de salle
                            existing = supabase.table('schedule').select('*').eq('classroom_id', classroom_data['id']).eq('day_of_week', day_of_week).execute()

                            has_conflict = False
                            for sch in existing.data:
                                existing_start = datetime.strptime(sch['start_time'], '%H:%M:%S').time()
                                existing_end = datetime.strptime(sch['end_time'], '%H:%M:%S').time()

                                # Vérifier si les horaires se chevauchent
                                if not (end_time <= existing_start or start_time >= existing_end):
                                    has_conflict = True
                                    break

                            if has_conflict:
                                st.error("⚠️ Conflit d'horaire : cette salle est déjà occupée à cet horaire")
                            else:
                                # Créer le planning
                                new_schedule = {
                                    'group_id': group_data['id'],
                                    'classroom_id': classroom_data['id'],
                                    'day_of_week': day_of_week,
                                    'start_time': start_time.strftime('%H:%M:%S'),
                                    'end_time': end_time.strftime('%H:%M:%S')
                                }

                                response = supabase.table('schedule').insert(new_schedule).execute()

                                if response.data:
                                    st.success("✅ Cours ajouté au planning avec succès!")
                                    st.rerun()
                                else:
                                    st.error("Erreur lors de l'ajout du cours")

                        except Exception as e:
                            st.error(f"Erreur : {str(e)}")
                else:
                    st.warning("Veuillez remplir tous les champs obligatoires")

    with tab3:
        st.subheader("Filtrer le Planning")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Filtrer par enseignant
            try:
                teachers = supabase.table('teachers').select('*').execute()
                if teachers.data:
                    teacher_options = ["Tous"] + [f"{t['first_name']} {t['last_name']}" for t in teachers.data]
                    selected_teacher = st.selectbox("Enseignant", teacher_options)
                else:
                    selected_teacher = "Tous"
            except:
                selected_teacher = "Tous"

        with col2:
            # Filtrer par groupe
            try:
                groups = supabase.table('groups').select('*').execute()
                if groups.data:
                    group_filter_options = ["Tous"] + [g['name'] for g in groups.data]
                    selected_group_filter = st.selectbox("Groupe", group_filter_options)
                else:
                    selected_group_filter = "Tous"
            except:
                selected_group_filter = "Tous"

        with col3:
            # Filtrer par salle
            try:
                classrooms = supabase.table('classrooms').select('*').execute()
                if classrooms.data:
                    classroom_filter_options = ["Toutes"] + [c['name'] for c in classrooms.data]
                    selected_classroom_filter = st.selectbox("Salle", classroom_filter_options)
                else:
                    selected_classroom_filter = "Toutes"
            except:
                selected_classroom_filter = "Toutes"

        # Afficher les résultats filtrés
        try:
            schedules = supabase.table('schedule').select(
                '*, groups(name, level, mode, languages(name)), classrooms(name, location)'
            ).execute()

            filtered_schedules = schedules.data

            # Appliquer les filtres
            if selected_group_filter != "Tous":
                filtered_schedules = [s for s in filtered_schedules if s.get('groups', {}).get('name') == selected_group_filter]

            if selected_classroom_filter != "Toutes":
                filtered_schedules = [s for s in filtered_schedules if s.get('classrooms', {}).get('name') == selected_classroom_filter]

            if selected_teacher != "Tous":
                # Récupérer les groupes de l'enseignant
                teacher = [t for t in teachers.data if f"{t['first_name']} {t['last_name']}" == selected_teacher]
                if teacher:
                    group_teacher = supabase.table('group_teacher').select('group_id').eq('teacher_id', teacher[0]['id']).execute()
                    teacher_group_ids = [gt['group_id'] for gt in group_teacher.data]
                    filtered_schedules = [s for s in filtered_schedules if s['group_id'] in teacher_group_ids]

            if filtered_schedules:
                st.divider()
                st.subheader(f"Résultats ({len(filtered_schedules)} cours)")

                # Créer un DataFrame
                schedule_list = []
                for sch in filtered_schedules:
                    group = sch.get('groups', {})
                    classroom = sch.get('classrooms', {})
                    lang_name = group.get('languages', {}).get('name', 'N/A') if group.get('languages') else 'N/A'

                    schedule_list.append({
                        'Jour': sch['day_of_week'],
                        'Heure': f"{sch['start_time']} - {sch['end_time']}",
                        'Groupe': group.get('name', 'N/A'),
                        'Langue': lang_name,
                        'Niveau': group.get('level', 'N/A'),
                        'Salle': classroom.get('name', 'N/A'),
                        'Localisation': classroom.get('location', 'N/A')
                    })

                df = pd.DataFrame(schedule_list)
                st.dataframe(df, width="stretch", hide_index=True)
            else:
                st.info("Aucun cours ne correspond aux filtres sélectionnés")

        except Exception as e:
            st.error(f"Erreur : {str(e)}")
