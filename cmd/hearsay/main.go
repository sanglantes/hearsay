package main

import (
	"context"
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
		core.HearsayConnect("192.168.10.137:6697", "#antisocial", ctx, db)
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
