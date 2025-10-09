# 🎓 Institut Torii - Application de Gestion

Application Streamlit complète pour la gestion des inscriptions, cours, paiements et présences de l'Institut Torii.

## 📋 Fonctionnalités

### Pour les Administrateurs
- **Dashboard** : Vue d'ensemble avec statistiques et KPIs
- **Gestion des Étudiants** : Ajout, recherche, suivi des codes étudiants
- **Gestion des Paiements** : Inscriptions, paiements échelonnés, suivi des soldes
- **Gestion des Groupes** : Création de groupes, assignation d'enseignants
- **Gestion des Enseignants** : Ajout et gestion des enseignants
- **Gestion des Salles** : Création et gestion des salles de cours
- **Planning** : Création et gestion des emplois du temps
- **Présences** : Prise et suivi des présences

### Pour les Enseignants
- **Mon Planning** : Vue du planning personnel
- **Présences** : Prise de présences pour les cours assignés

## 🗄️ Structure de la Base de Données

### Tables principales
- `languages` : Langues (Japonais, Chinois, Coréen)
- `teachers` : Enseignants
- `classrooms` : Salles de cours
- `groups` : Groupes de cours
- `group_teacher` : Liaison enseignants-groupes
- `students` : Étudiants (avec génération automatique du code)
- `payments` : Paiements
- `enrollments` : Inscriptions (étudiants → groupes)
- `schedule` : Planning des cours
- `attendance` : Présences

## 🚀 Installation

1. **Cloner le projet ou télécharger les fichiers**

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Configurer les variables d'environnement**

Le fichier `.env` contient déjà les informations de connexion Supabase.

4. **Initialiser la base de données**

Exécutez d'abord le script d'initialisation pour ajouter les langues :
```bash
python init_database.py
```

5. **Lancer l'application**
```bash
streamlit run app.py
```

## 💰 Logique des Paiements

### Tarifs par défaut
- **Japonais** :
  - Groupe en ligne : 10 000 DA/mois
  - Individuel en ligne : 2 000 DA/heure
  - Groupe présentiel : 12 000 DA/mois
  - Individuel présentiel : 2 500 DA/heure

- **Chinois** :
  - Groupe en ligne : 20 000 DA/mois
  - Individuel en ligne : 3 000 DA/heure
  - Groupe présentiel : 22 000 DA/mois
  - Individuel présentiel : 3 500 DA/heure

- **Coréen** :
  - Groupe en ligne : 15 000 DA/mois
  - Individuel en ligne : 2 500 DA/heure
  - Groupe présentiel : 17 000 DA/mois
  - Individuel présentiel : 3 000 DA/heure

- **Frais d'inscription** : 1 000 DA (à chaque nouveau code étudiant)

### Règles de paiement
1. **Cours en ligne individuel** : Paiement intégral obligatoire pour activer l'inscription
2. **Autres cours** : Paiement échelonné possible (1, 2 ou 3 fois)
   - Le premier paiement doit inclure au minimum : mensualité + frais d'inscription
3. L'inscription est activée (`enrollment_active = True`) seulement si les conditions sont remplies

## 👤 Codes Étudiants

Le code étudiant est généré automatiquement selon le format : **YYXXX**
- YY : Année (format court, ex: 26 pour 2026)
- XXX : Numéro séquentiel (001, 002, etc.)

Le système utilise un trigger PostgreSQL pour :
- Attribuer le plus petit numéro disponible pour l'année
- Gérer les trous dans la numérotation
- Garantir l'unicité des codes

## 🔐 Authentification avec Supabase Auth

L'application utilise **Supabase Auth** pour une authentification sécurisée avec gestion des rôles.

### Configuration initiale

1. **Exécuter le script SQL dans Supabase** :
   - Ouvrez votre tableau de bord Supabase
   - Allez dans "SQL Editor"
   - Copiez et exécutez le contenu de `setup_supabase_auth.sql`
   - Cela créera la table `users` et configurera les politiques de sécurité (RLS)

2. **Créer votre premier compte admin** :
   - Lancez l'application : `streamlit run app.py`
   - Cliquez sur "Créer un compte"
   - Remplissez le formulaire
   - Sélectionnez "Administrateur" comme type de compte
   - Validez l'email envoyé par Supabase

### Fonctionnalités d'authentification

✅ **Inscription** : Création de compte avec email/mot de passe
✅ **Connexion sécurisée** : Authentification via Supabase Auth
✅ **Gestion des rôles** : Admin ou Enseignant
✅ **Mot de passe oublié** : Réinitialisation par email
✅ **Profil utilisateur** : Modification des informations et mot de passe
✅ **Déconnexion** : Fermeture de session sécurisée

### Types de comptes

**Administrateur** :
- Accès complet à toutes les fonctionnalités
- Gestion des étudiants, paiements, groupes, enseignants, salles
- Création et gestion du planning
- Prise de présences pour tous les groupes

**Enseignant** :
- Consultation de son planning personnel
- Prise de présences pour ses groupes assignés
- Gestion de son profil

## 📁 Structure du Projet

```
torii_inscription/
├── app.py                     # Point d'entrée principal
├── auth.py                    # Module d'authentification Supabase Auth
├── utils.py                   # Utilitaires (connexion Supabase)
├── init_database.py           # Script d'initialisation des langues
├── setup_supabase_auth.sql    # Script SQL pour configurer Auth
├── requirements.txt           # Dépendances
├── .env                       # Variables d'environnement
├── README.md                  # Documentation
└── pages/                     # Modules des pages
    ├── __init__.py
    ├── auth_pages.py          # Pages connexion/inscription
    ├── dashboard.py           # Dashboard
    ├── students.py            # Gestion étudiants
    ├── teachers.py            # Gestion enseignants
    ├── classrooms.py          # Gestion salles
    ├── groups.py              # Gestion groupes
    ├── payments.py            # Gestion paiements
    ├── schedule.py            # Gestion planning
    ├── attendance.py          # Gestion présences
    └── profile.py             # Gestion du profil utilisateur
```

## 🛠️ Développement

### Ajouter une nouvelle page
1. Créer un fichier dans `pages/`
2. Implémenter une fonction `show()`
3. Ajouter l'import et l'appel dans `app.py`

### Modifier les tarifs
Éditez le dictionnaire `COURSE_FEES` dans `pages/payments.py:7`

## 📝 TODO / Améliorations possibles

- [ ] Authentification réelle avec Supabase Auth
- [ ] Export des données (PDF, Excel)
- [ ] Notifications par email
- [ ] Génération automatique de factures
- [ ] Graphiques interactifs (avec Plotly)
- [ ] Gestion des absences justifiées
- [ ] Historique des modifications
- [ ] Sauvegarde automatique

## 🐛 Résolution de problèmes

### Erreur de connexion Supabase
- Vérifiez que les variables dans `.env` sont correctes
- Vérifiez votre connexion internet

### Les langues n'apparaissent pas
- Exécutez `python init_database.py` pour initialiser les langues

### Erreur lors de l'ajout d'un étudiant
- Vérifiez que le trigger PostgreSQL est bien créé dans Supabase

## 📧 Support

Pour toute question ou problème, contactez l'équipe technique de l'Institut Torii.

---

**Version** : 1.0.0
**Date** : 2025
**Développé avec** : Streamlit + Supabase