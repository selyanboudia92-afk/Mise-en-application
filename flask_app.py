# ---------------------------------------------------------------
#  Atelier Flask + SQLite
# ---------------------------------------------------------------
#  Ce fichier est le "cerveau" de votre application : il reçoit
#  les demandes des navigateurs, interroge la base de données
#  et fabrique les réponses.
#
#  Plan du fichier :
#    1. Configuration et outils communs (connexion, rôles)
#    2. Authentification (exercice 8)
#    3. Gestion des clients : lecture, recherche, CRUD (exercices 2 à 6)
#    4. Commandes et statistiques (exercice 7)
#    5. API clients (exercice 9)
#    6. Projet bibliothèque : livres, emprunts, utilisateurs, API
# ---------------------------------------------------------------

import os
import sqlite3

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# La clé secrète signe le cookie de session. En production, on la range
# dans une variable d'environnement plutôt que dans le code (dépôt public !).
app.secret_key = os.environ.get('FLASK_SECRET_KEY', b'_5#y2L"F4Q8z\n\xec]/')

# Chemin ABSOLU vers la base de données.
# Sur PythonAnywhere, le serveur ne démarre pas forcément dans le dossier
# du projet : un simple 'database.db' créerait une base vide ailleurs !
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'database.db')

MAX_EMPRUNTS = 3          # règle R2
DUREE_EMPRUNT_JOURS = 21  # date de retour prévue = aujourd'hui + 21 jours


# ===============================================================
#  1. Outils communs
# ===============================================================

