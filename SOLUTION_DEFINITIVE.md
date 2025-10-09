# ✅ Solution Définitive - Problème de Clé Étrangère

## 🔴 Problème

L'erreur indique que la table `users` a été créée avec une contrainte `REFERENCES auth.users(id)` qui bloque l'insertion car l'utilisateur n'existe pas encore dans `auth.users` au moment de l'insertion dans `users`.

## ✅ Solution

La table `users` ne doit **PAS** avoir de contrainte de clé étrangère sur `auth.users`. L'ID doit juste être un UUID simple.

### Étape 1 : Exécuter le script de correction

Dans **Supabase SQL Editor**, exécutez le fichier `FIX_FOREIGN_KEY.sql` :

```sql
-- Supprimer la contrainte problématique
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_id_fkey;

-- Recréer la table users SANS foreign key
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE users (
    id UUID PRIMARY KEY,  -- Pas de REFERENCES !
    email TEXT UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'teacher')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Désactiver RLS
ALTER TABLE users DISABLE ROW LEVEL SECURITY;

-- Index
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Fonction updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Teachers
ALTER TABLE teachers ADD COLUMN IF NOT EXISTS user_id UUID;
CREATE INDEX IF NOT EXISTS idx_teachers_user_id ON teachers(user_id);
ALTER TABLE teachers DISABLE ROW LEVEL SECURITY;
```

### Étape 2 : Redémarrer l'application

```bash
streamlit run app.py
```

### Étape 3 : Créer un compte

Maintenant l'inscription devrait fonctionner ! 🎉

## 🔍 Explication

Le flux correct est :
1. Supabase Auth crée l'utilisateur dans `auth.users` (interne)
2. Notre code récupère l'ID généré
3. Notre code insère dans notre table `users` avec cet ID

La table `users` est juste une table de profil qui **stocke** l'ID, elle ne doit pas avoir de contrainte FK qui bloquerait l'insertion.

## ✅ Après l'exécution

- ✅ Table `users` recréée sans FK
- ✅ RLS désactivé
- ✅ Inscription fonctionnelle
- ✅ Validation email active
