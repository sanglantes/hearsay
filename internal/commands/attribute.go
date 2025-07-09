package commands

import (
	"database/sql"
	"hearsay/internal/config"
)

func attributeHandler(args []string, author string, db *sql.DB) string {
	return author + " is a nerd."
}

var attributeHelp string = `Attribute text to a chatter. Usage: ` + config.CommandPrefix + `attribute <message>`
