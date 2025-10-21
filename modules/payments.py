import streamlit as st
import pandas as pd
from utils import get_supabase_client
from datetime import datetime

# Tarifs des cours - Structure simplifiée
# is_old_pricing du groupe détermine si on utilise OLD ou NEW
COURSE_FEES = {
    'Japonais': {
        'OLD': {
            'online_group': 12000,
            'online_individual': 1500,  # par heure
            'presential_group': 12000,
            'presential_individual': 1500  # par heure
        },
        'NEW': {
            'online_group': 16000,
            'online_individual': 2000,  # par heure
            'presential_group': 16000,
            'presential_individual': 2000  # par heure
        }
    },
    'Chinois': {
        'OLD': {
            'online_group': 15000,
            'online_individual': 2000,
            'presential_group': 15000,
            'presential_individual': 2000
        },
        'NEW': {
            'online_group': 20000,
            'online_individual': 3000,
            'presential_group': 20000,
            'presential_individual': 3000
        }
    },
    'Coréen': {
        'OLD': {
            'online_group': 16000,
            'online_individual': 1500,
            'presential_group': 16000,
            'presential_individual': 1500
        },
        'NEW': {
            'online_group': 15000,
            'online_individual': 2000,
            'presential_group': 15000,
            'presential_individual': 2000
        }
    }
}

INSCRIPTION_FEE = 1000

def get_student_registration_status(supabase, student_id):
    """
    Vérifie si l'étudiant a déjà payé les frais d'inscription cette année académique.
    Lit le champ registration_fee_paid de la table students.

    Returns:
        bool: True si frais déjà payés cette année, False sinon
    """
    student = supabase.table('students').select('registration_fee_paid').eq('id', student_id).execute()

    if student.data and len(student.data) > 0:
        return student.data[0].get('registration_fee_paid', False)

    return False

def mark_registration_fee_as_paid(supabase, student_id):
    """
    Marque les frais d'inscription comme payés pour cet étudiant.
    """
    supabase.table('students').update({'registration_fee_paid': True}).eq('id', student_id).execute()

