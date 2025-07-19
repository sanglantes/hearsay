package commands

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"hearsay/internal/config"
	"hearsay/internal/storage"
	"io"
	"log"
	"net/http"
	"time"
)

type retrainResponse struct {
	TimeD    float64 `json:"time"`
	Url      string  `json:"url"`
	Accuracy float64 `json:"accuracy"`
}

var lastRetrain = time.Now().Add(-12 * time.Hour)

func retrainHandler(args []string, author string, db *sql.DB) string {
	if time.Since(lastRetrain) < 12*time.Hour {
		return author + ": The model has already been retrained within the last 12 hours."
	}
	lastRetrain = time.Now()

	if storage.IsOptedOut(author) {
		return author + ": You must be opted in to use this command. +help opt"
	}

	if !storage.EnoughFulfilsMessagesCount(config.PeopleQuota, config.MessageQuota, db) { // TODO: (URGENT) Add in config.yaml
		return fmt.Sprintf("%s: Not enough people fulfil the message quota. hearsay requires %d people with >= %d messages.", author, config.PeopleQuota, config.MessageQuota)
	}

	url := "http://api:8111/retrain"
	if len(args) != 0 {
		url = fmt.Sprintf("http://api:8111/retrain?varg=%s", args[0])
	}
	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		log.Printf("Failed to get retrain URL for %s: %s\n", author, err.Error())
		return author + ": Failed to fetch results."
	}

	res, err := http.DefaultClient.Do(req)
	if err != nil {
		log.Printf("Failed to send GET request in retrain for %s: %s\n", author, err.Error())
		return author + ": Failed to fetch results."
	}

	resBody, err := io.ReadAll(res.Body)
	if err != nil {
		log.Printf("Failed to read response body in retrain for %s: %s\n", author, err.Error())
		return author + ": Failed to fetch results."
	}

	var result retrainResponse
	err = json.Unmarshal(resBody, &result)
	if err != nil {
		log.Printf("Failed to unmarshal response body in retrain for %s: %s\n", author, err.Error())
		return author + ": Failed to fetch results."
	}

	responseOne := fmt.Sprintf("%s: The SVM model has been retrained. It took %.2f seconds to fit.", author, result.TimeD)
	if result.Url != "" {
		responseOne += fmt.Sprintf(" Confusion matrix: %s | 5-fold cross-validation accuracy: %.1f", result.Url, result.Accuracy*100)
	}

	return responseOne
}

var retrainHelp string = `Refit the SVM classification model. This can be done every 12 hours. Add the --cm flag for evaluation statistics (heavy). Usage: ` + config.CommandPrefix + `retrain [--cm]`
