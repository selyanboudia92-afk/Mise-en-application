# 📒 Mon carnet de bord

**Nom :** 

**Prénom :** 

**Adresse de mon site :** https://______.pythonanywhere.com

**Adresse de mon dépôt GitHub :** https://github.com/selyanboudia92-afk/Mise-en-application

> Modifiez ce fichier directement sur GitHub (icône crayon ✏️) pour répondre aux questions de chaque exercice.
> Écrivez avec vos propres mots : une réponse courte et juste vaut mieux qu'un long copier-coller ! 🙂

---

## 🟢 Exercice 1 — Explorer la base en SQL

1. Expliquez avec vos mots la différence entre une **table**, une **colonne** et une **ligne**.

   > Une **table** est un tableau qui regroupe toutes les données sur un même sujet (ex. : les clients). Une **colonne** est une catégorie d'information commune à tous les éléments de la table (le nom, l'adresse…). Une **ligne** est une entrée : un élément précis (un client) avec toutes ses informations.

2. À quoi sert la clé primaire `id` ? Pourquoi ne pas simplement identifier un client par son nom ?

   > L'`id` identifie chaque ligne de façon **unique** et ne change jamais. On n'utilise pas le nom car deux clients peuvent avoir le même nom (deux DUPONT), et un nom peut changer (mariage, faute de frappe) : on ne saurait plus de quel client on parle.

3. Pourquoi votre client ajouté en console est-il apparu sur le site ?

   > Parce que la console `sqlite3` et le site Flask lisent et écrivent dans **le même fichier** `database.db` sur le serveur. Le site n'a pas de copie des données : à chaque visite de `/consultation/`, il refait un `SELECT` et voit donc les nouvelles lignes. L'`id` a été choisi automatiquement par SQLite (`AUTOINCREMENT`) et `created` rempli par `DEFAULT CURRENT_TIMESTAMP`.

