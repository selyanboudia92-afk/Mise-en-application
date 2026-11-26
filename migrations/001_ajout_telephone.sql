-- Migration 001 (exercice 6) : ajout du numéro de téléphone des clients.
-- À exécuter UNE SEULE FOIS sur le serveur :
--     cd ~/mysite && sqlite3 database.db < migrations/001_ajout_telephone.sql
ALTER TABLE clients ADD COLUMN telephone TEXT;
