-- Migration 002 (exercice 7) : table des commandes, reliée aux clients.
--     cd ~/mysite && sqlite3 database.db < migrations/002_commandes.sql
CREATE TABLE IF NOT EXISTS commandes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    produit TEXT NOT NULL,
    montant REAL NOT NULL,
    date_commande TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients (id)
);
