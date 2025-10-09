# 📧 Vérification de la Configuration Email

## 1️⃣ Vérifier que l'utilisateur a été créé

Dans **Supabase Dashboard** :
1. Allez dans **Authentication** → **Users**
2. Cherchez votre email dans la liste
3. Regardez la colonne **"Email Confirmed"**
   - ❌ Si "false" : L'email n'a pas été confirmé
   - ✅ Si "true" : L'email est déjà confirmé

## 2️⃣ Confirmer manuellement l'email (Solution rapide)

Si l'utilisateur existe mais l'email n'est pas confirmé :

1. Dans **Authentication** → **Users**
2. Cliquez sur l'utilisateur
3. Cliquez sur **"Confirm email"** manuellement

Puis essayez de vous connecter !

## 3️⃣ Vérifier la configuration SMTP

Dans **Supabase Dashboard** :
1. **Project Settings** → **Authentication**
2. Section **"SMTP Settings"**
3. Vérifiez si SMTP est configuré :
   - ❌ Si "Not configured" : Supabase utilise son service email (peut être lent ou bloqué)
   - ✅ Si configuré : Vérifiez les paramètres

## 4️⃣ Vérifier les logs d'email

1. Allez dans **Logs** → **Auth Logs**
2. Cherchez des entrées pour votre email
3. Regardez s'il y a des erreurs

## 5️⃣ Solution Alternative : Désactiver la confirmation email

Si vous voulez vous connecter immédiatement sans validation :

### Dans Supabase :
1. **Authentication** → **Settings**
2. **Email Auth** section
3. Désactivez **"Enable email confirmations"**
4. Sauvegardez

### Puis dans le code, simplifiez l'inscription :

Modifiez `auth.py` pour que l'utilisateur puisse se connecter immédiatement.

## 6️⃣ Tester avec un autre email

Essayez avec :
- Gmail
- Outlook
- Un autre service

Parfois les emails Supabase finissent dans les spams !

## ✅ Checklist de Dépannage

- [ ] L'utilisateur apparaît dans Authentication → Users
- [ ] Vérifier les spams / courrier indésirable
- [ ] Attendre 5-10 minutes (les emails peuvent être retardés)
- [ ] Vérifier les logs Auth dans Supabase
- [ ] Confirmer manuellement l'email dans Supabase
- [ ] Essayer avec un autre email
- [ ] Désactiver temporairement la confirmation email
