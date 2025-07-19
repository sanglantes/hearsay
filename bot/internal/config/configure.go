package config

import (
	"log"
	"os"

	"gopkg.in/yaml.v3"
)

var CommandPrefix = "+"
var BotMode = "+B"
var MaxMessagePool = 30
var DeletionDays = 1
var MessageQuota = 100
var PeopleQuota = 5

type BotStruct struct {
	Prefix string `yaml:"prefix"`
	Mode   string `yaml:"mode"`
}

type StorageStruct struct {
	MessagePoolSize int `yaml:"message_pool_size"`
	MessageQuota    int `yaml:"message_quota"`
	PeopleQuota     int `yaml:"people_quota"`
}

type SchedulerStruct struct {
	DeletionDays int `yaml:"deletion_days"`
}

type ConfigStruct struct {
	Bot       BotStruct       `yaml:"bot"`
	Storage   StorageStruct   `yaml:"storage"`
	Scheduler SchedulerStruct `yaml:"scheduler"`
}

func ReadConfig(path string, verbose bool) error {
	yamlFile, err := os.ReadFile(path)
	if err != nil {
		log.Printf("Failed to open config file: %s\n", err)
		return err
	}

	var cfg ConfigStruct
	err = yaml.Unmarshal(yamlFile, &cfg)
	if err != nil {
		log.Printf("Failed to unmarshal YAML: %s\n", err)
		return err
	}

	if cfg.Bot.Prefix != "" {
		CommandPrefix = cfg.Bot.Prefix
	}
	if cfg.Bot.Mode != "" {
		BotMode = cfg.Bot.Mode
	}

	if cfg.Storage.MessagePoolSize > 0 {
		MaxMessagePool = cfg.Storage.MessagePoolSize
	}

	if cfg.Storage.MessageQuota > 0 {
		MessageQuota = cfg.Storage.MessageQuota
	}

	if cfg.Storage.PeopleQuota > 0 {
		PeopleQuota = cfg.Storage.PeopleQuota
	}

	if cfg.Scheduler.DeletionDays > 0 {
		DeletionDays = cfg.Scheduler.DeletionDays
	}

	if verbose {
		log.Printf("Configuration:\nPrefix: %s\nMode: %s\nPool size: %d\nQuota: %d\nDeletion: %d\n", CommandPrefix, BotMode, MaxMessagePool, MessageQuota, DeletionDays)
	}

	return nil
}
