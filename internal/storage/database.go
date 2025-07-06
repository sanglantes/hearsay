package storage

import (
	"database/sql"
	"log"

	_ "github.com/mattn/go-sqlite3"
)

func openDbHelper(path string) *sql.DB {
	db, err := sql.Open("sqlite3", path)
	if err != nil {
		log.Fatalf("Error opening %s: %v\n", path, err.Error())
	}

	err = db.Ping()
	if err != nil {
		log.Fatalf("Error connecting to %s: %v\n", path, err)
	}

	return db
}

func InitDatabase() *sql.DB {
	db := openDbHelper("data/database.db")
	_, err := db.Exec(`CREATE TABLE IF NOT EXISTS messages(
	id INTEGER PRIMARY KEY,
	nickname TEXT NOT NULL,
	channel TEXT NOT NULL,
	message TEXT NOT NULL,
	time DATETIME DEFAULT CURRENT_TIMESTAMP
	)`)
	if err != nil {
		log.Fatalf("Error creating messages table: %v\n", err.Error())
	}

	_, err = db.Exec("CREATE INDEX IF NOT EXISTS idx_nickname ON messages(nickname)")
	if err != nil {
		log.Fatalf("Error indexing nickname: %v\n", err.Error())
	}

	_, err = db.Exec(`CREATE TABLE IF NOT EXISTS users(
	nickname TEXT PRIMARY KEY,
	registered DATETIME DEFAULT CURRENT_TIMESTAMP,
	opt BOOL DEFAULT TRUE,
	deletion DATETIME DEFAULT NULL
	)`)
	if err != nil {
		log.Fatalf("Error creating users table: %v\n", err.Error())
	}

	return db
}