4. Que signifie `NOT NULL` dans `schema.sql` ? Quelle erreur avez-vous obtenue avec `INSERT INTO clients (nom) VALUES ('TEST');` ?

   > `NOT NULL` est une contrainte : la colonne doit obligatoirement contenir une valeur, on ne peut pas la laisser vide. La requête ne donne que le nom, donc SQLite refuse : `Runtime error: NOT NULL constraint failed: clients.prenom` (le prénom, puis l'adresse, sont obligatoires).

🧩 **Défi** — mes requêtes / ma solution :

   > ```sql
   > -- Les 3 derniers clients enregistrés
   > SELECT * FROM clients ORDER BY id DESC LIMIT 3;
   > -- Les clients dont le prénom commence par A
   > SELECT * FROM clients WHERE prenom LIKE 'A%';
   > -- Le nombre de clients qui habitent à Paris
   > SELECT COUNT(*) FROM clients WHERE adresse LIKE '%Paris%';
   > ```

---

## 🟢 Exercice 2 — Afficher les données proprement

1. Décrivez avec vos mots le trajet d'une requête, du navigateur jusqu'à la base de données, puis le retour.

   > Le navigateur envoie une requête HTTP `GET /consultation/` au serveur. Flask trouve la fonction associée à cette route (`ReadBDD`), qui ouvre une connexion à `database.db` et exécute `SELECT * FROM clients`. SQLite renvoie les lignes à Python, Flask les passe au template `read_data.html` qui fabrique le HTML (le moteur Jinja remplace les `{% for %}`), puis la page HTML est renvoyée au navigateur. Le navigateur ne reçoit **que du HTML** : jamais de SQL ni de Python.

2. Pourquoi faut-il **fermer** la connexion (`conn.close()`) après chaque requête ?

   > Pour libérer les ressources du serveur et le fichier de la base. Une connexion restée ouverte (surtout après une écriture) peut **verrouiller** la base : les autres requêtes obtiennent alors `database is locked`.

3. Quel est l'avantage d'écrire `row['nom']` plutôt que `row[2]` ? (Pensez à ce qui arriverait si on ajoutait une colonne au milieu de la table.)

   > Le code est plus lisible (on sait ce qu'on affiche) et plus robuste : si on ajoute ou déplace une colonne, `row[2]` désignerait une autre information alors que `row['nom']` continue à désigner le nom.

4. Pourquoi est-il préférable de trier avec `ORDER BY` dans la requête SQL plutôt qu'en Python ?

   > La base de données est optimisée pour trier (elle peut utiliser des index), c'est moins de code à écrire et ça reste efficace même avec beaucoup de données. On peut aussi combiner le tri avec `LIMIT` pour ne récupérer que les lignes utiles.

---

## 🟢 Exercice 3 — Rechercher un client

1. Quelle est la différence entre `WHERE nom = 'DUPONT'` et `WHERE nom LIKE '%DUP%'` ?

   > `=` cherche une égalité **exacte** (et sensible à la casse : `dupont` ne trouve pas `DUPONT`). `LIKE '%DUP%'` cherche les noms qui **contiennent** « DUP » n'importe où (`%` = n'importe quelle suite de caractères), et sans tenir compte de la casse pour les lettres non accentuées dans SQLite.

2. Expliquez avec vos mots ce qu'est une **injection SQL**. Qu'est-ce qu'un pirate pourrait faire de pire qu'afficher tous les clients ?

   > C'est quand le texte tapé par l'utilisateur est collé directement dans la requête SQL : le pirate peut alors écrire du SQL qui sera exécuté. Avec `x' OR '1'='1`, la condition devient toujours vraie et tous les clients s'affichent. Il pourrait faire bien pire : lire d'autres tables (mots de passe), modifier ou supprimer des données (`DELETE`, `DROP TABLE`), se connecter sans mot de passe…

3. Pourquoi la version avec `?` est-elle protégée contre l'injection ?

   > Avec `?`, la requête et les valeurs sont envoyées **séparément** à SQLite. La valeur est toujours traitée comme une simple donnée (du texte), jamais comme du code SQL : `x' OR '1'='1` est cherché tel quel comme nom, et ne trouve rien.

4. Pour la recherche, on a utilisé `method="get"`. Quel avantage pour l'utilisateur ? (Indice : favoris, partage de lien.)

   > Les paramètres apparaissent dans l'URL (`/recherche?q=ma`) : on peut mettre la recherche en favori, partager le lien, utiliser le bouton « précédent » ou recharger la page sans avertissement. C'est adapté car une recherche ne modifie pas les données.

🧩 **Défi** — mes requêtes / ma solution :

   > On ne peut pas mettre un nom de colonne dans un `?`. J'ai donc utilisé une **liste blanche** en Python : `TRIS_AUTORISES = {'nom': 'nom, prenom', 'prenom': 'prenom, nom', 'created': 'created DESC'}`. La valeur reçue (`?tri=...`) sert uniquement de **clé** : si elle n'est pas dans le dictionnaire, on trie par nom. Seul un texte écrit par moi entre dans le SQL, donc aucune injection possible. (Voir `recherche()` dans `flask_app.py` et la liste déroulante dans `recherche.html`.)

---

## 🔵 Exercice 4 — Enregistrer un client

1. Quelles étaient les deux anomalies du formulaire d'origine, et d'où venaient-elles ?

   > 1) **L'adresse valait toujours « ICI »** : `formulaire.html` n'avait pas de champ `adresse` et l'`INSERT` de `enregistrer_client()` écrivait `"ICI"` en dur. 2) **La date de création était absurde (`1002938`)** : l'`INSERT` remplissait lui-même la colonne `created` avec ce nombre fixe au lieu de laisser SQLite utiliser `DEFAULT CURRENT_TIMESTAMP`. (Il y avait aussi deux fonctions pour la même route `/enregistrer_client` en GET ; je les ai fusionnées en une seule.)

