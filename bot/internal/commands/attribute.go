package commands

import (
	"database/sql"
	"fmt"
	"hearsay/internal/config"
	"hearsay/internal/storage"
)

func attributeHandler(args []string, author string, db *sql.DB) string {
	if storage.IsOptedOut(author) {
		return author + ": You must be opted in to use this command. +help opt"
	}

	if !storage.FulfilsMessagesCount(author, config.MessageQuota, db) {
		return fmt.Sprintf("%s: You have too few messages stored to use this command. hearsay requires %d messages.", author, config.MessageQuota)
	}
	return author + " is a nerd."
}

var attributeHelp string = `Attribute text to a chatter. Usage: ` + config.CommandPrefix + `attribute <message>`