def get_db():
    """Ouvre une connexion à la base de données SQLite."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row               # pour écrire row['nom'] au lieu de row[2]
    conn.execute('PRAGMA foreign_keys = ON')     # faire respecter les clés étrangères
    return conn


def est_authentifie():
    """Renvoie True si l'utilisateur s'est authentifié."""
    return session.get('authentifie')


def a_le_role(*roles):
    """Renvoie True si l'utilisateur connecté a l'un des rôles indiqués."""
    return session.get('role') in roles


def message(titre, texte, code=200, lien=None, texte_lien=None):
    """Affiche une page de message (erreur ou information) avec un code HTTP."""
    return render_template('message.html', titre=titre, texte=texte,
                           lien=lien, texte_lien=texte_lien), code


def acces_refuse():
    return message('Accès refusé', 'Cette page est réservée aux administrateurs.', 403)


@app.context_processor
def infos_utilisateur():
    """Variables disponibles dans TOUS les templates (bandeau de retard)."""
    nb_retards = 0
    if session.get('utilisateur_id'):
        conn = get_db()
        try:
            nb_retards = conn.execute(
                "SELECT COUNT(*) FROM emprunts WHERE utilisateur_id = ? "
                "AND date_retour IS NULL AND date_retour_prevue < date('now')",
                (session['utilisateur_id'],)).fetchone()[0]
        except sqlite3.OperationalError:
            nb_retards = 0  # table pas encore créée sur le serveur
        finally:
            conn.close()
    return {'nb_retards': nb_retards}


@app.route('/')
def hello_world():
    return render_template('hello.html')


# ===============================================================
#  2. Authentification (exercice 8 + défi : comptes en base, hachés)
# ===============================================================

@app.route('/lecture')
def lecture():
    if not est_authentifie():
        # Rediriger vers la page d'authentification si l'utilisateur n'est pas authentifié
        return redirect(url_for('authentification'))
    return message('Bravo', f"Vous êtes authentifié en tant que {session['utilisateur']} "
                            f"(rôle : {session['role']}).")


@app.route('/authentification', methods=['GET', 'POST'])
def authentification():
    if request.method == 'POST':
        login = request.form.get('username', '').strip()
        mot_de_passe = request.form.get('password', '')

        conn = get_db()
        compte = conn.execute('SELECT * FROM utilisateurs WHERE login = ?', (login,)).fetchone()
        conn.close()

        if compte and check_password_hash(compte['mot_de_passe_hash'], mot_de_passe):
            session.clear()
            session['authentifie'] = True
            session['utilisateur'] = compte['login']
            session['utilisateur_id'] = compte['id']
            session['role'] = compte['role']
            return redirect(url_for('hello_world'))
        return render_template('formulaire_authentification.html', error=True), 401

    return render_template('formulaire_authentification.html', error=False)


@app.route('/deconnexion')
def deconnexion():
    session.clear()
    return redirect('/')


# ===============================================================
#  3. Les clients (exercices 2 à 6)
# ===============================================================

@app.route('/consultation/')
def ReadBDD():
    if not a_le_role('user', 'admin'):
        return redirect(url_for('authentification'))
    conn = get_db()
    data = conn.execute('SELECT * FROM clients ORDER BY nom;').fetchall()
    conn.close()
    return render_template('read_data.html', data=data, titre='Liste des clients')


@app.route('/fiche_client/<int:post_id>')
def Readfiche(post_id):
    if not a_le_role('user', 'admin'):
        return redirect(url_for('authentification'))
    conn = get_db()
    client = conn.execute('SELECT * FROM clients WHERE id = ?', (post_id,)).fetchone()
    commandes = conn.execute('SELECT * FROM commandes WHERE client_id = ? ORDER BY date_commande DESC',
                             (post_id,)).fetchall()
    conn.close()
    if client is None:
        return message('Client introuvable', f"Aucun client n°{post_id}.", 404)
    return render_template('fiche_client.html', client=client, commandes=commandes)


@app.route('/fiche_nom/<nom>')
def fiche_nom(nom):
    if not a_le_role('user', 'admin'):
        return redirect(url_for('authentification'))
    conn = get_db()
    # Requête PARAMÉTRÉE : le "?" protège contre l'injection SQL
    data = conn.execute('SELECT * FROM clients WHERE nom = ?', (nom,)).fetchall()
    conn.close()
    return render_template('read_data.html', data=data, titre=f'Clients nommés « {nom} »')


# Défi exercice 3 : les noms de colonnes ne peuvent pas être passés avec "?".
# On utilise donc une liste blanche : seules ces valeurs peuvent entrer dans le SQL.
TRIS_AUTORISES = {
    'nom': 'nom, prenom',
    'prenom': 'prenom, nom',
    'created': 'created DESC',
}


@app.route('/recherche')
def recherche():
    if not a_le_role('user', 'admin'):
        return redirect(url_for('authentification'))
    q = request.args.get('q', '').strip()
    tri = request.args.get('tri', 'nom')
    if tri not in TRIS_AUTORISES:
        tri = 'nom'
    data = []
    if q:
        conn = get_db()
        motif = '%' + q + '%'
        data = conn.execute('SELECT * FROM clients WHERE nom LIKE ? OR prenom LIKE ? '
                            'ORDER BY ' + TRIS_AUTORISES[tri], (motif, motif)).fetchall()
        conn.close()
    return render_template('recherche.html', q=q, tri=tri, data=data)


@app.route('/enregistrer_client', methods=['GET', 'POST'])
def enregistrer_client():
    if not a_le_role('admin'):
        if not est_authentifie():
            return redirect(url_for('authentification'))
        return acces_refuse()

    if request.method == 'POST':
        nom = request.form.get('nom', '').strip().upper()
        prenom = request.form.get('prenom', '').strip()
        adresse = request.form.get('adresse', '').strip()
        telephone = request.form.get('telephone', '').strip() or None

        # Validation côté serveur : on ne fait jamais confiance au navigateur
        if not nom or not prenom or not adresse:
            return render_template('formulaire.html', erreur="Tous les champs sont obligatoires."), 400

        conn = get_db()
        cursor = conn.execute('INSERT INTO clients (nom, prenom, adresse, telephone) VALUES (?, ?, ?, ?)',
                              (nom, prenom, adresse, telephone))
        conn.commit()
        nouvel_id = cursor.lastrowid
        conn.close()
        # Redirection (Post/Redirect/Get) vers la fiche du client créé (défi exercice 4)
        return redirect(url_for('Readfiche', post_id=nouvel_id))

    return render_template('formulaire.html')


@app.route('/modifier_client/<int:id>', methods=['GET', 'POST'])
def modifier_client(id):
    if not a_le_role('admin'):
        return acces_refuse()
    conn = get_db()
    try:
        if request.method == 'POST':
            nom = request.form.get('nom', '').strip().upper()
            prenom = request.form.get('prenom', '').strip()
            adresse = request.form.get('adresse', '').strip()
            telephone = request.form.get('telephone', '').strip() or None
            if not nom or not prenom or not adresse:
                return message('Formulaire incomplet', 'Nom, prénom et adresse sont obligatoires.', 400,
                               url_for('modifier_client', id=id), 'Revenir au formulaire')
            conn.execute('UPDATE clients SET nom = ?, prenom = ?, adresse = ?, telephone = ? WHERE id = ?',
                         (nom, prenom, adresse, telephone, id))
            conn.commit()
            return redirect('/consultation/')

        client = conn.execute('SELECT * FROM clients WHERE id = ?', (id,)).fetchone()
    finally:
        conn.close()
    if client is None:
        return message('Client introuvable', f"Aucun client n°{id}.", 404)
    return render_template('modifier_client.html', client=client)


@app.route('/supprimer_client/<int:id>', methods=['POST'])
def supprimer_client(id):
    if not a_le_role('admin'):
        return acces_refuse()
    conn = get_db()
    try:
        conn.execute('DELETE FROM clients WHERE id = ?', (id,))
        conn.commit()
    except sqlite3.IntegrityError:
        nb = conn.execute('SELECT COUNT(*) FROM commandes WHERE client_id = ?', (id,)).fetchone()[0]
        return message('Suppression impossible', f"Impossible : ce client a {nb} commande(s).", 409,
                       url_for('Readfiche', post_id=id), 'Voir sa fiche')
    finally:
        conn.close()  # exécuté dans TOUS les cas, même après le return
    return redirect('/consultation/')


# ===============================================================
#  4. Commandes et statistiques (exercice 7)
# ===============================================================

@app.route('/commandes/')
def liste_commandes():
    if not a_le_role('user', 'admin'):
        return redirect(url_for('authentification'))
    conn = get_db()
    commandes = conn.execute('''
        SELECT commandes.id, commandes.client_id, clients.nom, clients.prenom,
               commandes.produit, commandes.montant, commandes.date_commande
        FROM commandes
        JOIN clients ON commandes.client_id = clients.id
        ORDER BY commandes.date_commande DESC, commandes.id DESC
    ''').fetchall()
    conn.close()
    return render_template('commandes.html', commandes=commandes)


@app.route('/fiche_client/<int:post_id>/commandes', methods=['POST'])
def ajouter_commande(post_id):
    if not a_le_role('admin'):
        return acces_refuse()
    produit = request.form.get('produit', '').strip()
    try:
        montant = float(request.form.get('montant', '').replace(',', '.'))
    except ValueError:
        montant = -1
    if not produit or montant < 0:
        return message('Commande invalide', 'Indiquez un produit et un montant positif.', 400,
                       url_for('Readfiche', post_id=post_id), 'Revenir à la fiche')
    conn = get_db()
    try:
        conn.execute('INSERT INTO commandes (client_id, produit, montant) VALUES (?, ?, ?)',
                     (post_id, produit, montant))
        conn.commit()
    except sqlite3.IntegrityError:
        return message('Client introuvable', f"Aucun client n°{post_id}.", 404)
    finally:
        conn.close()
    return redirect(url_for('Readfiche', post_id=post_id))


@app.route('/statistiques/')
def statistiques():
    if not a_le_role('user', 'admin'):
        return redirect(url_for('authentification'))
    conn = get_db()
    stats = conn.execute('''
        SELECT clients.id, clients.nom, clients.prenom,
               COUNT(commandes.id) AS nb_commandes,
               COALESCE(SUM(commandes.montant), 0) AS total
        FROM clients
        LEFT JOIN commandes ON commandes.client_id = clients.id
        GROUP BY clients.id
        ORDER BY total DESC, clients.nom
    ''').fetchall()
    conn.close()
    return render_template('statistiques.html', stats=stats)


# ===============================================================
#  5. API clients (exercice 9)
# ===============================================================

@app.get('/api/clients')
def api_liste_clients():
    q = request.args.get('q', '').strip()
    conn = get_db()
    if q:
        motif = '%' + q + '%'
        rows = conn.execute('SELECT * FROM clients WHERE nom LIKE ? OR prenom LIKE ? ORDER BY nom',
                            (motif, motif)).fetchall()
    else:
        rows = conn.execute('SELECT * FROM clients ORDER BY nom').fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.get('/api/clients/<int:id>')
def api_un_client(id):
    conn = get_db()
    row = conn.execute('SELECT * FROM clients WHERE id = ?', (id,)).fetchone()
    conn.close()
    if row is None:
        return jsonify({'erreur': 'Client introuvable'}), 404
    return jsonify(dict(row))


@app.post('/api/clients')
def api_creer_client():
    if not a_le_role('admin'):
        return jsonify({'erreur': 'Authentification administrateur requise'}), 401
    donnees = request.get_json(silent=True) or {}
    nom = str(donnees.get('nom', '')).strip().upper()
    prenom = str(donnees.get('prenom', '')).strip()
    adresse = str(donnees.get('adresse', '')).strip()
    telephone = str(donnees.get('telephone') or '').strip() or None

    if not nom or not prenom or not adresse:
        return jsonify({'erreur': 'Les champs nom, prenom et adresse sont obligatoires'}), 400

    conn = get_db()
    cursor = conn.execute('INSERT INTO clients (nom, prenom, adresse, telephone) VALUES (?, ?, ?, ?)',
                          (nom, prenom, adresse, telephone))
    conn.commit()
    nouvel_id = cursor.lastrowid
    conn.close()
    return jsonify({'id': nouvel_id, 'nom': nom, 'prenom': prenom,
                    'adresse': adresse, 'telephone': telephone}), 201


@app.delete('/api/clients/<int:id>')
def api_supprimer_client(id):
    if not a_le_role('admin'):
        return jsonify({'erreur': 'Authentification administrateur requise'}), 401
    conn = get_db()
    try:
        cursor = conn.execute('DELETE FROM clients WHERE id = ?', (id,))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({'erreur': 'Ce client a des commandes : suppression impossible'}), 409
    finally:
        conn.close()
    if cursor.rowcount == 0:
        return jsonify({'erreur': 'Client introuvable'}), 404
    return jsonify({'message': f'Client {id} supprimé'})


@app.route('/clients_js')
def clients_js():
    """Page qui affiche les clients en JavaScript (fetch), sans recharger la page."""
    return render_template('clients_js.html')


# ===============================================================
#  6. Projet bibliothèque
# ===============================================================

# La disponibilité n'est pas stockée : elle est CALCULÉE à partir des emprunts en cours.
SQL_LIVRES = '''
    SELECT livres.*,
           livres.nb_exemplaires - COUNT(emprunts.id) AS nb_disponibles
    FROM livres
    LEFT JOIN emprunts ON emprunts.livre_id = livres.id AND emprunts.date_retour IS NULL
'''


def chercher_livres(conn, q='', disponibles_seulement=False):
    sql, params = SQL_LIVRES, []
    if q:
        motif = '%' + q + '%'
        sql += ' WHERE livres.titre LIKE ? OR livres.auteur LIKE ?'
        params = [motif, motif]
    sql += ' GROUP BY livres.id'
    if disponibles_seulement:
        sql += ' HAVING nb_disponibles > 0'
    sql += ' ORDER BY livres.titre'
    return conn.execute(sql, params).fetchall()


def un_livre(conn, livre_id):
    return conn.execute(SQL_LIVRES + ' WHERE livres.id = ? GROUP BY livres.id', (livre_id,)).fetchone()


def lire_formulaire_livre(form):
    """Lit et valide le formulaire d'un livre. Renvoie (valeurs, erreur)."""
    valeurs = {
        'titre': form.get('titre', '').strip(),
        'auteur': form.get('auteur', '').strip(),
        'isbn': form.get('isbn', '').strip() or None,
        'genre': form.get('genre', '').strip() or None,
        'annee': form.get('annee', '').strip(),
        'nb_exemplaires': form.get('nb_exemplaires', '1').strip(),
    }
    if not valeurs['titre'] or not valeurs['auteur']:                       # règle R5
        return valeurs, 'Le titre et l\'auteur sont obligatoires.'
    try:
        valeurs['annee'] = int(valeurs['annee']) if valeurs['annee'] else None
        valeurs['nb_exemplaires'] = int(valeurs['nb_exemplaires'])
    except ValueError:
        return valeurs, 'L\'année et le nombre d\'exemplaires doivent être des nombres.'
    if valeurs['nb_exemplaires'] < 0:
        return valeurs, 'Le nombre d\'exemplaires ne peut pas être négatif.'
    return valeurs, None


