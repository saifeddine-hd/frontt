# 🔧 **GUIDE DE CONFIGURATION SECRETHAWK**

## 🚀 **DÉMARRAGE RAPIDE**

### **1. Copiez les fichiers d'environnement**
```bash
# Backend
cp apps/api/.env.example apps/api/.env

# Frontend  
cp apps/web/.env.example apps/web/.env
```

### **2. Modifiez les variables OBLIGATOIRES**

#### 🔐 **SÉCURITÉ (CRITIQUE)**
```bash
# Générez une clé secrète forte (64+ caractères)
SECRET_KEY="votre-cle-secrete-super-forte-avec-64-caracteres-minimum-123456"

# Générez une clé de chiffrement Fernet
# Python: from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())
ENCRYPTION_KEY="votre-cle-fernet-44-caracteres-base64-generee"
```

#### 🌐 **URLS DE VOTRE DOMAINE**
```bash
# Remplacez par vos vrais domaines
FRONTEND_URL="https://secrethawk.votre-domaine.com"
BASE_URL="https://api.secrethawk.votre-domaine.com"
VITE_API_URL="https://api.secrethawk.votre-domaine.com/api/v1"
```

### **3. Configuration optionnelle**

#### 🔔 **NOTIFICATIONS DISCORD**
1. Créez un webhook Discord :
   - Serveur Discord → Paramètres → Intégrations → Webhooks
   - Créer un webhook → Copier l'URL
2. Ajoutez l'URL :
```bash
DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/123456789/votre-token-webhook"
```

#### 🗄️ **BASE DE DONNÉES (Production)**
```bash
# PostgreSQL (recommandé pour la production)
DATABASE_URL="postgresql://secrethawk_user:mot_de_passe@localhost:5432/secrethawk_db"

# MySQL
DATABASE_URL="mysql://secrethawk_user:mot_de_passe@localhost:3306/secrethawk_db"
```

#### 📊 **REDIS (Performance)**
```bash
# Pour les sessions et cache en production
REDIS_URL="redis://localhost:6379/0"
```

---

## 🛠️ **INSTALLATION ET DÉPLOIEMENT**

### **Option 1: Docker (Recommandé)**
```bash
# 1. Configurez vos .env
# 2. Lancez avec Docker
docker-compose up -d

# Accès:
# Frontend: http://localhost:3000
# API: http://localhost:8000
```

### **Option 2: Installation manuelle**

#### **Backend (Python)**
```bash
cd apps/api
pip install -r requirements.txt

# Installez Gitleaks
wget https://github.com/trufflesecurity/gitleaks/releases/download/v8.18.0/gitleaks_8.18.0_linux_x64.tar.gz
tar -xzf gitleaks_8.18.0_linux_x64.tar.gz
sudo mv gitleaks /usr/local/bin/

# Lancez l'API
uvicorn main:app --host 0.0.0.0 --port 8000
```

#### **Frontend (React)**
```bash
cd apps/web
npm install
npm run build  # Pour la production
npm run dev    # Pour le développement
```

---

## 🔑 **AUTHENTIFICATION**

### **Utilisateur par défaut**
- **Username:** `admin`
- **Password:** `admin123`

### **Changer le mot de passe**
Modifiez dans `apps/api/core/security.py` :
```python
DEMO_USERS = {
    "admin": {
        "password": hash_password("VOTRE_NOUVEAU_MOT_DE_PASSE"),
        "role": "admin"
    }
}
```

---

## 📋 **CHECKLIST DE CONFIGURATION**

### ✅ **Avant la production**
- [ ] Changé `SECRET_KEY` et `ENCRYPTION_KEY`
- [ ] Configuré les URLs de domaine
- [ ] Installé Gitleaks
- [ ] Configuré la base de données
- [ ] Changé le mot de passe admin
- [ ] Configuré Discord (optionnel)
- [ ] Testé les scans
- [ ] Configuré HTTPS
- [ ] Configuré les sauvegardes

### 🔧 **Variables critiques à vérifier**
```bash
# Ces variables DOIVENT être changées
SECRET_KEY=❌ (par défaut)
ENCRYPTION_KEY=❌ (par défaut)  
FRONTEND_URL=❌ (localhost)
BASE_URL=❌ (localhost)

# Ces variables peuvent rester par défaut
DATABASE_URL=✅ (SQLite OK pour commencer)
GITLEAKS_PATH=✅ (si installé dans /usr/local/bin)
```

---

## 🚨 **SÉCURITÉ IMPORTANTE**

### **🔐 Génération des clés**
```python
# SECRET_KEY (64+ caractères aléatoires)
import secrets
print(secrets.token_urlsafe(64))

# ENCRYPTION_KEY (Fernet)
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

### **🛡️ Bonnes pratiques**
- Utilisez HTTPS en production
- Sauvegardez régulièrement la base de données
- Surveillez les logs d'erreur
- Limitez l'accès réseau à l'API
- Utilisez un reverse proxy (Nginx)

---

## 📞 **SUPPORT**

Si vous avez des problèmes :
1. Vérifiez les logs : `docker-compose logs`
2. Testez l'API : `curl http://localhost:8000/api/v1/health`
3. Vérifiez Gitleaks : `gitleaks version`