def calculate_course_fee(language, mode, is_old_pricing=False, hours=10):
    """
    Calcule les frais de cours selon la langue, le mode et la tarification.

    Args:
        language: Nom de la langue (Japonais, Chinois, Coréen)
        mode: Mode du cours (online_group, online_individual, presential_group, presential_individual)
        is_old_pricing: True pour ancienne tarification, False pour nouvelle
        hours: Nombre d'heures (uniquement pour cours individuels)

    Returns:
        float: Montant du cours en DA
    """
    if language not in COURSE_FEES:
        return 0

    # Déterminer la tarification
    pricing_type = 'OLD' if is_old_pricing else 'NEW'

    # Nettoyer le mode (enlever _old si présent pour compatibilité)
    clean_mode = mode.replace('_old', '')

    if pricing_type not in COURSE_FEES[language]:
        return 0

    if clean_mode not in COURSE_FEES[language][pricing_type]:
        return 0

    base_price = COURSE_FEES[language][pricing_type][clean_mode]

    if 'individual' in clean_mode:
        # Pour les cours individuels, on calcule par heure
        return base_price * hours
    else:
        # Pour les cours en groupe, tarif total
        return base_price

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

                    # Calculer le total payé pour CETTE inscription uniquement
                    payments = supabase.table('payments').select('amount').eq('enrollment_id', enr['id']).execute()
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
                st.dataframe(df, use_container_width=True, hide_index=True)

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
                    # Afficher les statistiques de paiements (liquide vs en ligne)
                    try:
                        # Paiements liquides en caisse
                        last_reset = supabase.table('cash_register_resets').select('reset_date, amount_left, reset_by').order('reset_date', desc=True).limit(1).execute()

                        if last_reset.data:
                            last_reset_date = last_reset.data[0]['reset_date']
                            amount_left_last_time = last_reset.data[0].get('amount_left', 0) or 0
                            last_reset_by = last_reset.data[0].get('reset_by', 'N/A')

                            # Compter UNIQUEMENT les paiements LIQUIDES depuis la dernière signature
                            cash_payments = supabase.table('payments').select('amount').gte('payment_date', last_reset_date).eq('payment_method', 'liquide').execute()
                            cash_total = sum([p['amount'] for p in cash_payments.data]) if cash_payments.data else 0

                            # Montant total en caisse = argent laissé + nouveaux paiements liquides
                            cash_register_amount = amount_left_last_time + cash_total

                            # Compter les paiements EN LIGNE depuis la dernière signature
                            online_payments = supabase.table('payments').select('amount').gte('payment_date', last_reset_date).eq('payment_method', 'en_ligne').execute()
                            online_total = sum([p['amount'] for p in online_payments.data]) if online_payments.data else 0

                            # Afficher la métrique caisse
                            reset_datetime = datetime.fromisoformat(last_reset_date.replace('Z', '+00:00'))
                            last_reset_text = reset_datetime.strftime('%d/%m/%Y')
                            st.metric("💵 Caisse (Liquide)", f"{cash_register_amount:,.0f} DA",
                                     delta=f"Dernier comptage: {last_reset_text}")
                        else:
                            # Pas de signature précédente
                            cash_payments = supabase.table('payments').select('amount').eq('payment_method', 'liquide').execute()
                            cash_register_amount = sum([p['amount'] for p in cash_payments.data]) if cash_payments.data else 0

                            online_payments = supabase.table('payments').select('amount').eq('payment_method', 'en_ligne').execute()
                            online_total = sum([p['amount'] for p in online_payments.data]) if online_payments.data else 0

                            st.metric("💵 Caisse (Liquide)", f"{cash_register_amount:,.0f} DA", delta="Aucun comptage")
                    except Exception as e:
                        st.metric("💵 Caisse", "Erreur", delta=str(e))

                # Deuxième ligne de métriques pour les paiements en ligne
                st.divider()
                col5, col6, col7, col8 = st.columns(4)
                with col5:
                    try:
                        # Total paiements en ligne
                        if 'online_total' in locals():
                            st.metric("💳 Paiements En Ligne", f"{online_total:,.0f} DA")
                        else:
                            online_payments = supabase.table('payments').select('amount').eq('payment_method', 'en_ligne').execute()
                            online_total = sum([p['amount'] for p in online_payments.data]) if online_payments.data else 0
                            st.metric("💳 Paiements En Ligne", f"{online_total:,.0f} DA")
                    except Exception as e:
                        st.metric("💳 En Ligne", "Erreur")

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

                            # Historique des paiements pour CETTE inscription uniquement
                            payments = supabase.table('payments').select('*').eq('enrollment_id', enr['id']).order('payment_date', desc=True).execute()

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
                                    # Afficher l'icône de la méthode de paiement
                                    method_icon = "💵" if payment.get('payment_method') == 'liquide' else "💳"
                                    st.write(f"- {method_icon} {payment['amount']:,.0f} DA le {date}{receipt_text}")
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
                    group_options = {}
                    for g in groups.data:
                        lang_name = g['languages']['name'] if g.get('languages') else 'N/A'
                        tarif = "OLD" if g.get('is_old_pricing', False) else "NEW"
                        label = f"{g['name']} ({lang_name}, {tarif})"
                        group_options[label] = g
                    selected_group = st.selectbox("Groupe *", list(group_options.keys()))
                else:
                    st.error("Aucun groupe disponible")
                    selected_group = None
            except Exception as e:
                st.error(f"Erreur : {str(e)}")
                selected_group = None

            # Créer une clé unique si on a un groupe et un étudiant sélectionnés
            form_key = None
            if selected_group and selected_student:
                group_data_temp = group_options[selected_group]
                student_data_temp = student_options[selected_student]
                form_key = f"{group_data_temp['id']}_{student_data_temp['id']}"

            # Afficher le champ niveau avec une clé dynamique si disponible
            if form_key:
                level = st.number_input("Niveau *", min_value=1, value=1, key=f"level_{form_key}")
            else:
                level = st.number_input("Niveau *", min_value=1, value=1)

            # Calculer automatiquement les frais
            if selected_group and selected_student:
                group_data = group_options[selected_group]
                student_data = student_options[selected_student]

                lang_name = group_data['languages']['name'] if group_data.get('languages') else 'Japonais'
                mode = group_data['mode']
                duration = group_data['duration_months']
                group_is_old_pricing = group_data.get('is_old_pricing', False)

                # Checkbox pour appliquer l'ancienne tarification pour cet étudiant spécifiquement
                st.divider()
                use_old_pricing = st.checkbox(
                    "Appliquer l'ancienne tarification (OLD) pour cet étudiant",
                    value=group_is_old_pricing,  # Par défaut = tarif du groupe
                    key=f"use_old_pricing_{form_key}",
                    help="Cochez pour appliquer les anciens tarifs à cet étudiant, même si le groupe est en nouvelle tarification"
                )

                # Calculer le prix du cours selon le choix de tarification
                if 'individual' in mode:
                    hours = st.number_input("Nombre d'heures", min_value=1, value=10, key=f"hours_{form_key}")
                    course_fee = calculate_course_fee(lang_name, mode, use_old_pricing, hours)
                else:
                    course_fee = calculate_course_fee(lang_name, mode, use_old_pricing)

                # Vérifier si les frais d'inscription ont déjà été payés cette année
                registration_fee_paid = get_student_registration_status(supabase, student_data['id'])

                # Calculer le montant total
                total_fee = course_fee + (0 if registration_fee_paid else INSCRIPTION_FEE)

                # Afficher le récapitulatif
                st.divider()
                st.markdown("**💰 Récapitulatif des Frais**")

                tarif_type = "OLD (ancienne tarification)" if use_old_pricing else "NEW (nouvelle tarification)"
                st.write(f"**Tarification appliquée:** {tarif_type}")

                if registration_fee_paid:
                    st.success(f"✅ Frais d'inscription déjà payés pour cette année académique")
                    st.info(f"**Prix du cours:** {course_fee:,.0f} DA")
                else:
                    st.info(f"**Prix du cours:** {course_fee:,.0f} DA + **Frais d'inscription:** {INSCRIPTION_FEE:,.0f} DA = **{total_fee:,.0f} DA**")

                st.markdown(f"### **TOTAL: {total_fee:,.0f} DA**")

                # Champ du montant du premier paiement
                st.divider()
                st.markdown("**💳 Premier Paiement**")

                # Cours individuels en ligne : paiement intégral obligatoire
                if 'individual' in mode and 'online' in mode:
                    st.warning("⚠️ Paiement intégral requis pour les cours individuels en ligne")
                    payment_amount = st.number_input(
                        "Montant du premier paiement (DA) *",
                        min_value=float(total_fee),
                        value=float(total_fee),
                        step=1000.0,
                        key=f"payment_amount_{form_key}",
                        help="Le montant total doit être payé"
                    )
                else:
                    # Autres cours : paiement flexible (échelonnement possible)
                    payment_amount = st.number_input(
                        "Montant du premier paiement (DA) *",
                        min_value=0.0,
                        value=float(total_fee),  # Par défaut : paiement complet
                        step=1000.0,
                        key=f"payment_amount_{form_key}",
                        help="Vous pouvez payer en plusieurs fois"
                    )

                    # Afficher le reste à payer
                    if payment_amount < total_fee:
                        reste = total_fee - payment_amount
                        st.info(f"💡 Reste à payer : {reste:,.0f} DA")

                # Méthode de paiement
                payment_method = st.selectbox(
                    "Méthode de paiement *",
                    ["💵 Liquide", "💳 En Ligne"],
                    help="Sélectionnez si le paiement est en liquide ou en ligne"
                )
            else:
                total_fee = 0
                course_fee = 0
                payment_amount = 0
                registration_fee_paid = False
                payment_method = "💵 Liquide"

            st.markdown("*Les champs marqués d'un astérisque sont obligatoires*")

            submitted = st.form_submit_button("Créer l'inscription", use_container_width=True)

            if submitted:
                if selected_student and selected_group:
                    try:
                        student_data = student_options[selected_student]
                        group_data = group_options[selected_group]

                        # Vérifier les conditions d'activation
                        mode = group_data['mode']
                        enrollment_active = False

                        if 'individual' in mode and 'online' in mode:
                            # Paiement intégral requis pour cours individuels en ligne
                            if payment_amount >= total_fee:
                                enrollment_active = True
                        else:
                            # Pour les autres cours
                            if registration_fee_paid:
                                # Frais d'inscription déjà payés : activer dès qu'il y a un paiement
                                enrollment_active = True
                            else:
                                # Frais d'inscription pas encore payés : activer si paiement >= 1000 DA
                                if payment_amount >= INSCRIPTION_FEE:
                                    enrollment_active = True

                        # Créer l'inscription
                        new_enrollment = {
                            'student_id': student_data['id'],
                            'group_id': group_data['id'],
                            'level': level,
                            'total_course_fee': total_fee,
                            'enrollment_active': enrollment_active
                        }

                        enr_response = supabase.table('enrollments').insert(new_enrollment).execute()

                        if enr_response.data:
                            # Convertir la méthode de paiement
                            method_value = 'liquide' if '💵' in payment_method else 'en_ligne'

                            # Enregistrer le premier paiement lié à cette inscription
                            new_payment = {
                                'student_id': student_data['id'],
                                'enrollment_id': enr_response.data[0]['id'],
                                'amount': payment_amount,
                                'payment_method': method_value,
                                'receipt_link': None
                            }

                            pay_response = supabase.table('payments').insert(new_payment).execute()

                            if pay_response.data:
                                # Si c'est le premier enrollment et paiement >= 1000 DA, marquer les frais comme payés
                                if not registration_fee_paid and payment_amount >= INSCRIPTION_FEE:
                                    mark_registration_fee_as_paid(supabase, student_data['id'])

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

                    # Sélectionner l'inscription
                    selected_enrollment = None
                    enrollment_options = {}
                    if selected_student:
                        student_data = student_options[selected_student]
                        enrollments = supabase.table('enrollments').select('*, groups(name, languages(name))').eq('student_id', student_data['id']).execute()

                        if enrollments.data:
                            for enr in enrollments.data:
                                group = enr.get('groups', {})
                                lang_name = group.get('languages', {}).get('name', 'N/A') if group.get('languages') else 'N/A'

                                # Calculer le solde pour cette inscription
                                payments = supabase.table('payments').select('amount').eq('enrollment_id', enr['id']).execute()
                                total_paid = sum([p['amount'] for p in payments.data]) if payments.data else 0
                                remaining = enr['total_course_fee'] - total_paid

                                status_icon = "✅" if enr['enrollment_active'] else "❌"
                                label = f"{group.get('name', 'N/A')} ({lang_name}) - Restant: {remaining:,.0f} DA {status_icon}"
                                enrollment_options[label] = enr

                            selected_enrollment = st.selectbox("Inscription *", list(enrollment_options.keys()), key="payment_enrollment")

                            # Afficher le détail du solde pour l'inscription sélectionnée
                            if selected_enrollment:
                                enr_data = enrollment_options[selected_enrollment]
                                payments = supabase.table('payments').select('amount').eq('enrollment_id', enr_data['id']).execute()
                                total_paid = sum([p['amount'] for p in payments.data]) if payments.data else 0
                                remaining = enr_data['total_course_fee'] - total_paid

                                if remaining > 0:
                                    st.warning(f"💰 Montant restant pour cette inscription: {remaining:,.0f} DA")
                                else:
                                    st.success("✅ Cette inscription est entièrement payée")
                        else:
                            st.info("Aucune inscription pour cet étudiant")
                else:
                    st.error("Aucun étudiant disponible")
                    selected_student = None
            except Exception as e:
                st.error(f"Erreur : {str(e)}")
                selected_student = None
                selected_enrollment = None

            amount = st.number_input("Montant du paiement (DA) *", min_value=100.0, step=100.0)
            receipt_link = st.text_input("Lien du reçu (URL)")

            # Méthode de paiement
            payment_method_tab3 = st.selectbox(
                "Méthode de paiement *",
                ["💵 Liquide", "💳 En Ligne"],
                help="Sélectionnez si le paiement est en liquide ou en ligne",
                key="payment_method_tab3"
            )

            st.markdown("*Les champs marqués d'un astérisque sont obligatoires*")

            submitted = st.form_submit_button("Enregistrer le paiement", use_container_width=True)

            if submitted:
                if selected_student and selected_enrollment and amount > 0:
                    try:
                        student_data = student_options[selected_student]
                        enr_data = enrollment_options[selected_enrollment]

                        # Convertir la méthode de paiement
                        method_value = 'liquide' if '💵' in payment_method_tab3 else 'en_ligne'

                        # Enregistrer le paiement lié à cette inscription
                        new_payment = {
                            'student_id': student_data['id'],
                            'enrollment_id': enr_data['id'],
                            'amount': amount,
                            'payment_method': method_value,
                            'receipt_link': receipt_link if receipt_link else None
                        }

                        response = supabase.table('payments').insert(new_payment).execute()

                        if response.data:
                            # Marquer les frais d'inscription comme payés si nécessaire
                            student_reg_status = get_student_registration_status(supabase, student_data['id'])
                            if not student_reg_status and amount >= INSCRIPTION_FEE:
                                mark_registration_fee_as_paid(supabase, student_data['id'])

                            # Vérifier si on doit activer cette inscription
                            if not enr_data['enrollment_active']:
                                # Recalculer le total payé pour cette inscription
                                payments = supabase.table('payments').select('amount').eq('enrollment_id', enr_data['id']).execute()
                                total_paid = sum([p['amount'] for p in payments.data]) if payments.data else 0

                                group = enr_data.get('groups', {})
                                mode = group.get('mode', '')

                                should_activate = False

                                if 'individual' in mode and 'online' in mode:
                                    # Vérifier si paiement intégral pour cours individuels en ligne
                                    if total_paid >= enr_data['total_course_fee']:
                                        should_activate = True
                                else:
                                    # Vérifier si minimum atteint
                                    # Si frais d'inscription déjà payés, activer immédiatement
                                    # Sinon, activer si total_paid >= 1000 DA
                                    if student_reg_status or total_paid >= INSCRIPTION_FEE:
                                        should_activate = True

                                if should_activate:
                                    supabase.table('enrollments').update({'enrollment_active': True}).eq('id', enr_data['id']).execute()
                                    st.success("✅ Paiement enregistré et inscription activée!")
                                else:
                                    st.success("✅ Paiement enregistré avec succès!")
                            else:
                                st.success("✅ Paiement enregistré avec succès!")

                            st.rerun()
                        else:
                            st.error("Erreur lors de l'enregistrement du paiement")

                    except Exception as e:
                        st.error(f"Erreur : {str(e)}")
                else:
                    st.warning("Veuillez sélectionner un étudiant, une inscription et saisir un montant")
