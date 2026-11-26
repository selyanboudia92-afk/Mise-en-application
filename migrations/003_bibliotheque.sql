-- Migration 003 (exercice 8 + projet) : comptes, livres et emprunts.
--     cd ~/mysite && sqlite3 database.db < migrations/003_bibliotheque.sql
-- Les comptes de test (mots de passe hachés) sont ensuite créés avec :
--     python3 create_db.py --comptes
CREATE TABLE IF NOT EXISTS utilisateurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT NOT NULL UNIQUE,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    mot_de_passe_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user'))
);

CREATE TABLE IF NOT EXISTS livres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT NOT NULL,
    auteur TEXT NOT NULL,
    isbn TEXT,
    annee INTEGER,
    genre TEXT,
    nb_exemplaires INTEGER NOT NULL DEFAULT 1 CHECK (nb_exemplaires >= 0)
);

CREATE TABLE IF NOT EXISTS emprunts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    livre_id INTEGER NOT NULL,
    utilisateur_id INTEGER NOT NULL,
    date_emprunt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_retour_prevue DATE NOT NULL DEFAULT (date('now', '+21 days')),
    date_retour TIMESTAMP,
    FOREIGN KEY (livre_id) REFERENCES livres (id),
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs (id)
);
