# 🔐 Guide d'Authentification Supabase

Ce guide explique comment configurer et utiliser l'authentification Supabase Auth dans l'application Institut Torii.

## 📋 Prérequis

- Un compte Supabase actif
- La base de données déjà configurée avec les tables principales
- L'application Streamlit installée

## 🚀 Configuration Étape par Étape

### 1. Activer Supabase Auth

Dans votre tableau de bord Supabase :

1. Allez dans **Authentication** → **Settings**
2. Vérifiez que **Enable Email Signup** est activé
3. Configurez l'URL de redirection (optionnel pour réinitialisation de mot de passe)

### 2. Exécuter le Script SQL

1. Ouvrez **SQL Editor** dans Supabase
2. Créez une nouvelle query
3. Copiez le contenu du fichier `setup_supabase_auth.sql`
4. Exécutez le script (bouton Run)

Ce script va :
- ✅ Créer la table `users` pour stocker les profils
- ✅ Modifier la table `teachers` pour ajouter `user_id`
- ✅ Configurer les politiques RLS (Row Level Security)
- ✅ Créer les triggers automatiques

### 3. Vérifier la Configuration

Après l'exécution du script, vérifiez dans **Table Editor** :

- Table `users` créée avec les colonnes : id, email, first_name, last_name, role
- Table `teachers` a une nouvelle colonne `user_id`
- Les politiques RLS sont actives (cadenas fermé sur les tables)

### 4. Créer le Premier Compte Admin

1. Lancez l'application :
```bash
streamlit run app.py
```

2. Cliquez sur **"Créer un compte"**

3. Remplissez le formulaire :
   - Prénom et Nom
   - Email (utilisez un email valide)
   - Mot de passe (minimum 6 caractères)
   - Type de compte : **Administrateur**

4. Validez le formulaire

5. **Important** : Vérifiez votre boîte mail pour confirmer l'email
   - Supabase envoie un email de confirmation
   - Cliquez sur le lien de confirmation
   - Vous pouvez maintenant vous connecter

### 5. Première Connexion

1. Retournez à l'application
2. Entrez votre email et mot de passe
3. Cliquez sur **"Se connecter"**

## 👥 Créer des Comptes Enseignants

### Méthode 1 : Via l'interface (Recommandé)

1. Connectez-vous en tant qu'Admin
2. Allez dans **👨‍🏫 Enseignants** → **➕ Ajouter**
3. Ajoutez l'enseignant (nom, prénom, email)
4. L'enseignant doit ensuite :
   - Aller sur l'application
   - Cliquer sur "Créer un compte"
   - S'inscrire avec le **même email**
   - Choisir le type "Enseignant"
   - Valider son email
   - Se connecter

### Méthode 2 : Invitation directe

1. L'enseignant crée son compte directement sur l'application
2. Choisit le type "Enseignant"
3. Une fois inscrit, l'admin peut l'assigner aux groupes

## 🔑 Fonctionnalités d'Authentification

### Connexion
- Email + Mot de passe
- Validation automatique du rôle
- Session persistante

### Inscription
- Création de compte avec validation email
- Choix du rôle (Admin ou Enseignant)
- Création automatique du profil

### Mot de passe oublié
- Cliquez sur "Mot de passe oublié ?"
- Entrez votre email
- Recevez un email de réinitialisation
- Suivez le lien pour définir un nouveau mot de passe

### Gestion du profil
- Accédez à **👤 Mon Profil**
- Modifiez vos informations (prénom, nom)
- Changez votre mot de passe
- Consultez vos statistiques (pour enseignants)

## 🛡️ Sécurité

### Row Level Security (RLS)

Les politiques RLS sont activées pour protéger les données :

- **users** : Chaque utilisateur ne peut voir/modifier que son propre profil
- **teachers** : Les enseignants voient leur profil, les admins voient tous les profils
- Les données sensibles sont protégées au niveau de la base de données

### Meilleures Pratiques

✅ **À FAIRE** :
- Utilisez des mots de passe forts (minimum 8 caractères, incluant chiffres et caractères spéciaux)
- Validez toujours votre email après inscription
- Changez régulièrement votre mot de passe
- Ne partagez jamais vos identifiants

❌ **À ÉVITER** :
- N'utilisez pas le même mot de passe pour plusieurs comptes
- Ne stockez pas les mots de passe en clair
- Ne donnez pas vos identifiants admin à des enseignants

## 🔧 Dépannage

### Problème : "Email déjà utilisé"
**Solution** : Cet email est déjà enregistré. Utilisez la fonction "Mot de passe oublié" pour réinitialiser votre accès.

### Problème : "Email ou mot de passe incorrect"
**Solutions** :
- Vérifiez que vous avez validé votre email
- Vérifiez la casse (majuscules/minuscules)
- Utilisez "Mot de passe oublié" si besoin

### Problème : Email de confirmation non reçu
**Solutions** :
- Vérifiez vos spams
- Attendez quelques minutes
- Vérifiez que l'email est correct
- Dans Supabase, allez dans **Authentication** → **Users** pour voir si l'utilisateur existe

### Problème : "Informations utilisateur non trouvées"
**Solution** : La table `users` n'a pas été créée correctement. Re-exécutez le script `setup_supabase_auth.sql`.

### Problème : L'enseignant ne peut pas se connecter
**Vérifications** :
1. Le compte existe dans Supabase Auth
2. L'email est validé
3. Une entrée existe dans la table `users` avec `role = 'teacher'`
4. Une entrée existe dans la table `teachers` avec le même email et `user_id` rempli

## 📊 Structure des Tables

### Table `users`
```sql
id          UUID    -- Référence à auth.users
email       TEXT    -- Email de l'utilisateur
first_name  TEXT    -- Prénom
last_name   TEXT    -- Nom
role        TEXT    -- 'admin' ou 'teacher'
created_at  TIMESTAMP
updated_at  TIMESTAMP
```

### Liaison avec `teachers`
```sql
-- Dans la table teachers
user_id     UUID    -- Référence vers users.id
```

## 🔄 Migration depuis l'Ancien Système

Si vous aviez des enseignants créés avant l'authentification :

1. Exécutez le script SQL
2. Les enseignants doivent créer leur compte
3. Lors de l'inscription avec le même email :
   - Le système créera l'entrée `users`
   - Liera automatiquement avec l'entrée existante dans `teachers`

## 💡 Conseils

1. **Créez toujours un compte admin en premier**
2. **Gardez les identifiants admin en sécurité**
3. **Configurez les emails Supabase** pour un meilleur branding
4. **Testez la réinitialisation de mot de passe** avant de mettre en production
5. **Documentez les accès** pour votre équipe

## 📧 Configuration Avancée des Emails

Pour personnaliser les emails envoyés par Supabase :

1. Allez dans **Authentication** → **Email Templates**
2. Personnalisez les templates :
   - Confirmation email
   - Reset password
   - Magic link
3. Ajoutez votre logo et couleurs

## 🎯 Récapitulatif

1. ✅ Exécuter `setup_supabase_auth.sql` dans Supabase
2. ✅ Créer le premier compte admin via l'interface
3. ✅ Valider l'email de confirmation
4. ✅ Se connecter et tester les fonctionnalités
5. ✅ Créer des comptes enseignants selon les besoins

---

**En cas de problème**, consultez les logs de Supabase dans **Logs** → **Auth Logs** pour diagnostiquer les erreurs d'authentification.
