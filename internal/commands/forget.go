package commands

import (
	"database/sql"
	"hearsay/internal/config"
	"log"
	"strconv"
	"time"
)

func forgetHandler(args []string, author string, db *sql.DB) string {
	var deletionTime sql.NullTime
	res := db.QueryRow("SELECT deletion FROM users WHERE nick = ?", author)
	if err := res.Scan(&deletionTime); err != nil {
		if err == sql.ErrNoRows {
			return author + ": Your nick was not found in the database."
		}
		log.Printf("Failed to query deletion time: %s\n", err.Error())
		return author + ": The requested action was met with an error."
	}

	if deletionTime.Valid {
		return author + ": Your data is already scheduled for deletion."
	}

	deletionDate := time.Now()
	deletionDate = deletionDate.AddDate(0, 0, config.DeletionDays)
	_, err := db.Exec("UPDATE users SET deletion ? WHERE nick = ?", deletionDate, author)
	if err != nil {
		log.Printf("Failed to schedule deletion: %s\n", err.Error())
		return author + ": The requested action was met with an error."
	}

	return author + ": Your data is scheduled for deletion and will complete in " + strconv.Itoa(config.DeletionDays) + " days. To cancel this request, type +unforget"
}

var forgetHelp string = `Permanently purge all your data. Usage: +forget`