def emprunter_livre(conn, livre_id, utilisateur_id):
    """Applique les règles R1 et R2. Renvoie (code HTTP, message)."""
    livre = un_livre(conn, livre_id)
    if livre is None:
        return 404, 'Livre introuvable.'
    if livre['nb_disponibles'] <= 0:                                        # règle R1
        return 409, f"« {livre['titre']} » n'est plus disponible : tous les exemplaires sont empruntés."
    en_cours = conn.execute('SELECT COUNT(*) FROM emprunts WHERE utilisateur_id = ? AND date_retour IS NULL',
                            (utilisateur_id,)).fetchone()[0]
    if en_cours >= MAX_EMPRUNTS:                                            # règle R2
        return 409, f'Vous avez déjà {en_cours} livres empruntés : le maximum est {MAX_EMPRUNTS}.'
    deja = conn.execute('SELECT COUNT(*) FROM emprunts WHERE utilisateur_id = ? AND livre_id = ? '
                        'AND date_retour IS NULL', (utilisateur_id, livre_id)).fetchone()[0]
    if deja:
        return 409, f"Vous avez déjà un exemplaire de « {livre['titre']} »."
    conn.execute("INSERT INTO emprunts (livre_id, utilisateur_id, date_retour_prevue) "
                 "VALUES (?, ?, date('now', ?))", (livre_id, utilisateur_id, f'+{DUREE_EMPRUNT_JOURS} days'))
    conn.commit()
    return 201, f"Vous avez emprunté « {livre['titre']} ». Bonne lecture !"


