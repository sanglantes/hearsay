package storage

import (
	"database/sql"
	"fmt"
	"log"
	"time"
)

type Message struct {
	Nick      string
	Content   string
	Channel   string
	Timestamp time.Time
}

func SubmitMessages(messages []Message, db *sql.DB) error {
	tx, err := db.Begin()
	if err != nil {
		return err
	}

	userInsertionStmt, err := tx.Prepare("INSERT OR IGNORE INTO users(nick, registered, opt, deletion) VALUES (?, ?, ?, ?)")
	if err != nil {
		return err
	}

	messagesStmt, err := tx.Prepare("INSERT INTO messages (nick, channel, message, time) VALUES (?, ?, ?, ?)")
	if err != nil {
		return err
	}

	for _, message := range messages {
		_, err = userInsertionStmt.Exec(message.Nick, message.Timestamp, true, nil)
		if err != nil {
			tx.Rollback()
			return err
		}

		_, err := messagesStmt.Exec(message.Nick, message.Channel, message.Content, message.Timestamp)
		if err != nil {
			tx.Rollback()
			return err
		}
	}

	return tx.Commit()
}

func FulfilsMessagesCount(nick string, quota int, db *sql.DB) bool {
	var count int

	err := db.QueryRow("SELECT COUNT(nick) FROM messages WHERE nick = ? AND time >= datetime('now', '-30 days')", nick).Scan(&count)
	fmt.Printf("%d\n", count)
	if err != nil {
		log.Printf("Failed to count messages in FulfilsMessagesCount for nick %s: %s\n", nick, err.Error())
		return false
	}

	return (count > quota)
}
