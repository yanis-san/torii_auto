# ✅ Configuration Finale - Activation Manuelle des Comptes

## Étape 1 : Ajouter la colonne email_confirmed

Dans **Supabase SQL Editor**, exécutez :

```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_confirmed BOOLEAN DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS idx_users_email_confirmed ON users(email_confirmed);
```

## Étape 2 : Désactiver l'envoi automatique d'email

Dans **Supabase Dashboard** :
1. Allez dans **Authentication** → **Settings**
2. Trouvez **"Enable email confirmations"**
3. **Décochez** cette option
4. Sauvegardez

Cela empêche Supabase d'envoyer des emails de confirmation.

## Étape 3 : Redémarrer l'application

```bash
streamlit run app.py
```

## 🎯 Comment ça fonctionne maintenant :

### Pour l'utilisateur :
1. ✅ Crée un compte (formulaire d'inscription)
2. ✅ Voit le message : "Compte créé avec succès! Un administrateur doit activer votre compte avant que vous puissiez vous connecter."
3. ❌ Ne peut PAS se connecter (message : "Votre compte n'a pas encore été activé")

### Pour vous (Admin) :
1. Allez dans **Supabase** → **Table Editor** → **users**
2. Trouvez l'utilisateur créé
3. Cliquez sur la ligne pour l'éditer
4. Changez `email_confirmed` de `false` à `true`
5. Sauvegardez

### Après activation :
6. L'utilisateur peut maintenant se connecter ! ✅

## 📋 Vue de la table users

Vous verrez maintenant ces colonnes :
- id
- email
- first_name
- last_name
- role
- created_at
- updated_at
- **email_confirmed** ← Nouvelle colonne ! (cochez pour activer)

## 🔍 Vérifier un utilisateur :

Dans **Table Editor** → **users** :
- ❌ `email_confirmed = false` : Compte en attente d'activation
- ✅ `email_confirmed = true` : Compte actif, peut se connecter

## 💡 Astuce rapide

Pour activer directement dans SQL :

```sql
-- Activer un utilisateur spécifique
UPDATE users SET email_confirmed = true WHERE email = 'utilisateur@example.com';

-- Activer tous les utilisateurs en attente
UPDATE users SET email_confirmed = true WHERE email_confirmed = false;
```

## ✅ Résumé

1. ✅ Plus d'envoi d'email
2. ✅ Comptes désactivés par défaut (`email_confirmed = false`)
3. ✅ Vous activez manuellement dans Supabase en cochant `email_confirmed`
4. ✅ L'utilisateur peut alors se connecter

Parfait pour un contrôle total sur qui accède à l'application !
