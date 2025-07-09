package main

import (
	"context"
	"flag"
	"hearsay/internal/config"
	"hearsay/internal/core"
	"hearsay/internal/storage"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"
)

func main() {
	log.Println("hearsay is starting...")

	var serverAddress *string = flag.String("s", "localhost:6697", "server address and port. example: irc.example.net:6697")
	var channel *string = flag.String("c", "#test", "channel to join. example: #test")
	flag.Parse()

	configPath := "config.yaml"
	log.Printf("Reading config from %s.\n", configPath)
	err := config.ReadConfig(configPath, true)
	if err != nil {
		log.Fatalln("Failed to load configuration.")
	} else {
		log.Println("Successfully loaded configuration.")
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)

	db, err := storage.InitDatabase()
	if err != nil {
		log.Fatalln("Failed DB init.")
	} else {
		log.Println("Passed DB init.")
	}

	defer db.Close()

	if err = storage.LoadOptOuts(db); err != nil {
		log.Fatalf("Failed loading opt-out map: %s\n", err.Error())
	} else {
		log.Println("Passed opt-out loading.")
	}

	serverDisconnect := make(chan struct{}) // We use an empty struct (0 bytes) to emphasize a signal is being closed with close(). Booleans are ambiguous.
	go func() {
		core.HearsayConnect(*serverAddress, *channel, ctx, db)
		close(serverDisconnect)
	}()

	select {
	case <-sigs:
		log.Println("Termination signal received. Shutting down...")
		cancel()
		time.Sleep(2 * time.Second)

	case <-serverDisconnect:
		return
	}

}
