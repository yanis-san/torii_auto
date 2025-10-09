import streamlit as st
import pandas as pd
from utils import get_supabase_client
from datetime import datetime

def show():
    st.title("📊 Dashboard")

    supabase = get_supabase_client()

    # Filtres
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        try:
            languages_response = supabase.table('languages').select('*').execute()
            languages = ["Toutes"] + [lang['name'] for lang in languages_response.data] if languages_response.data else ["Toutes"]
        except:
            languages = ["Toutes"]
        selected_language = st.selectbox("Langue", languages)

    with col2:
        years = ["Toutes"] + list(range(datetime.now().year - 5, datetime.now().year + 2))
        selected_year = st.selectbox("Année", years)

    with col3:
        modes = ["Tous", "online_group", "online_individual", "presential_group", "presential_individual"]
        selected_mode = st.selectbox("Mode", modes)

    with col4:
        levels = ["Tous", "1", "2", "3", "4", "5"]
        selected_level = st.selectbox("Niveau", levels)

    st.divider()

    # KPIs principaux
    col1, col2, col3, col4 = st.columns(4)

    try:
        # Total étudiants
        students_response = supabase.table('students').select('*', count='exact').execute()
        total_students = students_response.count

        # Total paiements
        payments_response = supabase.table('payments').select('amount').execute()
        total_payments = sum([p['amount'] for p in payments_response.data]) if payments_response.data else 0

        # Groupes actifs
        groups_response = supabase.table('groups').select('*', count='exact').execute()
        total_groups = groups_response.count

        # Inscriptions actives
        enrollments_response = supabase.table('enrollments').select('*', count='exact').eq('enrollment_active', True).execute()
        active_enrollments = enrollments_response.count

        with col1:
            st.metric("Total Étudiants", total_students)

        with col2:
            st.metric("Paiements Reçus", f"{total_payments:,.0f} DA")

        with col3:
            st.metric("Groupes", total_groups)

        with col4:
            st.metric("Inscriptions Actives", active_enrollments)

    except Exception as e:
        st.error(f"Erreur lors du chargement des statistiques : {str(e)}")

    st.divider()

    # Statistiques détaillées
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📚 Étudiants par Langue")
        try:
            # Récupérer les inscriptions avec les langues
            query = """
                SELECT l.name, COUNT(DISTINCT e.student_id) as count
                FROM enrollments e
                JOIN groups g ON e.group_id = g.id
                JOIN languages l ON g.language_id = l.id
                WHERE e.enrollment_active = true
                GROUP BY l.name
            """
            enrollments_lang = supabase.table('enrollments').select('*, groups(*, languages(*))').eq('enrollment_active', True).execute()

            # Compter manuellement
            lang_count = {}
            for enr in enrollments_lang.data:
                if enr.get('groups') and enr['groups'].get('languages'):
                    lang_name = enr['groups']['languages']['name']
                    lang_count[lang_name] = lang_count.get(lang_name, 0) + 1

            if lang_count:
                df_lang = pd.DataFrame(list(lang_count.items()), columns=['Langue', 'Étudiants'])
                st.bar_chart(df_lang.set_index('Langue'))
            else:
                st.info("Aucune donnée disponible")
        except Exception as e:
            st.error(f"Erreur : {str(e)}")

    with col2:
        st.subheader("📊 Types de Cours")
        try:
            groups_data = supabase.table('groups').select('mode').execute()
            if groups_data.data:
                mode_count = {}
                for g in groups_data.data:
                    mode = g['mode']
                    mode_count[mode] = mode_count.get(mode, 0) + 1

                df_modes = pd.DataFrame(list(mode_count.items()), columns=['Mode', 'Groupes'])
                st.bar_chart(df_modes.set_index('Mode'))
            else:
                st.info("Aucune donnée disponible")
        except Exception as e:
            st.error(f"Erreur : {str(e)}")

    st.divider()

    # Groupes prêts à démarrer
    st.subheader("🚀 Groupes Prêts à Démarrer")
    try:
        groups = supabase.table('groups').select('*, languages(name)').execute()

        ready_groups = []
        for group in groups.data:
            # Compter les étudiants inscrits
            enrollments = supabase.table('enrollments').select('*', count='exact').eq('group_id', group['id']).eq('enrollment_active', True).execute()
            enrolled_count = enrollments.count

            if enrolled_count >= group['min_students']:
                ready_groups.append({
                    'Nom': group['name'],
                    'Langue': group['languages']['name'] if group.get('languages') else 'N/A',
                    'Niveau': group['level'],
                    'Mode': group['mode'],
                    'Inscrits': enrolled_count,
                    'Minimum': group['min_students']
                })

        if ready_groups:
            df_ready = pd.DataFrame(ready_groups)
            st.dataframe(df_ready, width="stretch")
        else:
            st.info("Aucun groupe prêt pour le moment")
    except Exception as e:
        st.error(f"Erreur : {str(e)}")

    st.divider()

    # Étudiants avec paiement restant
    st.subheader("💳 Étudiants avec Paiement Restant")
    try:
        enrollments = supabase.table('enrollments').select('*, students(first_name, last_name, email)').execute()

        debt_list = []
        for enr in enrollments.data:
            # Calculer les paiements effectués
            payments = supabase.table('payments').select('amount').eq('student_id', enr['student_id']).execute()
            total_paid = sum([p['amount'] for p in payments.data]) if payments.data else 0

            remaining = enr['total_course_fee'] - total_paid

            if remaining > 0:
                student = enr.get('students', {})
                debt_list.append({
                    'Étudiant': f"{student.get('first_name', 'N/A')} {student.get('last_name', 'N/A')}",
                    'Email': student.get('email', 'N/A'),
                    'Total Cours': f"{enr['total_course_fee']:,.0f} DA",
                    'Payé': f"{total_paid:,.0f} DA",
                    'Restant': f"{remaining:,.0f} DA"
                })

        if debt_list:
            df_debt = pd.DataFrame(debt_list)
            st.dataframe(df_debt, width="stretch")
        else:
            st.success("Tous les paiements sont à jour!")
    except Exception as e:
        st.error(f"Erreur : {str(e)}")