def rendre_livre(conn, emprunt_id):
    """Rend un livre : on NE SUPPRIME PAS l'emprunt, on remplit date_retour."""
    emprunt = conn.execute('SELECT * FROM emprunts WHERE id = ?', (emprunt_id,)).fetchone()
    if emprunt is None:
        return 404, 'Emprunt introuvable.'
    if emprunt['utilisateur_id'] != session.get('utilisateur_id') and not a_le_role('admin'):
        return 403, 'Cet emprunt ne vous appartient pas.'
    if emprunt['date_retour'] is not None:
        return 409, 'Ce livre a déjà été rendu.'
    conn.execute('UPDATE emprunts SET date_retour = CURRENT_TIMESTAMP WHERE id = ?', (emprunt_id,))
    conn.commit()
    return 200, 'Livre rendu, merci !'


# ----- F3 : catalogue et recherche --------------------------------

@app.route('/livres')
def livres():
    if not est_authentifie():
        return redirect(url_for('authentification'))
    q = request.args.get('q', '').strip()
    dispo = request.args.get('disponibles') == '1'
    conn = get_db()
    liste = chercher_livres(conn, q, dispo)
    conn.close()
    return render_template('livres.html', livres=liste, q=q, dispo=dispo)


# ----- F1 / F2 : administration des livres et des stocks ----------

