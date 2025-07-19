package commands

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"fmt"
	"hearsay/internal/config"
	"hearsay/internal/storage"
	"io"
	"log"
	"net/http"
	"strings"
)

type attributeResponse struct {
	Author string `json:"author"`
}

func attributeHandler(args []string, author string, db *sql.DB) string {
	if storage.IsOptedOut(author) {
		return author + ": You must be opted in to use this command. +help opt"
	}

	if !storage.EnoughFulfilsMessagesCount(config.PeopleQuota, config.MessageQuota, db) {
		return fmt.Sprintf("%s: Not enough people fulfil the message quota. hearsay requires %d people with >= %d messages.", author, config.PeopleQuota, config.MessageQuota)
	}

	if len(args) == 0 {
		return author + ": You cannot attribute an empty message."
	}

	msg := strings.Join(args, " ")
	body := map[string]interface{}{
		"msg":          msg,
		"min_messages": config.MessageQuota,
	}
	postJson, err := json.Marshal(body)
	if err != nil {
		log.Printf("Failed to marshal POST request in attribute by %s: %s\n", author, err.Error())
		return author + ": Failed to fetch results."
	}

	req, err := http.NewRequest(http.MethodPost, "http://api:8111/attribute", bytes.NewBuffer(postJson))
	if err != nil {
		log.Printf("Failed to get attribute URL for %s: %s\n", author, err.Error())
		return author + ": Failed to fetch results."
	}
	req.Header.Set("Content-Type", "application/json")

	res, err := http.DefaultClient.Do(req)
	if err != nil {
		log.Printf("Failed to send GET request in attribute for %s: %s\n", author, err.Error())
		return author + ": Failed to fetch results."
	}

	resBody, err := io.ReadAll(res.Body)
	if err != nil {
		log.Printf("Failed to read response body in attribute for %s: %s\n", author, err.Error())
		return author + ": Failed to fetch results."
	}

	var result attributeResponse
	err = json.Unmarshal(resBody, &result)
	if err != nil {
		log.Printf("Failed to unmarshal response body in attribute for %s: %s\n", author, err.Error())
		return author + ": Failed to fetch results."
	}

	return fmt.Sprintf("%s: Predicted author: %s", author, result.Author)
}

var attributeHelp string = `Attribute a message to a chatter who is opted in and fulfils the message quota. Usage: ` + config.CommandPrefix + `attribute <message>`
