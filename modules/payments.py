import streamlit as st
import pandas as pd
from utils import get_supabase_client
from datetime import datetime

# Tarifs des cours
COURSE_FEES = {
    'Japonais': {
        # Anciens tarifs
        'online_group_old': 12000,
        'online_individual_old': 1500,  # par heure
        'presential_group_old': 12000,
        'presential_individual_old': 1500,  # par heure
        # Nouveaux tarifs
        'online_group': 16000,
        'online_individual': 2000,  # par heure
        'presential_group': 16000,
        'presential_individual': 2000  # par heure
    },
    'Chinois': {
        # Anciens tarifs
        'online_group_old': 15000,
        'online_individual_old': 2000,
        'presential_group_old': 15000,
        'presential_individual_old': 2000,
        # Nouveaux tarifs
        'online_group': 20000,
        'online_individual': 3000,
        'presential_group': 20000,
        'presential_individual': 3000
    },
    'Coréen': {
        # Anciens tarifs
        'online_group_old': 16000,
        'online_individual_old': 1500,
        'presential_group_old': 16000,
        'presential_individual_old': 1500,
        # Nouveaux tarifs
        'online_group': 15000,
        'online_individual': 2000,
        'presential_group': 15000,
        'presential_individual': 2000
    }
}

INSCRIPTION_FEE = 1000

def calculate_course_fee(language, mode, duration_months=3, hours=10):
    """Calcule les frais de cours selon la langue et le mode"""
    if language not in COURSE_FEES:
        return 0

    if 'individual' in mode:
        # Pour les cours individuels, on calcule par heure
        return COURSE_FEES[language][mode] * hours
    else:
        # Pour les cours en groupe, tarif mensuel multiplié par la durée
        return COURSE_FEES[language][mode] * duration_months