@app.route('/livres/ajouter', methods=['GET', 'POST'])
def ajouter_livre():
    if not a_le_role('admin'):
        return acces_refuse()
    if request.method == 'POST':
        valeurs, erreur = lire_formulaire_livre(request.form)
        if erreur:
            return render_template('livre_form.html', livre=valeurs, erreur=erreur), 400
        conn = get_db()
        conn.execute('INSERT INTO livres (titre, auteur, isbn, annee, genre, nb_exemplaires) '
                     'VALUES (:titre, :auteur, :isbn, :annee, :genre, :nb_exemplaires)', valeurs)
        conn.commit()
        conn.close()
        return redirect(url_for('livres'))
    return render_template('livre_form.html', livre={'nb_exemplaires': 1})


@app.route('/livres/<int:id>/modifier', methods=['GET', 'POST'])
def modifier_livre(id):
    if not a_le_role('admin'):
        return acces_refuse()
    conn = get_db()
    try:
        livre = un_livre(conn, id)
        if livre is None:
            return message('Livre introuvable', f'Aucun livre n°{id}.', 404)
        if request.method == 'POST':
            valeurs, erreur = lire_formulaire_livre(request.form)
            empruntes = livre['nb_exemplaires'] - livre['nb_disponibles']
            if not erreur and valeurs['nb_exemplaires'] < empruntes:
                erreur = f'{empruntes} exemplaire(s) sont en cours d\'emprunt : le stock ne peut pas être inférieur.'
            if erreur:
                valeurs['id'] = id
                return render_template('livre_form.html', livre=valeurs, erreur=erreur), 400
            valeurs['id'] = id
            conn.execute('UPDATE livres SET titre = :titre, auteur = :auteur, isbn = :isbn, annee = :annee, '
                         'genre = :genre, nb_exemplaires = :nb_exemplaires WHERE id = :id', valeurs)
            conn.commit()
            return redirect(url_for('livres'))
    finally:
        conn.close()
    return render_template('livre_form.html', livre=livre)


