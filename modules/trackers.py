import streamlit as st
import pandas as pd
from utils import get_supabase_client
from datetime import datetime, timedelta

def show():
    st.title("📊 Suivi de Caisse")

    supabase = get_supabase_client()

    # Tabs pour organiser les différentes vues
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💰 Caisse & Signature",
        "➕ Ajouter Paiement",
        "📋 Historique Signatures",
        "📈 Statistiques",
        "👥 Par Personne"
    ])

    # ============================================
    # TAB 1: CAISSE & SIGNATURE
    # ============================================
    with tab1:
        st.subheader("💰 Caisse & Signature")

        # Calculer le montant actuel en caisse
        try:
            # Récupérer la dernière signature
            last_signature = supabase.table('cash_register_resets').select('*').order('reset_date', desc=True).limit(1).execute()

            if last_signature.data:
                last_sig = last_signature.data[0]
                last_reset_date = last_sig['reset_date']
                amount_left_last_time = last_sig.get('amount_left', 0) or 0
                last_reset_by = last_sig.get('reset_by', 'N/A')

                # Compter UNIQUEMENT les paiements LIQUIDES depuis la dernière signature
                payments_since = supabase.table('payments').select('*').gte('payment_date', last_reset_date).eq('payment_method', 'liquide').execute()
                payments_total = sum([p['amount'] for p in payments_since.data]) if payments_since.data else 0

                current_amount = amount_left_last_time + payments_total
            else:
                # Pas de signature précédente, compter tous les paiements liquides
                all_payments = supabase.table('payments').select('*').eq('payment_method', 'liquide').execute()
                current_amount = sum([p['amount'] for p in all_payments.data]) if all_payments.data else 0
                last_reset_date = None
                last_reset_by = 'N/A'
                payments_since = all_payments
                amount_left_last_time = 0

            # Affichage en grand du montant
            st.markdown("### 💵 Montant Actuel en Caisse")

            col_amount1, col_amount2 = st.columns([3, 1])
            with col_amount1:
                st.markdown(f"# {current_amount:,.0f} DA")

            with col_amount2:
                # Bouton d'initialisation UNIQUEMENT s'il n'y a JAMAIS eu de signature
                # (pas même une signature "Système")
                all_signatures = supabase.table('cash_register_resets').select('id').execute()
                has_any_signature = len(all_signatures.data) > 0 if all_signatures.data else False

                if not has_any_signature and current_amount > 0:
                    # Aucune signature n'a jamais été créée, mais il y a des paiements liquides
                    st.warning(f"⚠️ Initialisation requise")
                    if st.button("🔄 Initialiser la Caisse", type="secondary", help="Créer le point de départ pour le suivi de caisse"):
                        try:
                            current_user = st.session_state.get('user_name', 'Utilisateur')
                            supabase.table('cash_register_resets').insert({
                                'reset_date': datetime.now().isoformat(),
                                'reset_by': current_user,
                                'amount_in_register': current_amount,
                                'amount_taken': 0,
                                'amount_left': current_amount,
                                'notes': f"🔄 Initialisation : {current_amount:,.0f} DA de paiements liquides en caisse"
                            }).execute()

                            st.success(f"✅ Caisse initialisée avec {current_amount:,.0f} DA !")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {str(e)}")

            st.divider()

            # Détails en 2 colonnes
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 📝 Dernière Signature")
                if last_reset_date:
                    last_date = datetime.fromisoformat(last_reset_date.replace('Z', '+00:00'))
                    st.write(f"**Date:** {last_date.strftime('%d/%m/%Y à %H:%M')}")
                    st.write(f"**Signé par:** {last_reset_by}")
                    st.write(f"**Montant laissé:** {amount_left_last_time:,.0f} DA")
                else:
                    st.info("Aucune signature enregistrée")

            with col2:
                st.markdown("#### 💳 Nouveaux Paiements Liquides")
                payments_count = len(payments_since.data) if payments_since.data else 0
                st.write(f"**Nombre de paiements:** {payments_count}")
                st.write(f"**Montant total:** {payments_total:,.0f} DA")

            st.divider()

            # Section: Signature du comptage
            st.markdown("### ✍️ Signature du Comptage de Caisse")
            st.info(f"💵 **Montant actuel en caisse : {current_amount:,.0f} DA**")

            if st.button("✍️ Signer le Comptage", type="primary", use_container_width=True):
                st.session_state['show_signature_form'] = True

            # Formulaire de signature (modal)
            if st.session_state.get('show_signature_form', False):
                with st.form("signature_form"):
                    st.markdown("#### 📝 Signature de Comptage")

                    # Récupérer le nom de l'utilisateur connecté
                    current_user = st.session_state.get('user_name', 'Utilisateur')
                    st.info(f"👤 Signé par : **{current_user}**")

                    st.write(f"💵 **Montant total en caisse : {current_amount:,.0f} DA**")

                    # Combien prélevé
                    amount_taken = st.number_input("Montant prélevé (DA)", min_value=0.0, max_value=float(current_amount),
                                                  value=0.0, step=1000.0,
                                                  help="Combien d'argent retirez-vous de la caisse?")

                    # Calcul automatique de ce qui reste
                    amount_left = current_amount - amount_taken
                    st.success(f"💰 **Montant laissé dans la caisse : {amount_left:,.0f} DA**")

                    # Notes
                    notes = st.text_area("Observations (optionnel)",
                                        placeholder="Ex: Tout est correct, Dépôt à la banque, Vérification...")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("✅ Signer et Confirmer", use_container_width=True):
                            try:
                                # Enregistrer la signature
                                supabase.table('cash_register_resets').insert({
                                    'reset_date': datetime.now().isoformat(),
                                    'reset_by': current_user,
                                    'amount_in_register': current_amount,
                                    'amount_taken': amount_taken,
                                    'amount_left': amount_left,
                                    'notes': notes.strip() if notes.strip() else None
                                }).execute()

                                st.success("✅ Signature enregistrée avec succès!")
                                st.session_state['show_signature_form'] = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {str(e)}")

                    with col2:
                        if st.form_submit_button("❌ Annuler", use_container_width=True):
                            st.session_state['show_signature_form'] = False
                            st.rerun()

        except Exception as e:
            st.error(f"Erreur : {str(e)}")

    # ============================================
    # TAB 2: AJOUTER UN PAIEMENT
    # ============================================
    with tab2:
        st.subheader("➕ Enregistrer un Paiement")
        st.info("💡 Utilisez ce formulaire pour enregistrer un paiement (liquide ou en ligne)")

        with st.form("add_payment_form_tracker"):
            # Sélectionner l'étudiant
            try:
                students = supabase.table('students').select('*').order('created_at', desc=True).execute()
                if students.data:
                    student_options = {f"{s['first_name']} {s['last_name']} ({s.get('student_code', 'N/A')})": s for s in students.data}
                    selected_student = st.selectbox("Étudiant *", list(student_options.keys()), key="tracker_student")

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

                                # Calculer le solde
                                payments = supabase.table('payments').select('amount').eq('enrollment_id', enr['id']).execute()
                                total_paid = sum([p['amount'] for p in payments.data]) if payments.data else 0
                                remaining = enr['total_course_fee'] - total_paid

                                status_icon = "✅" if enr['enrollment_active'] else "❌"
                                label = f"{group.get('name', 'N/A')} ({lang_name}) - Restant: {remaining:,.0f} DA {status_icon}"
                                enrollment_options[label] = enr

                            selected_enrollment = st.selectbox("Inscription *", list(enrollment_options.keys()), key="tracker_enrollment")

                            # Afficher le détail du solde
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

            col1, col2 = st.columns(2)

            with col1:
                amount = st.number_input("Montant (DA) *", min_value=100.0, step=1000.0, key="tracker_amount")

            with col2:
                # Méthode de paiement
                payment_method = st.selectbox(
                    "Méthode de paiement *",
                    ["💵 Liquide", "💳 En Ligne"],
                    help="Sélectionnez si le paiement est en liquide ou en ligne",
                    key="tracker_payment_method"
                )

            receipt_link = st.text_input("Lien du reçu (optionnel)", key="tracker_receipt")

            st.markdown("*Les champs marqués d'un astérisque sont obligatoires*")

            submitted = st.form_submit_button("💳 Enregistrer le Paiement", use_container_width=True)

            if submitted:
                if selected_student and selected_enrollment and amount > 0:
                    try:
                        student_data = student_options[selected_student]
                        enr_data = enrollment_options[selected_enrollment]

                        # Convertir la méthode de paiement
                        method_value = 'liquide' if '💵' in payment_method else 'en_ligne'

                        # Enregistrer le paiement
                        new_payment = {
                            'student_id': student_data['id'],
                            'enrollment_id': enr_data['id'],
                            'amount': amount,
                            'payment_method': method_value,
                            'receipt_link': receipt_link if receipt_link else None
                        }

                        response = supabase.table('payments').insert(new_payment).execute()

                        if response.data:
                            payment_type_text = "💵 liquide" if method_value == 'liquide' else "💳 en ligne"
                            st.success(f"✅ Paiement de {amount:,.0f} DA ({payment_type_text}) enregistré avec succès!")
                            st.rerun()
                        else:
                            st.error("Erreur lors de l'enregistrement")
                    except Exception as e:
                        st.error(f"Erreur : {str(e)}")
                else:
                    st.warning("Veuillez remplir tous les champs obligatoires")

    # ============================================
    # TAB 3: HISTORIQUE DES SIGNATURES
    # ============================================
    with tab3:
        st.subheader("📋 Historique des Signatures de Comptage")

        try:
            # Récupérer toutes les signatures (exclure l'initialisation)
            signatures = supabase.table('cash_register_resets').select('*').neq('reset_by', 'Système').order('reset_date', desc=True).execute()

            if signatures.data:
                # Préparer les données pour l'affichage
                history_data = []
                for sig in signatures.data:
                    reset_datetime = datetime.fromisoformat(sig['reset_date'].replace('Z', '+00:00'))

                    history_data.append({
                        'ID': sig['id'],
                        'Date': reset_datetime.strftime('%d/%m/%Y'),
                        'Heure': reset_datetime.strftime('%H:%M'),
                        'Signé par': sig['reset_by'],
                        'Total en Caisse': f"{sig['amount_in_register']:,.0f} DA",
                        'Prélevé': f"{sig['amount_taken']:,.0f} DA",
                        'Laissé': f"{sig['amount_left']:,.0f} DA",
                        'Observations': sig.get('notes', '-') or '-'
                    })

                df_history = pd.DataFrame(history_data)
                st.dataframe(df_history, use_container_width=True, hide_index=True)

                # Métriques récapitulatives
                st.divider()
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Total Signatures", len(history_data))

                with col2:
                    total_preleve = sum([sig['amount_taken'] for sig in signatures.data])
                    st.metric("Total Prélevé", f"{total_preleve:,.0f} DA")

                with col3:
                    moyenne_preleve = total_preleve / len(signatures.data) if signatures.data else 0
                    st.metric("Moyenne par Signature", f"{moyenne_preleve:,.0f} DA")

                with col4:
                    # Dernière signature
                    last_sig = signatures.data[0]
                    last_date = datetime.fromisoformat(last_sig['reset_date'].replace('Z', '+00:00'))
                    st.metric("Dernière Signature", last_date.strftime('%d/%m/%Y'))

            else:
                st.info("Aucune signature enregistrée pour le moment")

        except Exception as e:
            st.error(f"Erreur : {str(e)}")

    # ============================================
    # TAB 4: STATISTIQUES (ANALYSES DÉTAILLÉES)
    # ============================================
    with tab4:
        st.subheader("📈 Statistiques et Analyses")

        try:
            signatures = supabase.table('cash_register_resets').select('*').neq('reset_by', 'Système').order('reset_date', desc=True).execute()

            if signatures.data:
                # Section: Signatures récentes (7 derniers jours)
                st.markdown("### 📅 Signatures Récentes (7 derniers jours)")

                seven_days_ago = datetime.now() - timedelta(days=7)
                recent_sigs = [sig for sig in signatures.data
                              if datetime.fromisoformat(sig['reset_date'].replace('Z', '+00:00')) >= seven_days_ago]

                if recent_sigs:
                    recent_data = []
                    for sig in recent_sigs:
                        reset_datetime = datetime.fromisoformat(sig['reset_date'].replace('Z', '+00:00'))
                        recent_data.append({
                            'Date': reset_datetime.strftime('%d/%m/%Y %H:%M'),
                            'Signé par': sig['reset_by'],
                            'Total': f"{sig['amount_in_register']:,.0f} DA",
                            'Prélevé': f"{sig['amount_taken']:,.0f} DA",
                            'Laissé': f"{sig['amount_left']:,.0f} DA",
                            'Observations': sig.get('notes', '-') or '-'
                        })

                    df_recent = pd.DataFrame(recent_data)
                    st.dataframe(df_recent, use_container_width=True, hide_index=True)
                else:
                    st.info("Aucune signature dans les 7 derniers jours")

                st.divider()

                # Section: Prélèvements importants (> 20,000 DA)
                st.markdown("### 💸 Prélèvements Importants (> 20,000 DA)")

                big_withdrawals = [sig for sig in signatures.data if sig['amount_taken'] > 20000]

                if big_withdrawals:
                    big_data = []
                    for sig in big_withdrawals:
                        reset_datetime = datetime.fromisoformat(sig['reset_date'].replace('Z', '+00:00'))
                        big_data.append({
                            'Date': reset_datetime.strftime('%d/%m/%Y %H:%M'),
                            'Signé par': sig['reset_by'],
                            'Montant Prélevé': f"{sig['amount_taken']:,.0f} DA",
                            'Observations': sig.get('notes', '-') or '-'
                        })

                    df_big = pd.DataFrame(big_data)
                    st.dataframe(df_big, use_container_width=True, hide_index=True)
                else:
                    st.info("Aucun prélèvement important")

                st.divider()

                # Section: Vérifications sans prélèvement
                st.markdown("### ✅ Vérifications Sans Prélèvement")

                verifications = [sig for sig in signatures.data if sig['amount_taken'] == 0]

                if verifications:
                    verif_data = []
                    for sig in verifications:
                        reset_datetime = datetime.fromisoformat(sig['reset_date'].replace('Z', '+00:00'))
                        verif_data.append({
                            'Date': reset_datetime.strftime('%d/%m/%Y %H:%M'),
                            'Signé par': sig['reset_by'],
                            'Total Vérifié': f"{sig['amount_in_register']:,.0f} DA",
                            'Observations': sig.get('notes', '-') or '-'
                        })

                    df_verif = pd.DataFrame(verif_data)
                    st.dataframe(df_verif, use_container_width=True, hide_index=True)
                else:
                    st.info("Aucune vérification sans prélèvement")

                st.divider()

                # Section: Analyse des délais entre signatures
                st.markdown("### ⏱️ Délais Entre Signatures")

                if len(signatures.data) >= 2:
                    delays_data = []
                    for i in range(len(signatures.data) - 1):
                        current_sig = signatures.data[i]
                        previous_sig = signatures.data[i + 1]

                        current_date = datetime.fromisoformat(current_sig['reset_date'].replace('Z', '+00:00'))
                        previous_date = datetime.fromisoformat(previous_sig['reset_date'].replace('Z', '+00:00'))

                        delay_days = (current_date - previous_date).days

                        delays_data.append({
                            'Signature': current_date.strftime('%d/%m/%Y'),
                            'Signé par': current_sig['reset_by'],
                            'Signature Précédente': previous_date.strftime('%d/%m/%Y'),
                            'Délai': f"{delay_days} jours"
                        })

                    df_delays = pd.DataFrame(delays_data)
                    st.dataframe(df_delays, use_container_width=True, hide_index=True)

                    # Moyenne des délais
                    avg_delay = sum([int(d['Délai'].split()[0]) for d in delays_data]) / len(delays_data)
                    st.info(f"⏰ Délai moyen entre signatures : **{avg_delay:.1f} jours**")
                else:
                    st.info("Pas assez de signatures pour calculer les délais")

            else:
                st.info("Aucune donnée disponible")

        except Exception as e:
            st.error(f"Erreur : {str(e)}")

    # ============================================
    # TAB 5: STATISTIQUES PAR PERSONNE
    # ============================================
    with tab5:
        st.subheader("👥 Statistiques par Personne")

        try:
            signatures = supabase.table('cash_register_resets').select('*').neq('reset_by', 'Système').order('reset_date', desc=True).execute()

            if signatures.data:
                # Grouper par personne
                stats_by_person = {}

                for sig in signatures.data:
                    person = sig['reset_by']
                    if person not in stats_by_person:
                        stats_by_person[person] = {
                            'count': 0,
                            'total_taken': 0,
                            'total_in_register': 0,
                            'amounts_taken': []
                        }

                    stats_by_person[person]['count'] += 1
                    stats_by_person[person]['total_taken'] += sig['amount_taken']
                    stats_by_person[person]['total_in_register'] += sig['amount_in_register']
                    stats_by_person[person]['amounts_taken'].append(sig['amount_taken'])

                # Créer le DataFrame
                person_data = []
                for person, stats in stats_by_person.items():
                    person_data.append({
                        'Personne': person,
                        'Nombre de Signatures': stats['count'],
                        'Total Prélevé': f"{stats['total_taken']:,.0f} DA",
                        'Moyenne par Signature': f"{stats['total_taken'] / stats['count']:,.0f} DA",
                        'Min Prélevé': f"{min(stats['amounts_taken']):,.0f} DA",
                        'Max Prélevé': f"{max(stats['amounts_taken']):,.0f} DA"
                    })

                df_person = pd.DataFrame(person_data)
                # Trier par total prélevé (convertir en nombre pour le tri)
                df_person['_sort'] = df_person['Total Prélevé'].str.replace(' DA', '').str.replace(',', '').astype(float)
                df_person = df_person.sort_values('_sort', ascending=False).drop('_sort', axis=1)

                st.dataframe(df_person, use_container_width=True, hide_index=True)

                st.divider()

                # Graphique si possible (simple affichage textuel)
                st.markdown("### 📊 Répartition des Signatures")

                for person, stats in sorted(stats_by_person.items(), key=lambda x: x[1]['total_taken'], reverse=True):
                    percentage = (stats['count'] / len(signatures.data)) * 100
                    st.write(f"**{person}:** {stats['count']} signatures ({percentage:.1f}%)")
                    st.progress(percentage / 100)

            else:
                st.info("Aucune donnée disponible")

        except Exception as e:
            st.error(f"Erreur : {str(e)}")
