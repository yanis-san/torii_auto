import streamlit as st
import pandas as pd
from utils import get_supabase_client, get_current_academic_year
from datetime import datetime

def show():
    st.title("👥 Gestion des Étudiants")

    supabase = get_supabase_client()

    # Récupérer l'année académique actuelle
    current_year = get_current_academic_year()
    if not current_year:
        st.error("⚠️ Aucune année académique active trouvée dans Supabase. Veuillez configurer une année académique.")
        # Afficher les données de la table pour diagnostic
        try:
            all_years = supabase.table('academic_years').select('*').execute()
            st.write("**Années académiques disponibles :**", all_years.data)
        except Exception as e:
            st.write(f"Erreur lors de la récupération des années: {e}")
        st.stop()

    # Afficher les détails de l'année actuelle pour debug
    st.sidebar.write("**Debug - Année actuelle:**")
    st.sidebar.json(current_year)

    tab1, tab2, tab3 = st.tabs(["📋 Liste", "➕ Ajouter", "🔍 Rechercher"])

    with tab1:
        st.subheader("Liste des Étudiants")

        try:
            students_response = supabase.table('students').select('*, academic_years(year_label, prefix)').order('created_at', desc=True).execute()

            if students_response.data:
                students_list = []
                for student in students_response.data:
                    id_doc_link = student.get('id_document_link')
                    academic_year = student.get('academic_years', {})
                    year_label = academic_year.get('year_label', 'N/A') if academic_year else 'N/A'

                    students_list.append({
                        'ID': student['id'],
                        'Code': student.get('student_code', 'N/A'),
                        'Prénom': student['first_name'],
                        'Nom': student['last_name'],
                        'Email': student['email'],
                        'Téléphone': student.get('phone_number', 'N/A'),
                        'Pièce ID': id_doc_link if id_doc_link else 'N/A',
                        'Date de naissance': student.get('birth_date', 'N/A'),
                        'Année académique': year_label,
                        'Créé le': student.get('created_at', 'N/A')
                    })

                df = pd.DataFrame(students_list)
                st.dataframe(
                    df,
                    column_config={
                        "Pièce ID": st.column_config.LinkColumn("Pièce ID", display_text="📄 Voir"),
                    },
                    hide_index=True,
                    use_container_width=True
                )

                # Statistiques rapides
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Étudiants", len(students_list))
                with col2:
                    # Compter les étudiants de l'année académique actuelle
                    current_year_students = [s for s in students_response.data
                                           if s.get('academic_year_id') == current_year['id']]
                    st.metric(f"Étudiants {current_year['year_label']}", len(current_year_students))
                with col3:
                    # Compter les inscriptions actives
                    enrollments = supabase.table('enrollments').select('*', count='exact').eq('enrollment_active', True).execute()
                    st.metric("Inscriptions Actives", enrollments.count)
            else:
                st.info("Aucun étudiant enregistré")

        except Exception as e:
            st.error(f"Erreur lors du chargement des étudiants : {str(e)}")

    with tab2:
        st.subheader("Ajouter un Nouvel Étudiant")

        # Afficher l'année académique en cours
        st.info(f"📅 Année académique en cours : **{current_year['year_label']}** (Préfixe : {current_year['prefix']})")

        with st.form("add_student_form"):
            col1, col2 = st.columns(2)

            with col1:
                first_name = st.text_input("Prénom *")
                last_name = st.text_input("Nom *")
                email = st.text_input("Email *")
                phone_number = st.text_input("Téléphone")
                id_document_link = st.text_input("Lien pièce d'identité (URL)")

            with col2:
                birth_date = st.date_input(
                    "Date de naissance",
                    value=None,
                    min_value=datetime(1940, 1, 1),
                    max_value=datetime.now()
                )

            st.markdown("*Les champs marqués d'un astérisque sont obligatoires*")
            st.markdown(f"*Le code étudiant sera automatiquement généré avec le préfixe **{current_year['prefix']}***")

            submitted = st.form_submit_button("Ajouter l'étudiant", width="stretch")

            if submitted:
                if first_name and last_name and email:
                    try:
                        # Vérifier que l'année académique est bien définie
                        if not current_year or not current_year.get('id'):
                            st.error("❌ Erreur : Aucune année académique active. Veuillez vérifier la configuration dans Supabase.")
                            st.stop()

                        # Vérifier si l'email existe déjà
                        existing = supabase.table('students').select('*').eq('email', email).execute()

                        if existing.data:
                            st.error("Un étudiant avec cet email existe déjà")
                        else:
                            # Insérer le nouvel étudiant (le trigger générera le code automatiquement)
                            new_student = {
                                'first_name': first_name,
                                'last_name': last_name,
                                'email': email,
                                'phone_number': phone_number if phone_number else None,
                                'id_document_link': id_document_link if id_document_link else None,
                                'academic_year_id': current_year['id'],
                                'birth_date': birth_date.isoformat() if birth_date else None
                            }

                            response = supabase.table('students').insert(new_student).execute()

                            if response.data:
                                st.success(f"✅ Étudiant ajouté avec succès! Code: {response.data[0].get('student_code', 'N/A')}")
                                st.rerun()
                            else:
                                st.error("Erreur lors de l'ajout de l'étudiant")

                    except Exception as e:
                        st.error(f"Erreur : {str(e)}")
                else:
                    st.warning("Veuillez remplir tous les champs obligatoires")

    with tab3:
        st.subheader("Rechercher un Étudiant")

        search_term = st.text_input("Rechercher par nom, prénom, email ou code étudiant")

        if search_term:
            try:
                # Recherche multiple
                students = supabase.table('students').select('*, academic_years(year_label, prefix)').execute()

                if students.data:
                    filtered = [
                        s for s in students.data
                        if search_term.lower() in s['first_name'].lower()
                        or search_term.lower() in s['last_name'].lower()
                        or search_term.lower() in s['email'].lower()
                        or (s.get('student_code') and search_term.lower() in s['student_code'].lower())
                    ]

                    if filtered:
                        for student in filtered:
                            with st.expander(f"{student['first_name']} {student['last_name']} - {student.get('student_code', 'N/A')}"):
                                col1, col2 = st.columns(2)

                                with col1:
                                    st.write(f"**Code Étudiant:** {student.get('student_code', 'N/A')}")
                                    st.write(f"**Email:** {student['email']}")
                                    st.write(f"**Téléphone:** {student.get('phone_number', 'N/A')}")
                                    id_doc = student.get('id_document_link')
                                    if id_doc:
                                        st.write(f"**Pièce d'identité:** [📄 Voir le document]({id_doc})")
                                    else:
                                        st.write("**Pièce d'identité:** N/A")
                                    st.write(f"**Date de naissance:** {student.get('birth_date', 'N/A')}")

                                with col2:
                                    academic_year = student.get('academic_years', {})
                                    year_label = academic_year.get('year_label', 'N/A') if academic_year else 'N/A'
                                    st.write(f"**Année académique:** {year_label}")
                                    st.write(f"**Créé le:** {student.get('created_at', 'N/A')}")

                                st.divider()

                                # Afficher les inscriptions
                                enrollments = supabase.table('enrollments').select('*, groups(name, level, mode, languages(name))').eq('student_id', student['id']).execute()

                                if enrollments.data:
                                    st.markdown("**Inscriptions:**")
                                    for enr in enrollments.data:
                                        group = enr.get('groups', {})
                                        lang_name = group.get('languages', {}).get('name', 'N/A') if group.get('languages') else 'N/A'
                                        status = "✅ Active" if enr['enrollment_active'] else "❌ Inactive"
                                        st.write(f"- {group.get('name', 'N/A')} ({lang_name}, Niveau {enr['level']}) - {status}")

                                # Afficher les paiements
                                payments = supabase.table('payments').select('*').eq('student_id', student['id']).order('payment_date', desc=True).execute()

                                if payments.data:
                                    st.markdown("**Paiements:**")
                                    total_paid = sum([p['amount'] for p in payments.data])
                                    st.write(f"Total payé: **{total_paid:,.0f} DA**")

                                    with st.expander("Détails des paiements"):
                                        for payment in payments.data:
                                            st.write(f"- {payment['amount']:,.0f} DA le {payment.get('payment_date', 'N/A')}")

                                # Boutons d'action
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button(f"Modifier", key=f"edit_{student['id']}"):
                                        st.info("Fonctionnalité à venir")
                                with col2:
                                    if st.button(f"Supprimer", key=f"delete_{student['id']}", type="primary"):
                                        try:
                                            supabase.table('students').delete().eq('id', student['id']).execute()
                                            st.success("Étudiant supprimé")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erreur : {str(e)}")
                    else:
                        st.info("Aucun étudiant trouvé")
                else:
                    st.info("Aucun étudiant enregistré")

            except Exception as e:
                st.error(f"Erreur : {str(e)}")
