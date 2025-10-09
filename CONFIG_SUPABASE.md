# Configuration Supabase pour l'Application

## 🔧 Étape 1 : Désactiver la validation email (Recommandé pour développement)

1. Allez dans **Supabase Dashboard**
2. **Authentication** → **Settings**
3. Trouvez **"Enable email confirmations"**
4. **Désactivez** cette option
5. Sauvegardez

Cela permet aux utilisateurs de se connecter immédiatement après l'inscription, sans valider l'email.

## 🔓 Étape 2 : Désactiver RLS (Row Level Security)

Exécutez ce script dans **SQL Editor** :

```sql
-- Désactiver RLS sur users
ALTER TABLE users DISABLE ROW LEVEL SECURITY;

-- Désactiver RLS sur teachers
ALTER TABLE teachers DISABLE ROW LEVEL SECURITY;

-- Supprimer toutes les politiques
DROP POLICY IF EXISTS "Users can view own profile" ON users;
DROP POLICY IF EXISTS "Users can update own profile" ON users;
DROP POLICY IF EXISTS "Enable insert for authentication" ON users;
DROP POLICY IF EXISTS "Enable insert during signup" ON users;
DROP POLICY IF EXISTS "Teachers can view own profile" ON teachers;
DROP POLICY IF EXISTS "Admins can view all teachers" ON teachers;
DROP POLICY IF EXISTS "Enable insert for service role" ON teachers;
DROP POLICY IF EXISTS "Enable insert for teachers" ON teachers;
DROP POLICY IF EXISTS "Teachers can view all" ON teachers;
DROP POLICY IF EXISTS "Teachers can update own" ON teachers;
```

## 📧 Option alternative : Configurer correctement l'URL de redirection

Si vous voulez garder la validation email :

1. Dans **Authentication** → **URL Configuration**
2. Ajoutez `http://localhost:8501` dans **Redirect URLs**
3. Configurez **Site URL** : `http://localhost:8501`

## ✅ Vérification

Après ces configurations :
- ✅ Vous pouvez créer un compte
- ✅ Vous pouvez vous connecter immédiatement
- ✅ Pas d'erreur RLS
- ✅ Pas de problème avec l'email de validation

## 🚀 Pour mettre en production plus tard

Quand vous voudrez déployer en production :
1. Réactivez la validation email
2. Configurez les URLs de production
3. Réactivez RLS avec des politiques adaptées
