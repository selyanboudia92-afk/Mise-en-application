# ---------------------------------------------------------------
#  Création (ou RÉ-initialisation) de la base de données
# ---------------------------------------------------------------
#  ⚠️ Attention : sans option, ce script EFFACE toutes les données
#  existantes (voir les "DROP TABLE" dans schema.sql) puis recrée
#  les tables avec quelques données d'exemple.
#
#  À lancer depuis une console Bash PythonAnywhere :
#      cd ~/mysite
#      python3 create_db.py
#
#  Option sans perte de données (après les migrations) :
#      python3 create_db.py --comptes
#  → ajoute seulement les comptes de test et les livres d'exemple
#    s'ils n'existent pas encore.
# ---------------------------------------------------------------

import os
import sqlite3
import sys

from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CLIENTS = [
    ('DUPONT', 'Emilie', '123, Rue des Lilas, 75001 Paris', '06 12 34 56 78'),
    ('LEROUX', 'Lucas', '456, Avenue du Soleil, 31000 Toulouse', None),
    ('MARTIN', 'Amandine', '789, Rue des Érables, 69002 Lyon', '07 98 76 54 32'),
    ('TREMBLAY', 'Antoine', '1010, Boulevard de la Mer, 13008 Marseille', None),
    ('LAMBERT', 'Sarah', '222, Avenue de la Liberté, 59000 Lille', None),
    ('GAGNON', 'Nicolas', '456, Boulevard des Cerisiers, 69003 Lyon', None),
    ('DUBOIS', 'Charlotte', '789, Rue des Roses, 13005 Marseille', None),
    ('LEFEVRE', 'Thomas', '333, Rue de la Paix, 75002 Paris', None),
]

COMMANDES = [
    (2, 'Clavier', 49.90), (2, 'Souris', 19.90), (3, 'Écran', 189.00),
    (5, 'Casque', 79.00), (5, 'Webcam', 59.00), (5, 'Câble HDMI', 9.90),
]

# login, nom, prénom, mot de passe (haché avant d'être stocké), rôle
COMPTES = [
    ('admin', 'ADMIN', 'Bibliothécaire', 'password', 'admin'),
    ('user', 'DURAND', 'Léa', '12345', 'user'),
    ('user2', 'PETIT', 'Hugo', '12345', 'user'),
]

# titre, auteur, isbn, année, genre, nombre d'exemplaires
LIVRES = [
    ('Le Petit Prince', 'Antoine de Saint-Exupéry', '9782070612758', 1943, 'Conte', 3),
    ('Les Misérables', 'Victor Hugo', '9782253096344', 1862, 'Roman', 2),
    ('L\'Étranger', 'Albert Camus', '9782070360024', 1942, 'Roman', 2),
    ('1984', 'George Orwell', '9782070368228', 1949, 'Science-fiction', 2),
    ('Le Seigneur des anneaux', 'J. R. R. Tolkien', '9782266282369', 1954, 'Fantasy', 1),
    ('Harry Potter à l\'école des sorciers', 'J. K. Rowling', '9782070584628', 1997, 'Fantasy', 4),
    ('Madame Bovary', 'Gustave Flaubert', '9782253004868', 1857, 'Roman', 1),
    ('Le Comte de Monte-Cristo', 'Alexandre Dumas', '9782253098058', 1844, 'Aventure', 2),
    ('Fondation', 'Isaac Asimov', '9782070360536', 1951, 'Science-fiction', 1),
    ('Vingt mille lieues sous les mers', 'Jules Verne', '9782253006329', 1870, 'Aventure', 2),
]


def ajouter_comptes_et_livres(cur):
    """Ajoute les comptes et les livres d'exemple sans rien effacer."""
    for login, nom, prenom, mdp, role in COMPTES:
        cur.execute(
            'INSERT OR IGNORE INTO utilisateurs (login, nom, prenom, mot_de_passe_hash, role) '
            'VALUES (?, ?, ?, ?, ?)',
            (login, nom, prenom, generate_password_hash(mdp), role))
    if cur.execute('SELECT COUNT(*) FROM livres').fetchone()[0] == 0:
        cur.executemany(
            'INSERT INTO livres (titre, auteur, isbn, annee, genre, nb_exemplaires) '
            'VALUES (?, ?, ?, ?, ?, ?)', LIVRES)


def main():
    connection = sqlite3.connect(os.path.join(BASE_DIR, 'database.db'))
    cur = connection.cursor()

    if '--comptes' in sys.argv:
        ajouter_comptes_et_livres(cur)
        connection.commit()
        connection.close()
        print("✅ Comptes de test et livres d'exemple ajoutés (aucune donnée effacée)")
        return

    with open(os.path.join(BASE_DIR, 'schema.sql'), encoding='utf-8') as f:
        connection.executescript(f.read())

    cur.executemany('INSERT INTO clients (nom, prenom, adresse, telephone) VALUES (?, ?, ?, ?)', CLIENTS)
    cur.executemany('INSERT INTO commandes (client_id, produit, montant) VALUES (?, ?, ?)', COMMANDES)
    ajouter_comptes_et_livres(cur)

    # Quelques emprunts d'exemple : un en cours, un rendu, un en retard
    cur.execute("INSERT INTO emprunts (livre_id, utilisateur_id) VALUES (1, 2)")
    cur.execute("INSERT INTO emprunts (livre_id, utilisateur_id, date_emprunt, date_retour_prevue, date_retour) "
                "VALUES (4, 2, datetime('now', '-40 days'), date('now', '-19 days'), datetime('now', '-25 days'))")
    cur.execute("INSERT INTO emprunts (livre_id, utilisateur_id, date_emprunt, date_retour_prevue) "
                "VALUES (5, 3, datetime('now', '-30 days'), date('now', '-9 days'))")

    connection.commit()
    connection.close()
    print("✅ Base de données créée : database.db")


if __name__ == '__main__':
    main()
