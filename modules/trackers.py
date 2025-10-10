import streamlit as st
import pandas as pd
from utils import get_supabase_client
from datetime import datetime, timedelta

def show():
    st.title("📊 Suivi de Caisse")

    supabase = get_supabase_client()

    # Tabs pour organiser les différentes vues
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Historique Complet",
        "📈 Statistiques",
        "💰 Montant Actuel",
        "👥 Par Personne"
    ])

    # ============================================
    # TAB 1: HISTORIQUE COMPLET
    # ============================================
    with tab1:
        st.subheader("Historique des Signatures de Comptage")

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
    # TAB 2: STATISTIQUES
    # ============================================
    with tab2:
        st.subheader("Statistiques et Analyses")

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
    # TAB 3: MONTANT ACTUEL EN CAISSE
    # ============================================
    with tab3:
        st.subheader("💰 Montant Actuel en Caisse")

        try:
            # Récupérer la dernière signature
            last_signature = supabase.table('cash_register_resets').select('*').order('reset_date', desc=True).limit(1).execute()

            if last_signature.data:
                last_sig = last_signature.data[0]
                last_reset_date = last_sig['reset_date']
                amount_left_last_time = last_sig.get('amount_left', 0) or 0
                last_reset_by = last_sig.get('reset_by', 'N/A')

                # Compter les paiements depuis la dernière signature
                payments_since = supabase.table('payments').select('*').gte('payment_date', last_reset_date).execute()

                payments_total = sum([p['amount'] for p in payments_since.data]) if payments_since.data else 0
                payments_count = len(payments_since.data) if payments_since.data else 0

                # Montant total en caisse
                current_amount = amount_left_last_time + payments_total

                # Affichage en grand
                st.markdown("### 💵 Montant Total en Caisse")
                st.markdown(f"# {current_amount:,.0f} DA")

                st.divider()

                # Détails
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("#### 📝 Dernière Signature")
                    last_date = datetime.fromisoformat(last_reset_date.replace('Z', '+00:00'))
                    st.write(f"**Date:** {last_date.strftime('%d/%m/%Y à %H:%M')}")
                    st.write(f"**Signé par:** {last_reset_by}")
                    st.write(f"**Montant laissé:** {amount_left_last_time:,.0f} DA")

                    if last_sig.get('notes'):
                        st.write(f"**Observations:** {last_sig['notes']}")

                with col2:
                    st.markdown("#### 💳 Nouveaux Paiements")
                    st.write(f"**Nombre de paiements:** {payments_count}")
                    st.write(f"**Montant total:** {payments_total:,.0f} DA")

                st.divider()

                # Détail des nouveaux paiements
                if payments_since.data:
                    st.markdown("#### 📋 Détail des Nouveaux Paiements")

                    payments_detail = []
                    for payment in payments_since.data:
                        payment_date = datetime.fromisoformat(payment['payment_date'].replace('Z', '+00:00'))

                        # Récupérer les infos de l'étudiant
                        student_info = supabase.table('students').select('first_name, last_name, student_code').eq('id', payment['student_id']).execute()
                        student_name = "N/A"
                        student_code = "N/A"
                        if student_info.data:
                            student = student_info.data[0]
                            student_name = f"{student.get('first_name', '')} {student.get('last_name', '')}"
                            student_code = student.get('student_code', 'N/A')

                        payments_detail.append({
                            'Date': payment_date.strftime('%d/%m/%Y %H:%M'),
                            'Étudiant': student_name,
                            'Code': student_code,
                            'Montant': f"{payment['amount']:,.0f} DA"
                        })

                    df_payments = pd.DataFrame(payments_detail)
                    st.dataframe(df_payments, use_container_width=True, hide_index=True)

            else:
                st.info("Aucune signature enregistrée")

        except Exception as e:
            st.error(f"Erreur : {str(e)}")

    # ============================================
    # TAB 4: STATISTIQUES PAR PERSONNE
    # ============================================
    with tab4:
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
