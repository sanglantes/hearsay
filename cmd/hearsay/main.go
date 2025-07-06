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

	db := storage.InitDatabase()
	defer db.Close()

	serverDisconnect := make(chan struct{}) // We use an empty struct (0 bytes) to emphasize a signal is being closed with close(). Booleans are ambiguous.
	go func() {
		core.HearsayConnect("192.168.10.137:6697", "#cat", ctx, db)
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