2. Pourquoi la validation côté **navigateur** (`required`) ne suffit-elle pas ? Pourquoi la garder quand même ?

   > Le navigateur est sous le contrôle de l'utilisateur : on peut supprimer `required` avec F12, ou envoyer la requête avec un script ou `curl`. Seule la validation **côté serveur** est fiable. On garde `required` pour le confort : l'utilisateur est prévenu immédiatement, sans aller-retour avec le serveur.

3. À quoi sert `conn.commit()` ? Que se passe-t-il sans lui ?

   > `commit()` valide définitivement la transaction : les modifications sont écrites dans le fichier. Sans lui, l'`INSERT` est annulé à la fermeture de la connexion : le client n'apparaît pas dans `/consultation/`.

4. Pourquoi redirige-t-on vers `/consultation/` après l'enregistrement, au lieu d'afficher directement une page ? (Indice : essayez d'appuyer sur F5 après l'envoi.)

   > C'est le principe *Post/Redirect/Get* : après le POST, le serveur répond `302` et le navigateur fait un nouveau GET. Si l'utilisateur appuie sur F5, il recharge seulement la page de consultation au lieu de renvoyer le formulaire, ce qui créerait un **doublon** du client.

🧩 **Défi** : après l'`INSERT`, je récupère `cursor.lastrowid` et je redirige vers `/fiche_client/<nouvel id>`.

---

## 🔵 Exercice 5 — Modifier et supprimer

1. Que signifie CRUD ? Donnez la requête SQL correspondant à chaque lettre.

   > **C**reate → `INSERT INTO clients (...) VALUES (...)` · **R**ead → `SELECT * FROM clients` · **U**pdate → `UPDATE clients SET ... WHERE id = ?` · **D**elete → `DELETE FROM clients WHERE id = ?`.

2. Que se passe-t-il si l'on oublie le `WHERE` dans un `UPDATE` ou un `DELETE` ? À quoi servent `BEGIN` et `ROLLBACK` ?

   > La requête s'applique à **toutes les lignes** de la table : tous les clients s'appellent `OUPS`, ou tous sont supprimés. `BEGIN` démarre une transaction (les modifications restent provisoires), `ROLLBACK` l'annule et remet la base dans l'état d'avant le `BEGIN` (`COMMIT` la validerait).