@app.route('/livres/<int:id>/supprimer', methods=['POST'])
def supprimer_livre(id):
    if not a_le_role('admin'):
        return acces_refuse()
    conn = get_db()
    try:
        livre = un_livre(conn, id)
        if livre is None:
            return message('Livre introuvable', f'Aucun livre n°{id}.', 404)
        if livre['nb_disponibles'] < livre['nb_exemplaires']:               # règle R3
            return message('Suppression impossible',
                           f"« {livre['titre']} » a des exemplaires en cours d'emprunt.", 409,
                           url_for('livres'), 'Retour au catalogue')
        # Le livre n'est plus emprunté : on efface son historique puis le livre
        conn.execute('DELETE FROM emprunts WHERE livre_id = ?', (id,))
        conn.execute('DELETE FROM livres WHERE id = ?', (id,))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for('livres'))


# ----- F4 / F5 / F6 : emprunts --------------------------------------

@app.route('/livres/<int:id>/emprunter', methods=['POST'])
def emprunter(id):
    if not est_authentifie():
        return redirect(url_for('authentification'))
    conn = get_db()
    try:
        code, texte = emprunter_livre(conn, id, session['utilisateur_id'])
    finally:
        conn.close()
    if code != 201:
        return message('Emprunt refusé', texte, code, url_for('livres'), 'Retour au catalogue')
    return redirect(url_for('mes_emprunts'))


@app.route('/emprunts/<int:id>/rendre', methods=['POST'])
def rendre(id):
    if not est_authentifie():
        return redirect(url_for('authentification'))
    conn = get_db()
    try:
        code, texte = rendre_livre(conn, id)
    finally:
        conn.close()
    if code != 200:
        return message('Retour impossible', texte, code, url_for('mes_emprunts'), 'Mes emprunts')
    return redirect(request.form.get('retour') or url_for('mes_emprunts'))


