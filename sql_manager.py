import mysql.connector
import dotenv
from dotenv import dotenv_values
import sqlite3
import json
import os


class DatabaseManager:
    def __init__(self):
        self.config = dotenv_values(os.path.dirname(os.path.abspath(__file__)) + "/.env")
        self.conn = None
        self.db_mode = self.config.get('DB_MODE')
        
        if self.db_mode == 'mysql':
            self.conn = mysql.connector.connect(
                host=self.config['DB_HOST'],
                port=int(self.config['DB_PORT']),
                user=self.config['DB_USER'],
                password=self.config['DB_PASSWORD'],
                database=self.config['DB_NAME']
            )
            # Buffered cursor lets us read results later without blocking commits/new queries
            self.cur = self.conn.cursor(buffered=True)
        elif self.db_mode == 'sqlite':
            db_dir = os.path.dirname(os.path.abspath(__file__)) + "/" +self.config.get('DB_DIR')
            self.conn = sqlite3.connect(db_dir)
            self.cur = self.conn.cursor()
        else:
            raise ValueError("DB_MODE non valido nel file .env. Deve essere 'sqlite' o 'mysql'.")

    def _convert_query(self, query, params):
        """Converte i placeholder da ? (SQLite) a %s (MySQL) se necessario."""
        if self.db_mode == 'mysql' and '?' in query:
            # Sostituisce ? con %s per MySQL
            query = query.replace('?', '%s')
        return query, params

    def cur_execute(self, query, params=()):
        """Esegue una query sul database e ritorna il cursore."""
        if self.conn is None:
            self.get_connection()
        query, params = self._convert_query(query, params)
        self.cur.execute(query, params)
        return self.cur

    def commit(self):
        """Esegue una query sul database."""
        if self.conn is None:
            self.get_connection()
        res = self.conn.commit()        
        return res

    def fetchall(self):
        """Ritorna tutti i risultati dell'ultima query eseguita."""
        return self.cur.fetchall()
    
    def fetchone(self):
        """Ritorna un singolo risultato dell'ultima query eseguita."""
        return self.cur.fetchone()

    def close_connection(self):
        """Chiude la connessione al database."""
        if self.conn:
            self.conn.close()
            self.conn = None
