-- ---------------------------------------------------------------
--  Structure de la base de données (schéma)
-- ---------------------------------------------------------------
--  ⚠️ Les DROP TABLE effacent les données : ce fichier sert à
--  (re)créer la base pendant le développement (create_db.py).
--  En production, on fait évoluer la base avec les scripts du
--  dossier migrations/ (exercice 6).
--
--  Ordre des DROP : on supprime d'abord les tables qui DÉPENDENT
--  des autres (celles qui ont des clés étrangères).
-- ---------------------------------------------------------------

DROP TABLE IF EXISTS emprunts;
DROP TABLE IF EXISTS livres;
DROP TABLE IF EXISTS utilisateurs;
DROP TABLE IF EXISTS commandes;
DROP TABLE IF EXISTS clients;

-- ===== Exercices 1 à 6 : les clients ============================
CREATE TABLE clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    adresse TEXT NOT NULL,
    telephone TEXT                                   -- exercice 6
);

-- ===== Exercice 7 : les commandes (relation 1 client → n commandes)
CREATE TABLE commandes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    produit TEXT NOT NULL,
    montant REAL NOT NULL,
    date_commande TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients (id)
);

-- ===== Exercice 8 (défi) + projet : les comptes ==================
CREATE TABLE utilisateurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT NOT NULL UNIQUE,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    mot_de_passe_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user'))
);

-- ===== Projet bibliothèque =======================================
CREATE TABLE livres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT NOT NULL,
    auteur TEXT NOT NULL,
    isbn TEXT,
    annee INTEGER,
    genre TEXT,
    nb_exemplaires INTEGER NOT NULL DEFAULT 1 CHECK (nb_exemplaires >= 0)
);

CREATE TABLE emprunts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    livre_id INTEGER NOT NULL,
    utilisateur_id INTEGER NOT NULL,
    date_emprunt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_retour_prevue DATE NOT NULL DEFAULT (date('now', '+21 days')),
    date_retour TIMESTAMP,                           -- NULL = emprunt en cours
    FOREIGN KEY (livre_id) REFERENCES livres (id),
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs (id)
);
