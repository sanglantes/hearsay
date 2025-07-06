package storage

import (
	"database/sql"
	"log"
)

// We keep a map of opt-outs. This prevents database lookups.
// This approach works fine for smaller servers.

var OptOuts = make(map[string]struct{}) // TODO: Add mutex if this is used in more than one place.

func IfOptedOut(nickname string) bool {
	if _, exists := OptOuts[nickname]; exists {
		return true
	}
	return false
}

func LoadOptOuts(db *sql.DB) error {
	res, err := db.Query("SELECT nickname FROM users WHERE opt = 0")
	if err != nil {
		log.Fatalf("Failed to load opt-out nicks: %s\n", err.Error())
	}
	defer res.Close()

	for res.Next() {
		var nick string
		if err := res.Scan(&nick); err != nil {
			return err
		}
		OptOuts[nick] = struct{}{}
	}

	return nil
}
