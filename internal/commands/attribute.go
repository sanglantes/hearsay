package commands

import "database/sql"

func attributeHandler(args []string, author string, db *sql.DB) string {
	return author + " is a nerd."
}

var attributeHelp string = `Attribute a sentence to a chatter. Usage: +attribute <message>`
