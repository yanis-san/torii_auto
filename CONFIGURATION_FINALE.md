# 🔧 Configuration Finale - Supabase Auth

## Étape 1 : Configurer les URLs dans Supabase

1. Allez dans **Supabase Dashboard**
2. **Authentication** → **URL Configuration**
3. Configurez les URLs suivantes :

### Site URL
```
http://localhost:8501
```

### Redirect URLs (ajoutez ces URLs)
```
http://localhost:8501
http://localhost:8501/**
```

4. **Sauvegardez** les modifications

## Étape 2 : Désactiver RLS sur les tables

Dans **SQL Editor**, exécutez :

```sql
-- Désactiver RLS
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE teachers DISABLE ROW LEVEL SECURITY;

-- Nettoyer les politiques
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

## Étape 3 : Tester l'inscription

1. Lancez l'application :
```bash
streamlit run app.py
```

2. Créez un compte :
   - Cliquez sur "Créer un compte"
   - Remplissez le formulaire
   - Validez

3. Vérifiez votre email :
   - Ouvrez l'email de Supabase
   - Cliquez sur le lien de confirmation
   - Vous serez redirigé vers `http://localhost:8501`

4. Connectez-vous :
   - Utilisez vos identifiants
   - Vous êtes connecté !

## ✅ Checklist

- [ ] URLs configurées dans Supabase
- [ ] RLS désactivé (script SQL exécuté)
- [ ] Application redémarrée
- [ ] Compte créé avec succès
- [ ] Email validé
- [ ] Connexion réussie

## 🚨 Si l'erreur RLS persiste

Vérifiez dans Supabase :
1. **Table Editor** → Table `users`
2. Regardez l'icône du cadenas (RLS)
3. Il doit être **OUVERT** (gris)
4. Si fermé (rouge), exécutez à nouveau :
```sql
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
```

## 📧 Format de l'email de validation

L'email contiendra un lien comme :
```
http://localhost:8501/#access_token=...&refresh_token=...
```

Streamlit ignorera les paramètres d'URL mais Supabase validera automatiquement le compte.