3. Pourquoi ne faut-il **jamais** supprimer des données avec une requête GET (un simple lien) ? (Indice : les moteurs de recherche et certains navigateurs « visitent » les liens à l'avance.)

   > Une requête GET doit seulement **lire**. Les robots des moteurs de recherche, le préchargement des navigateurs ou un simple lien piégé envoyé à un admin pourraient « visiter » le lien et supprimer des données sans que personne n'ait cliqué. Avec un formulaire POST (et une confirmation), la suppression est volontaire.

4. Une fois un `id` supprimé, pourquoi est-il préférable qu'il ne soit jamais réattribué à un autre client ?

   > Des liens, favoris, factures ou autres tables (commandes) peuvent encore faire référence à cet ancien `id`. S'il était réutilisé, ces références pointeraient vers un **autre client** (mélange de données). Grâce à `AUTOINCREMENT`, SQLite ne réutilise jamais un numéro.

🧩 **Défi (suppression logique)** : avec une colonne `actif`, on ne perd rien : on garde l'historique (commandes, factures), on peut annuler une suppression par erreur, et on ne casse pas les clés étrangères. Il faut juste penser à ajouter `WHERE actif = 1` dans les listes.

---

## 🟣 Exercice 6 — Faire évoluer la base

1. Quelle est la différence entre le **schéma** d'une base et ses **données** ? Où se trouve chacun ?

   > Le **schéma** est la structure (tables, colonnes, types, contraintes) : il est décrit dans `schema.sql` (dans GitHub) et appliqué dans la base. Les **données** sont le contenu (les clients saisis) : elles n'existent que dans `database.db`, sur le serveur.

2. Pourquoi ne faut-il pas relancer `create_db.py` sur une application en production ?

   > Parce que `schema.sql` commence par `DROP TABLE IF EXISTS` : toutes les tables sont effacées puis recréées avec les données d'exemple. Toutes les données réelles des utilisateurs seraient **définitivement perdues**.

3. Pourquoi est-il important de garder `schema.sql` à jour, même si on a modifié la base avec `ALTER TABLE` ?

   > Pour que le code reflète la vraie structure : si on (ou un collègue) recrée la base, en local ou sur un nouveau serveur, elle doit avoir les mêmes colonnes que la production, sinon le code plantera (`no such column: telephone`). C'est aussi la documentation de la base.

4. Pour ajouter **une** information, combien de fichiers avez-vous dû modifier ? Lesquels ?

   > Cinq fichiers du dépôt : `schema.sql` (structure), `formulaire.html` (saisie), `flask_app.py` (`INSERT` et `UPDATE`), `read_data.html` (affichage) et `modifier_client.html` (modification) — plus la base du serveur elle-même (`ALTER TABLE`, rangé dans `migrations/001_ajout_telephone.sql`), et `create_db.py` pour les données d'exemple. Une seule information traverse toute la chaîne !

🧩 **Défi** : j'ai créé le dossier `migrations/` (`001_ajout_telephone.sql`, `002_commandes.sql`, `003_bibliotheque.sql`). L'historique permet de savoir exactement quelles modifications appliquer, dans quel ordre, sur chaque serveur (local, test, production), sans jamais tout recréer.

> Le déploiement ignore `*.db` et `.gitignore` contient `*.db` pour que la base du serveur ne soit **jamais** écrasée par le code, et que les données des utilisateurs ne soient pas publiées sur GitHub. Pour les anciens clients sans téléphone, j'affiche `-` avec `{{ row['telephone'] or '-' }}`.

---

## 🟣 Exercice 7 — Relier deux tables

1. Qu'est-ce qu'une **clé étrangère** ? Dans quelle table se trouve-t-elle ici, et pourquoi pas dans l'autre ?

   > C'est une colonne qui contient l'`id` d'une ligne d'une **autre table** : elle crée le lien entre les deux. Ici c'est `commandes.client_id`. Elle est dans `commandes` car une commande appartient à **un seul** client, alors qu'un client peut avoir **plusieurs** commandes : on ne pourrait pas ranger plusieurs numéros de commande dans une seule case de `clients`.

2. Pourquoi est-ce une mauvaise idée de créer des colonnes `commande1`, `commande2`… dans la table `clients` ?

   > On ne sait pas combien prévoir (et s'il y en a 50 ?), la plupart des cases seraient vides, il faudrait modifier la structure à chaque nouveau maximum, et les requêtes deviendraient impossibles (chercher un produit dans 50 colonnes, faire un total…).

3. À quoi sert un `JOIN` ? Et un `GROUP BY` ?

   > `JOIN` combine les lignes de deux tables grâce à la clé étrangère (ex. : afficher le nom du client à côté de chaque commande). `LEFT JOIN` garde aussi les lignes sans correspondance (clients sans commande). `GROUP BY` regroupe les lignes qui ont la même valeur pour calculer un résultat par groupe avec `COUNT`, `SUM`… (nombre de commandes et total par client). `COALESCE(SUM(...), 0)` affiche 0 au lieu de `NULL`.

4. Pour la bibliothèque, quelles tables imaginez-vous ? Lesquelles contiendront des clés étrangères ?

   > Trois tables : `livres`, `utilisateurs` et `emprunts`. Seule `emprunts` contient des clés étrangères : `livre_id` (→ `livres.id`) et `utilisateur_id` (→ `utilisateurs.id`). Un emprunt relie un livre et un utilisateur.

> Avec `PRAGMA foreign_keys = ON`, SQLite refuse de supprimer un client qui a des commandes : c'est une bonne chose (pas de commandes orphelines). Le bloc `finally` ferme la connexion **dans tous les cas**, même si une erreur se produit ou si on fait un `return`, ce qui évite `database is locked`.

🧩 **Défi** : formulaire « Nouvelle commande » sur la fiche client (route `POST /fiche_client/<id>/commandes`) et message « Impossible : ce client a N commande(s) » avec un lien vers sa fiche.

---

## 🔴 Exercice 8 — Contrôle d'accès

1. Quelle est la différence entre **authentification** et **autorisation** ?

   > L'**authentification** vérifie **qui** vous êtes (login + mot de passe). L'**autorisation** vérifie **ce que vous avez le droit de faire** une fois connecté, selon votre rôle (`user` peut consulter, `admin` peut aussi modifier et supprimer).

2. Où est stockée la session ? Comment le serveur sait-il qui vous êtes à chaque nouvelle requête ?

   > Avec Flask, la session est stockée **dans un cookie** `session` du navigateur. Le navigateur renvoie automatiquement ce cookie à chaque requête ; le serveur vérifie sa **signature** (faite avec `app.secret_key`) puis lit dedans l'utilisateur et son rôle. Le cookie est signé mais pas chiffré : on peut le lire, mais pas le modifier sans connaître la clé secrète (la signature ne correspondrait plus).

3. Pourquoi masquer un bouton dans le HTML ne suffit-il pas à protéger une action ?

   > Le HTML est modifiable par l'utilisateur (F12) et on peut envoyer la requête directement (`curl`, `fetch`). Cacher le bouton est du confort ; la vraie protection est la vérification du rôle **dans la route, côté serveur** (`if not a_le_role('admin'): ... 403`).

4. Que signifient les codes `302` et `403` ? Dans quel cas votre application renvoie-t-elle chacun d'eux ?

   > `302` = **redirection** : quand un visiteur non connecté ouvre une page protégée, il est renvoyé vers `/authentification` (et aussi après un enregistrement, ou après la connexion). `403` = **interdit** : l'utilisateur est connecté mais n'a pas le bon rôle, par exemple un `user` qui ouvre `/enregistrer_client`, `/livres/ajouter` ou `/utilisateurs`.

5. Le mot de passe `password` est écrit en clair dans `flask_app.py`, sur un dépôt **public**. Quel est le risque ? Quelle solution avez-vous déjà rencontrée dans cet atelier pour cacher une information sensible ?

   > N'importe qui peut lire le dépôt et se connecter en admin (et même falsifier les cookies si la `secret_key` est publique). La solution vue dans l'atelier : les **secrets** (GitHub Actions secrets, variables d'environnement). J'ai déplacé les comptes dans la table `utilisateurs` avec des mots de passe **hachés**, et la clé secrète peut être fournie par la variable d'environnement `FLASK_SECRET_KEY`.

🧩 **Défi** : table `utilisateurs (id, login, nom, prenom, mot_de_passe_hash, role)`, `generate_password_hash` à la création et `check_password_hash` à la connexion. On stocke un *hash* car il est impossible de retrouver le mot de passe à partir de lui : si la base est volée, le pirate n'obtient pas directement les mots de passe (que les gens réutilisent souvent sur d'autres sites). Le hachage `scrypt` avec sel rend aussi les attaques par dictionnaire très lentes.

---

## 🔴 Exercice 9 — Créer une API

1. Quelle est la différence entre une page HTML et une réponse JSON ? À qui chacune est-elle destinée ?

   > Une page HTML (`Content-Type: text/html`) contient les données **et leur mise en forme** : elle est destinée à un **humain** dans un navigateur. Une réponse JSON (`Content-Type: application/json`) contient seulement les **données brutes et structurées** : elle est destinée à un **programme** (appli mobile, autre site, script JavaScript).

2. Que signifient les codes `200`, `201`, `400`, `401` et `404` renvoyés par votre API ?

   > `200` OK, la requête a réussi · `201` Created, une ressource (un client, un emprunt) a été **créée** · `400` Bad Request, les données envoyées sont incomplètes ou invalides · `401` Unauthorized, il faut être authentifié (admin) · `404` Not Found, la ressource demandée n'existe pas. (J'utilise aussi `409` Conflict quand une règle est violée, ex. livre indisponible.)

3. Pourquoi une API renvoie-t-elle une erreur JSON plutôt qu'une redirection vers la page de connexion ?

   > Le client d'une API est un programme : il ne sait pas remplir un formulaire HTML. Il attend du JSON avec un code d'erreur clair (`401`) qu'il peut tester pour réagir (afficher un message, demander la connexion). Une redirection lui renverrait une page HTML incompréhensible.

4. Citez une application de votre téléphone qui, selon vous, utilise une API. Quelles données échange-t-elle ?

   > Une application météo : elle envoie ma position à une API et reçoit en JSON la température, le vent, les prévisions heure par heure. Autre exemple : l'appli de la SNCF qui échange les gares, horaires, retards et billets.

🧩 **Défi** : `DELETE /api/clients/<id>` (admin), `/api/clients?q=dup`, et la page `/clients_js` qui charge la liste avec `fetch` et la filtre en direct sans recharger la page.

---

## 📚 Projet bibliothèque

1. Pourquoi ne supprime-t-on pas un emprunt quand le livre est rendu ?

   > Pour garder **l'historique** : savoir qui a emprunté quoi et quand (en cas de livre abîmé), voir son historique de lecture, faire des statistiques (livres les plus empruntés, emprunts par mois, genres préférés) et repérer les retards. Il suffit de remplir `date_retour` : un emprunt « en cours » est un emprunt où `date_retour IS NULL`.

2. Pourquoi calculer la disponibilité d'un livre plutôt que de la stocker dans une colonne ?

   > Une colonne `nb_disponibles` serait une **information en double** qu'il faudrait mettre à jour à chaque emprunt, retour, changement de stock… Le moindre oubli ou bug (erreur au milieu d'une opération, deux emprunts simultanés) la rendrait fausse et incohérente avec les emprunts. En la calculant (`nb_exemplaires - COUNT(emprunts en cours)`), elle est **toujours juste**.