@app.route('/mes_emprunts')
def mes_emprunts():
    if not est_authentifie():
        return redirect(url_for('authentification'))
    conn = get_db()
    emprunts = conn.execute('''
        SELECT emprunts.*, livres.titre, livres.auteur,
               (emprunts.date_retour IS NULL AND emprunts.date_retour_prevue < date('now')) AS en_retard
        FROM emprunts
        JOIN livres ON emprunts.livre_id = livres.id
        WHERE emprunts.utilisateur_id = ?
        ORDER BY emprunts.date_retour IS NOT NULL, emprunts.date_emprunt DESC
    ''', (session['utilisateur_id'],)).fetchall()
    conn.close()
    en_cours = [e for e in emprunts if e['date_retour'] is None]
    historique = [e for e in emprunts if e['date_retour'] is not None]
    return render_template('mes_emprunts.html', en_cours=en_cours, historique=historique,
                           max_emprunts=MAX_EMPRUNTS)


# ----- F7 : gestion des utilisateurs (admin) -------------------------

@app.route('/utilisateurs', methods=['GET', 'POST'])
def utilisateurs():
    if not a_le_role('admin'):
        return acces_refuse()
    erreur = None
    conn = get_db()
    try:
        if request.method == 'POST':
            login = request.form.get('login', '').strip().lower()
            nom = request.form.get('nom', '').strip().upper()
            prenom = request.form.get('prenom', '').strip()
            mot_de_passe = request.form.get('mot_de_passe', '')
            role = request.form.get('role', 'user')
            if not login or not nom or not prenom or len(mot_de_passe) < 4:
                erreur = 'Tous les champs sont obligatoires (mot de passe : 4 caractères minimum).'
            elif role not in ('user', 'admin'):
                erreur = 'Rôle invalide.'
            else:
                try:
                    conn.execute('INSERT INTO utilisateurs (login, nom, prenom, mot_de_passe_hash, role) '
                                 'VALUES (?, ?, ?, ?, ?)',
                                 (login, nom, prenom, generate_password_hash(mot_de_passe), role))
                    conn.commit()
                    return redirect(url_for('utilisateurs'))
                except sqlite3.IntegrityError:
                    erreur = f'Le login « {login} » existe déjà.'
        liste = conn.execute('''
            SELECT utilisateurs.id, login, nom, prenom, role,
                   COUNT(emprunts.id) AS nb_en_cours
            FROM utilisateurs
            LEFT JOIN emprunts ON emprunts.utilisateur_id = utilisateurs.id AND emprunts.date_retour IS NULL
            GROUP BY utilisateurs.id
            ORDER BY role, login
        ''').fetchall()
    finally:
        conn.close()
    return render_template('utilisateurs.html', utilisateurs=liste, erreur=erreur), (400 if erreur else 200)


@app.route('/utilisateurs/<int:id>/supprimer', methods=['POST'])
def supprimer_utilisateur(id):
    if not a_le_role('admin'):
        return acces_refuse()
    if id == session.get('utilisateur_id'):
        return message('Suppression impossible', 'Vous ne pouvez pas supprimer votre propre compte.', 409,
                       url_for('utilisateurs'), 'Retour aux utilisateurs')
    conn = get_db()
    try:
        en_cours = conn.execute('SELECT COUNT(*) FROM emprunts WHERE utilisateur_id = ? AND date_retour IS NULL',
                                (id,)).fetchone()[0]
        if en_cours:
            return message('Suppression impossible', f'Cet utilisateur a encore {en_cours} livre(s) à rendre.',
                           409, url_for('utilisateurs'), 'Retour aux utilisateurs')
        conn.execute('DELETE FROM emprunts WHERE utilisateur_id = ?', (id,))
        conn.execute('DELETE FROM utilisateurs WHERE id = ?', (id,))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for('utilisateurs'))


# ----- Bonus : retards et statistiques --------------------------------

