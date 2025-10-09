import streamlit as st
import pandas as pd
from utils import get_supabase_client
from datetime import datetime, date, timedelta

def show():
    st.title("✅ Gestion des Présences")

    supabase = get_supabase_client()

    # Affichage différent selon le rôle
    if st.session_state.user_role == "teacher":
        show_teacher_attendance(supabase)
    else:
        show_admin_attendance(supabase)

def show_teacher_attendance(supabase):
    """Gestion des présences pour les enseignants"""
    st.subheader(f"Prendre les Présences - {st.session_state.user_name}")

    try:
        teacher_id = st.session_state.get('teacher_id')

        if not teacher_id:
            st.error("Impossible de récupérer votre identifiant enseignant")
            return

        # Récupérer les groupes de l'enseignant
        group_teacher = supabase.table('group_teacher').select('*, groups(name, level, languages(name))').eq('teacher_id', teacher_id).execute()

        if group_teacher.data:
            # Sélectionner le groupe
            group_options = {f"{gt['groups']['name']} ({gt['groups']['languages']['name'] if gt['groups'].get('languages') else 'N/A'}, Niveau {gt['groups']['level']})": gt['groups'] for gt in group_teacher.data if gt.get('groups')}
            selected_group = st.selectbox("Sélectionner un groupe", list(group_options.keys()))

            if selected_group:
                group_data = group_options[selected_group]

                # Sélectionner la date
                attendance_date = st.date_input("Date du cours", value=date.today())

                # Récupérer les étudiants inscrits
                enrollments = supabase.table('enrollments').select('*, students(first_name, last_name, student_code)').eq('group_id', group_data['id']).eq('enrollment_active', True).execute()

                if enrollments.data:
                    st.divider()
                    st.subheader(f"Liste de présence - {attendance_date.strftime('%d/%m/%Y')}")

                    # Vérifier si des présences existent déjà pour cette date
                    existing_attendance = {}
                    for enr in enrollments.data:
                        att = supabase.table('attendance').select('*').eq('enrollment_id', enr['id']).eq('date', attendance_date.isoformat()).execute()
                        if att.data:
                            existing_attendance[enr['id']] = att.data[0]

                    # Formulaire de présence
                    with st.form("attendance_form"):
                        attendance_data = {}

                        for enr in enrollments.data:
                            student = enr.get('students', {})
                            student_name = f"{student.get('first_name', 'N/A')} {student.get('last_name', 'N/A')} ({student.get('student_code', 'N/A')})"

                            # Si présence déjà enregistrée, utiliser cette valeur par défaut
                            default_value = existing_attendance.get(enr['id'], {}).get('present', False)

                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(student_name)
                            with col2:
                                present = st.checkbox("Présent", value=default_value, key=f"att_{enr['id']}")

                            attendance_data[enr['id']] = present

                        submitted = st.form_submit_button("Enregistrer les présences", width="stretch")

                        if submitted:
                            try:
                                success_count = 0
                                for enrollment_id, present in attendance_data.items():
                                    # Vérifier si présence existe déjà
                                    if enrollment_id in existing_attendance:
                                        # Mettre à jour
                                        supabase.table('attendance').update({'present': present}).eq('id', existing_attendance[enrollment_id]['id']).execute()
                                    else:
                                        # Insérer nouvelle présence
                                        new_attendance = {
                                            'enrollment_id': enrollment_id,
                                            'date': attendance_date.isoformat(),
                                            'present': present
                                        }
                                        supabase.table('attendance').insert(new_attendance).execute()

                                    success_count += 1

                                st.success(f"✅ Présences enregistrées avec succès pour {success_count} étudiants!")
                                st.rerun()

                            except Exception as e:
                                st.error(f"Erreur : {str(e)}")

                    # Afficher l'historique des présences pour ce groupe
                    st.divider()
                    st.subheader("Historique des Présences")

                    # Récupérer toutes les dates de présence
                    all_attendance = supabase.table('attendance').select('date').in_('enrollment_id', [e['id'] for e in enrollments.data]).execute()

                    if all_attendance.data:
                        dates = sorted(list(set([att['date'] for att in all_attendance.data])), reverse=True)

                        for att_date in dates[:10]:  # Afficher les 10 dernières dates
                            with st.expander(f"📅 {datetime.fromisoformat(att_date).strftime('%d/%m/%Y')}"):
                                for enr in enrollments.data:
                                    student = enr.get('students', {})
                                    att = supabase.table('attendance').select('*').eq('enrollment_id', enr['id']).eq('date', att_date).execute()

                                    if att.data:
                                        status = "✅ Présent" if att.data[0]['present'] else "❌ Absent"
                                        st.write(f"{student.get('first_name', 'N/A')} {student.get('last_name', 'N/A')}: {status}")
                    else:
                        st.info("Aucune présence enregistrée pour ce groupe")

                else:
                    st.info("Aucun étudiant inscrit dans ce groupe")

        else:
            st.info("Vous n'êtes assigné à aucun groupe")

    except Exception as e:
        st.error(f"Erreur : {str(e)}")