3. Quelle a été la plus grande difficulté rencontrée pendant le projet, et comment l'avez-vous surmontée ?

   > Faire respecter les règles de gestion sans erreur 500 : par exemple supprimer un livre ou un utilisateur alors qu'il existe des emprunts (la clé étrangère bloque). J'ai regroupé les règles dans des fonctions (`emprunter_livre`, `rendre_livre`) qui vérifient tout **avant** d'écrire (R1 disponibilité, R2 maximum 3 livres, R3 livre emprunté) et renvoient un message clair avec un code `409`, et j'ai utilisé `try / finally` pour toujours fermer la connexion. Ces mêmes fonctions servent aux pages HTML **et** à l'API.

4. Quelles fonctionnalités n'avez-vous pas eu le temps de réaliser ? Comment vous y prendriez-vous ?

   > La **réservation** d'un livre indisponible : une table `reservations (id, livre_id, utilisateur_id, date_reservation, date_notification)` ; au retour d'un livre, on chercherait la plus ancienne réservation et on afficherait un bandeau à l'utilisateur (ou on lui enverrait un e-mail). Les **recommandations** : une requête qui cherche les livres empruntés par les autres lecteurs du même livre (`JOIN` de `emprunts` sur lui-même). Un **graphique** des statistiques avec Chart.js qui lirait une route d'API.

---

## 🏁 Pour conclure

En quelques phrases, expliquez à un ami ce qui se passe entre le moment où il clique sur « Enregistrer » dans un formulaire et celui où l'information s'affiche dans une liste :

> Quand tu cliques sur « Enregistrer », ton navigateur envoie les champs du formulaire au serveur dans une requête **POST**. Sur le serveur, Flask appelle la fonction liée à cette adresse : elle vérifie que tu as le droit (session, rôle) et que les champs sont bien remplis, puis elle exécute une requête SQL `INSERT` (avec des `?` pour éviter l'injection) et fait `commit()` pour l'écrire dans le fichier de la base SQLite. Le serveur répond ensuite par une **redirection** (302) vers la page de la liste. Ton navigateur demande alors cette page en **GET** : Flask fait un `SELECT` dans la base, remplit un modèle HTML avec les lignes obtenues, et te renvoie la page… où ton information apparaît.