@app.route('/admin/emprunts')
def admin_emprunts():
    if not a_le_role('admin'):
        return acces_refuse()
    seulement_retards = request.args.get('retards') == '1'
    sql = '''
        SELECT emprunts.*, livres.titre, utilisateurs.login, utilisateurs.nom, utilisateurs.prenom,
               (emprunts.date_retour_prevue < date('now')) AS en_retard
        FROM emprunts
        JOIN livres ON emprunts.livre_id = livres.id
        JOIN utilisateurs ON emprunts.utilisateur_id = utilisateurs.id
        WHERE emprunts.date_retour IS NULL
    '''
    if seulement_retards:
        sql += " AND emprunts.date_retour_prevue < date('now')"
    sql += ' ORDER BY emprunts.date_retour_prevue'
    conn = get_db()
    emprunts = conn.execute(sql).fetchall()
    conn.close()
    return render_template('admin_emprunts.html', emprunts=emprunts, seulement_retards=seulement_retards)


@app.route('/livres/statistiques')
def statistiques_livres():
    if not est_authentifie():
        return redirect(url_for('authentification'))
    conn = get_db()
    top = conn.execute('''
        SELECT livres.titre, livres.auteur, COUNT(emprunts.id) AS nb
        FROM livres JOIN emprunts ON emprunts.livre_id = livres.id
        GROUP BY livres.id ORDER BY nb DESC, livres.titre LIMIT 5
    ''').fetchall()
    genres = conn.execute('''
        SELECT COALESCE(livres.genre, 'Non classé') AS genre, COUNT(emprunts.id) AS nb
        FROM emprunts JOIN livres ON emprunts.livre_id = livres.id
        GROUP BY livres.genre ORDER BY nb DESC
    ''').fetchall()
    par_mois = conn.execute('''
        SELECT strftime('%Y-%m', date_emprunt) AS mois, COUNT(*) AS nb
        FROM emprunts GROUP BY mois ORDER BY mois DESC LIMIT 12
    ''').fetchall()
    conn.close()
    return render_template('statistiques_livres.html', top=top, genres=genres, par_mois=par_mois)


# ----- F9 : API bibliothèque --------------------------------------------

@app.get('/api/livres')
def api_livres():
    conn = get_db()
    liste = chercher_livres(conn, request.args.get('q', '').strip(), request.args.get('disponibles') == '1')
    conn.close()
    return jsonify([dict(l) | {'disponible': l['nb_disponibles'] > 0} for l in liste])


@app.get('/api/livres/<int:id>')
def api_un_livre(id):
    conn = get_db()
    livre = un_livre(conn, id)
    conn.close()
    if livre is None:
        return jsonify({'erreur': 'Livre introuvable'}), 404
    return jsonify(dict(livre) | {'disponible': livre['nb_disponibles'] > 0})


@app.get('/api/emprunts')
def api_mes_emprunts():
    if not est_authentifie():
        return jsonify({'erreur': 'Authentification requise'}), 401
    conn = get_db()
    rows = conn.execute('SELECT emprunts.*, livres.titre FROM emprunts JOIN livres ON livres.id = emprunts.livre_id '
                        'WHERE utilisateur_id = ? AND date_retour IS NULL', (session['utilisateur_id'],)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.post('/api/emprunts')
def api_emprunter():
    if not est_authentifie():
        return jsonify({'erreur': 'Authentification requise'}), 401
    donnees = request.get_json(silent=True) or {}
    try:
        livre_id = int(donnees.get('livre_id'))
    except (TypeError, ValueError):
        return jsonify({'erreur': 'Le champ livre_id (entier) est obligatoire'}), 400
    conn = get_db()
    try:
        code, texte = emprunter_livre(conn, livre_id, session['utilisateur_id'])
    finally:
        conn.close()
    return jsonify({'message' if code == 201 else 'erreur': texte}), code


@app.post('/api/emprunts/<int:id>/retour')
def api_rendre(id):
    if not est_authentifie():
        return jsonify({'erreur': 'Authentification requise'}), 401
    conn = get_db()
    try:
        code, texte = rendre_livre(conn, id)
    finally:
        conn.close()
    return jsonify({'message' if code == 200 else 'erreur': texte}), code


# ---------------------------------------------------------------
#  Ne pas modifier : utile seulement pour lancer le site
#  sur votre propre ordinateur (python flask_app.py)
# ---------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