def show_admin_attendance(supabase):
    """Gestion des présences pour les administrateurs"""
    tab1, tab2, tab3 = st.tabs(["📋 Vue Générale", "✅ Prendre les Présences", "📊 Statistiques"])

    with tab1:
        st.subheader("Vue Générale des Présences")

        try:
            # Filtres
            col1, col2, col3 = st.columns(3)

            with col1:
                # Sélectionner le groupe
                groups = supabase.table('groups').select('*, languages(name)').execute()
                if groups.data:
                    group_options = ["Tous"] + [f"{g['name']} ({g['languages']['name'] if g.get('languages') else 'N/A'})" for g in groups.data]
                    selected_group = st.selectbox("Groupe", group_options)
                else:
                    selected_group = "Tous"

            with col2:
                # Sélectionner la date de début
                start_date = st.date_input("Date de début", value=date.today() - timedelta(days=30))

            with col3:
                # Sélectionner la date de fin
                end_date = st.date_input("Date de fin", value=date.today())

            st.divider()

            # Récupérer toutes les présences
            attendance_response = supabase.table('attendance').select(
                '*, enrollments(*, students(first_name, last_name, student_code), groups(name, languages(name)))'
            ).gte('date', start_date.isoformat()).lte('date', end_date.isoformat()).order('date', desc=True).execute()

            if attendance_response.data:
                # Filtrer par groupe si sélectionné
                filtered_attendance = attendance_response.data

                if selected_group != "Tous":
                    filtered_attendance = [
                        att for att in attendance_response.data
                        if att.get('enrollments', {}).get('groups', {}).get('name', '') in selected_group
                    ]

                if filtered_attendance:
                    # Créer un DataFrame
                    attendance_list = []
                    for att in filtered_attendance:
                        enrollment = att.get('enrollments', {})
                        student = enrollment.get('students', {})
                        group = enrollment.get('groups', {})
                        lang_name = group.get('languages', {}).get('name', 'N/A') if group.get('languages') else 'N/A'

                        attendance_list.append({
                            'Date': datetime.fromisoformat(att['date']).strftime('%d/%m/%Y'),
                            'Étudiant': f"{student.get('first_name', 'N/A')} {student.get('last_name', 'N/A')}",
                            'Code': student.get('student_code', 'N/A'),
                            'Groupe': group.get('name', 'N/A'),
                            'Langue': lang_name,
                            'Présent': '✅ Oui' if att['present'] else '❌ Non'
                        })

                    df = pd.DataFrame(attendance_list)
                    st.dataframe(df, width="stretch", hide_index=True)

                    # Statistiques rapides
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Total Présences", len(filtered_attendance))

                    with col2:
                        present_count = len([att for att in filtered_attendance if att['present']])
                        st.metric("Présents", present_count)

                    with col3:
                        absent_count = len([att for att in filtered_attendance if not att['present']])
                        st.metric("Absents", absent_count)

                else:
                    st.info("Aucune présence enregistrée pour ce groupe")
            else:
                st.info("Aucune présence enregistrée pour cette période")

        except Exception as e:
            st.error(f"Erreur : {str(e)}")

    with tab2:
        st.subheader("Prendre les Présences")

        # Sélectionner le groupe
        try:
            groups = supabase.table('groups').select('*, languages(name)').execute()
            if groups.data:
                group_options = {f"{g['name']} ({g['languages']['name'] if g.get('languages') else 'N/A'}, Niveau {g['level']})": g for g in groups.data}
                selected_group = st.selectbox("Sélectionner un groupe", list(group_options.keys()), key="admin_group")

                if selected_group:
                    group_data = group_options[selected_group]

                    # Sélectionner la date
                    attendance_date = st.date_input("Date du cours", value=date.today(), key="admin_date")

                    # Récupérer les étudiants inscrits
                    enrollments = supabase.table('enrollments').select('*, students(first_name, last_name, student_code)').eq('group_id', group_data['id']).eq('enrollment_active', True).execute()

                    if enrollments.data:
                        st.divider()

                        # Vérifier si des présences existent déjà
                        existing_attendance = {}
                        for enr in enrollments.data:
                            att = supabase.table('attendance').select('*').eq('enrollment_id', enr['id']).eq('date', attendance_date.isoformat()).execute()
                            if att.data:
                                existing_attendance[enr['id']] = att.data[0]

                        # Formulaire de présence
                        with st.form("admin_attendance_form"):
                            attendance_data = {}

                            for enr in enrollments.data:
                                student = enr.get('students', {})
                                student_name = f"{student.get('first_name', 'N/A')} {student.get('last_name', 'N/A')} ({student.get('student_code', 'N/A')})"

                                default_value = existing_attendance.get(enr['id'], {}).get('present', False)

                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.write(student_name)
                                with col2:
                                    present = st.checkbox("Présent", value=default_value, key=f"admin_att_{enr['id']}")

                                attendance_data[enr['id']] = present

                            submitted = st.form_submit_button("Enregistrer les présences", width="stretch")

                            if submitted:
                                try:
                                    for enrollment_id, present in attendance_data.items():
                                        if enrollment_id in existing_attendance:
                                            supabase.table('attendance').update({'present': present}).eq('id', existing_attendance[enrollment_id]['id']).execute()
                                        else:
                                            new_attendance = {
                                                'enrollment_id': enrollment_id,
                                                'date': attendance_date.isoformat(),
                                                'present': present
                                            }
                                            supabase.table('attendance').insert(new_attendance).execute()

                                    st.success("✅ Présences enregistrées avec succès!")
                                    st.rerun()

                                except Exception as e:
                                    st.error(f"Erreur : {str(e)}")

                    else:
                        st.info("Aucun étudiant inscrit dans ce groupe")

            else:
                st.error("Aucun groupe disponible")

        except Exception as e:
            st.error(f"Erreur : {str(e)}")

    with tab3:
        st.subheader("📊 Statistiques de Présence")

        try:
            # Taux de présence par étudiant
            students = supabase.table('students').select('*').execute()

            if students.data:
                student_stats = []

                for student in students.data:
                    # Récupérer toutes les présences de l'étudiant
                    enrollments = supabase.table('enrollments').select('id').eq('student_id', student['id']).execute()

                    if enrollments.data:
                        enrollment_ids = [e['id'] for e in enrollments.data]
                        attendance = supabase.table('attendance').select('*').in_('enrollment_id', enrollment_ids).execute()

                        if attendance.data:
                            total = len(attendance.data)
                            present = len([att for att in attendance.data if att['present']])
                            rate = (present / total * 100) if total > 0 else 0

                            student_stats.append({
                                'Étudiant': f"{student['first_name']} {student['last_name']}",
                                'Code': student.get('student_code', 'N/A'),
                                'Total Cours': total,
                                'Présent': present,
                                'Absent': total - present,
                                'Taux de Présence': f"{rate:.1f}%"
                            })

                if student_stats:
                    df_stats = pd.DataFrame(student_stats)
                    st.dataframe(df_stats, width="stretch", hide_index=True)

                    # Moyenne générale
                    avg_rate = sum([float(s['Taux de Présence'].replace('%', '')) for s in student_stats]) / len(student_stats)
                    st.metric("Taux de Présence Moyen", f"{avg_rate:.1f}%")
                else:
                    st.info("Aucune statistique disponible")

        except Exception as e:
            st.error(f"Erreur : {str(e)}")
