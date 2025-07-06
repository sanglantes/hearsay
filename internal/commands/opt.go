package commands

import (
	"database/sql"
	"hearsay/internal/config"
	"hearsay/internal/storage"
	"log"
)

func optHandler(args []string, author string, db *sql.DB) string {
	if len(args) != 1 || (args[0] != "in" && args[0] != "out") {
		return author + ": Improper argument(s). See " + config.CommandPrefix + "help opt for usage."
	}

	opt := map[string]bool{
		"in":  true,
		"out": false,
	}

	res, err := db.Exec("UPDATE users SET opt = ? WHERE nick = ?", opt[args[0]], author)
	if err != nil {
		log.Fatalf("Failed updating opt preference: %s", err.Error())
		return author + ": Something went wrong."
	}

	rA, _ := res.RowsAffected()
	if rA == 0 {
		log.Println("In opt command: user not found.")
		return author + ": Your nick was not found in the database."
	}

	if opt[args[0]] {
		delete(storage.OptOuts, author)
	} else {
		storage.OptOuts[author] = struct{}{}
	}
	return author + ": You have successfully opted " + args[0] + "."
}

var optHelp string = `Opt in or out from data collection. Usage: +opt <in|out>`