def show():
    st.title("💰 Gestion des Paiements")

    supabase = get_supabase_client()

    tab1, tab2, tab3 = st.tabs(["📋 Inscriptions & Paiements", "➕ Nouvelle Inscription", "💳 Enregistrer un Paiement"])

    with tab1:
        st.subheader("Liste des Inscriptions et Paiements")

        try:
            enrollments_response = supabase.table('enrollments').select(
                '*, students(first_name, last_name, email, student_code), groups(name, mode, duration_months, languages(name))'
            ).order('enrollment_date', desc=True).execute()

            if enrollments_response.data:
                enrollments_list = []

                for enr in enrollments_response.data:
                    student = enr.get('students', {})
                    group = enr.get('groups', {})
                    lang_name = group.get('languages', {}).get('name', 'N/A') if group.get('languages') else 'N/A'

                    # Calculer le total payé
                    payments = supabase.table('payments').select('amount').eq('student_id', enr['student_id']).execute()
                    total_paid = sum([p['amount'] for p in payments.data]) if payments.data else 0

                    remaining = enr['total_course_fee'] - total_paid
                    status = "✅ Active" if enr['enrollment_active'] else "❌ Inactive"

                    enrollments_list.append({
                        'ID': enr['id'],
                        'Étudiant': f"{student.get('first_name', 'N/A')} {student.get('last_name', 'N/A')}",
                        'Code': student.get('student_code', 'N/A'),
                        'Groupe': group.get('name', 'N/A'),
                        'Langue': lang_name,
                        'Niveau': enr['level'],
                        'Total Cours': f"{enr['total_course_fee']:,.0f} DA",
                        'Payé': f"{total_paid:,.0f} DA",
                        'Restant': f"{remaining:,.0f} DA",
                        'Statut': status,
                        'Date': enr.get('enrollment_date', 'N/A')
                    })

                df = pd.DataFrame(enrollments_list)
                st.dataframe(df, width="stretch", hide_index=True)

                # Statistiques
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Inscriptions", len(enrollments_list))
                with col2:
                    active_count = len([e for e in enrollments_list if '✅' in e['Statut']])
                    st.metric("Inscriptions Actives", active_count)
                with col3:
                    total_revenue = sum([enr['total_course_fee'] for enr in enrollments_response.data])
                    st.metric("Revenu Total", f"{total_revenue:,.0f} DA")
                with col4:
                    all_payments = supabase.table('payments').select('amount').execute()
                    total_received = sum([p['amount'] for p in all_payments.data]) if all_payments.data else 0
                    st.metric("Total Encaissé", f"{total_received:,.0f} DA")

                # Détails des inscriptions
                st.divider()
                st.subheader("Détails")

                for enr in enrollments_response.data:
                    student = enr.get('students', {})
                    group = enr.get('groups', {})
                    lang_name = group.get('languages', {}).get('name', 'N/A') if group.get('languages') else 'N/A'

                    with st.expander(f"{student.get('first_name', 'N/A')} {student.get('last_name', 'N/A')} - {group.get('name', 'N/A')}"):
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            st.write(f"**Code Étudiant:** {student.get('student_code', 'N/A')}")
                            st.write(f"**Groupe:** {group.get('name', 'N/A')} ({lang_name})")
                            st.write(f"**Niveau:** {enr['level']}")
                            st.write(f"**Mode:** {group.get('mode', 'N/A')}")
                            st.write(f"**Total Cours:** {enr['total_course_fee']:,.0f} DA")

                            # Historique des paiements
                            payments = supabase.table('payments').select('*').eq('student_id', enr['student_id']).order('payment_date', desc=True).execute()

                            if payments.data:
                                total_paid = sum([p['amount'] for p in payments.data])
                                remaining = enr['total_course_fee'] - total_paid

                                st.write(f"**Total Payé:** {total_paid:,.0f} DA")
                                st.write(f"**Restant:** {remaining:,.0f} DA")

                                st.markdown("**Historique des paiements:**")
                                for payment in payments.data:
                                    date = payment.get('payment_date', 'N/A')
                                    if date != 'N/A':
                                        date = datetime.fromisoformat(date.replace('Z', '+00:00')).strftime('%d/%m/%Y %H:%M')
                                    receipt = payment.get('receipt_link')
                                    receipt_text = f" - [📄 Reçu]({receipt})" if receipt else ""
                                    st.write(f"- {payment['amount']:,.0f} DA le {date}{receipt_text}")
                            else:
                                st.warning("Aucun paiement enregistré")

                        with col2:
                            status_icon = "✅" if enr['enrollment_active'] else "❌"
                            st.write(f"**Statut:** {status_icon}")

                            if st.button("Supprimer", key=f"delete_enr_{enr['id']}", type="primary"):
                                try:
                                    supabase.table('enrollments').delete().eq('id', enr['id']).execute()
                                    st.success("Inscription supprimée")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erreur : {str(e)}")

            else:
                st.info("Aucune inscription enregistrée")

        except Exception as e:
            st.error(f"Erreur : {str(e)}")

    with tab2:
        st.subheader("Nouvelle Inscription")

        with st.form("new_enrollment_form"):
            # Sélectionner l'étudiant
            try:
                students = supabase.table('students').select('*').order('created_at', desc=True).execute()
                if students.data:
                    student_options = {f"{s['first_name']} {s['last_name']} ({s.get('student_code', 'N/A')})": s for s in students.data}
                    selected_student = st.selectbox("Étudiant *", list(student_options.keys()))
                else:
                    st.error("Aucun étudiant disponible")
                    selected_student = None
            except Exception as e:
                st.error(f"Erreur : {str(e)}")
                selected_student = None

            # Sélectionner le groupe
            try:
                groups = supabase.table('groups').select('*, languages(name)').execute()
                if groups.data:
                    group_options = {f"{g['name']} ({g['languages']['name'] if g.get('languages') else 'N/A'}, {g['mode']})": g for g in groups.data}
                    selected_group = st.selectbox("Groupe *", list(group_options.keys()))
                else:
                    st.error("Aucun groupe disponible")
                    selected_group = None
            except Exception as e:
                st.error(f"Erreur : {str(e)}")
                selected_group = None

            level = st.number_input("Niveau *", min_value=1, value=1)

            # Calculer automatiquement les frais
            if selected_group:
                group_data = group_options[selected_group]
                lang_name = group_data['languages']['name'] if group_data.get('languages') else 'Japonais'
                mode = group_data['mode']
                duration = group_data['duration_months']

                if 'individual' in mode:
                    hours = st.number_input("Nombre d'heures", min_value=1, value=10)
                    course_fee = calculate_course_fee(lang_name, mode, duration, hours)
                else:
                    course_fee = calculate_course_fee(lang_name, mode, duration)

                total_fee = course_fee + INSCRIPTION_FEE

                st.info(f"**Frais de cours:** {course_fee:,.0f} DA + **Frais d'inscription:** {INSCRIPTION_FEE:,.0f} DA = **Total:** {total_fee:,.0f} DA")

                # Pour les cours individuels en ligne, paiement intégral requis
                if 'individual' in mode and 'online' in mode:
                    st.warning("⚠️ Les cours en ligne individuels nécessitent un paiement intégral pour activer l'inscription.")
                    payment_amount = total_fee
                else:
                    st.info("💡 Pour les cours en groupe, le premier paiement doit inclure au moins la mensualité + frais d'inscription.")
                    min_payment = (course_fee / duration) + INSCRIPTION_FEE
                    payment_amount = st.number_input(f"Montant du premier paiement (minimum {min_payment:,.0f} DA) *",
                                                     min_value=min_payment, value=min_payment, step=1000.0)
            else:
                total_fee = 0
                payment_amount = 0

            st.markdown("*Les champs marqués d'un astérisque sont obligatoires*")

            submitted = st.form_submit_button("Créer l'inscription", width="stretch")

            if submitted:
                if selected_student and selected_group:
                    try:
                        student_data = student_options[selected_student]
                        group_data = group_options[selected_group]

                        # Créer l'inscription
                        enrollment_active = False

                        # Vérifier les conditions d'activation
                        mode = group_data['mode']
                        if 'individual' in mode and 'online' in mode:
                            # Paiement intégral requis pour cours individuels en ligne
                            if payment_amount >= total_fee:
                                enrollment_active = True
                        else:
                            # Premier paiement doit couvrir mensualité + inscription
                            min_payment = (course_fee / duration) + INSCRIPTION_FEE
                            if payment_amount >= min_payment:
                                enrollment_active = True

                        new_enrollment = {
                            'student_id': student_data['id'],
                            'group_id': group_data['id'],
                            'level': level,
                            'total_course_fee': total_fee,
                            'enrollment_active': enrollment_active
                        }

                        enr_response = supabase.table('enrollments').insert(new_enrollment).execute()

                        if enr_response.data:
                            # Enregistrer le premier paiement (sans lien de reçu lors de l'inscription initiale)
                            new_payment = {
                                'student_id': student_data['id'],
                                'amount': payment_amount,
                                'receipt_link': None
                            }

                            pay_response = supabase.table('payments').insert(new_payment).execute()

                            if pay_response.data:
                                status_msg = "activée" if enrollment_active else "créée (paiement insuffisant pour activation)"
                                st.success(f"✅ Inscription {status_msg} avec succès!")
                                st.rerun()
                            else:
                                st.error("Inscription créée mais erreur lors de l'enregistrement du paiement")
                        else:
                            st.error("Erreur lors de la création de l'inscription")

                    except Exception as e:
                        st.error(f"Erreur : {str(e)}")
                else:
                    st.warning("Veuillez sélectionner un étudiant et un groupe")

    with tab3:
        st.subheader("Enregistrer un Paiement")

        with st.form("add_payment_form"):
            # Sélectionner l'étudiant
            try:
                students = supabase.table('students').select('*').order('created_at', desc=True).execute()
                if students.data:
                    student_options = {f"{s['first_name']} {s['last_name']} ({s.get('student_code', 'N/A')})": s for s in students.data}
                    selected_student = st.selectbox("Étudiant *", list(student_options.keys()), key="payment_student")

                    # Afficher le solde restant
                    if selected_student:
                        student_data = student_options[selected_student]
                        enrollments = supabase.table('enrollments').select('*').eq('student_id', student_data['id']).execute()

                        if enrollments.data:
                            total_due = sum([e['total_course_fee'] for e in enrollments.data])
                            payments = supabase.table('payments').select('amount').eq('student_id', student_data['id']).execute()
                            total_paid = sum([p['amount'] for p in payments.data]) if payments.data else 0
                            remaining = total_due - total_paid

                            if remaining > 0:
                                st.warning(f"💰 Montant restant: {remaining:,.0f} DA")
                            else:
                                st.success("✅ Tous les paiements sont à jour")
                else:
                    st.error("Aucun étudiant disponible")
                    selected_student = None
            except Exception as e:
                st.error(f"Erreur : {str(e)}")
                selected_student = None

            amount = st.number_input("Montant du paiement (DA) *", min_value=100.0, step=100.0)
            receipt_link = st.text_input("Lien du reçu (URL)")

            st.markdown("*Les champs marqués d'un astérisque sont obligatoires*")

            submitted = st.form_submit_button("Enregistrer le paiement", width="stretch")

            if submitted:
                if selected_student and amount > 0:
                    try:
                        student_data = student_options[selected_student]

                        # Enregistrer le paiement
                        new_payment = {
                            'student_id': student_data['id'],
                            'amount': amount,
                            'receipt_link': receipt_link if receipt_link else None
                        }

                        response = supabase.table('payments').insert(new_payment).execute()

                        if response.data:
                            # Vérifier si on doit activer des inscriptions
                            enrollments = supabase.table('enrollments').select('*, groups(mode, duration_months)').eq('student_id', student_data['id']).eq('enrollment_active', False).execute()

                            for enr in enrollments.data:
                                # Recalculer le total payé
                                payments = supabase.table('payments').select('amount').eq('student_id', student_data['id']).execute()
                                total_paid = sum([p['amount'] for p in payments.data]) if payments.data else 0

                                group = enr.get('groups', {})
                                mode = group.get('mode', '')

                                should_activate = False

                                if 'individual' in mode and 'online' in mode:
                                    # Vérifier si paiement intégral pour cours individuels en ligne
                                    if total_paid >= enr['total_course_fee']:
                                        should_activate = True
                                else:
                                    # Vérifier si minimum atteint
                                    course_fee = enr['total_course_fee'] - INSCRIPTION_FEE
                                    duration = group.get('duration_months', 3)
                                    min_payment = (course_fee / duration) + INSCRIPTION_FEE
                                    if total_paid >= min_payment:
                                        should_activate = True

                                if should_activate:
                                    supabase.table('enrollments').update({'enrollment_active': True}).eq('id', enr['id']).execute()

                            st.success("✅ Paiement enregistré avec succès!")
                            st.rerun()
                        else:
                            st.error("Erreur lors de l'enregistrement du paiement")

                    except Exception as e:
                        st.error(f"Erreur : {str(e)}")
                else:
                    st.warning("Veuillez sélectionner un étudiant et saisir un montant")
