package core

import (
	"crypto/tls"
	"database/sql"
	"fmt"
	"log"
	"strconv"
	"strings"

	"hearsay/internal/commands"
	config "hearsay/internal/config"
	storage "hearsay/internal/storage"

	irc "github.com/fluffle/goirc/client"
	"golang.org/x/net/context"
)

var messagePool []storage.Message

func HearsayConnect(Server string, Channel string, ctx context.Context, db *sql.DB) {
	botNick := "hearsay" // TODO: Move to configure.go
	botUser := "hearsay"
	botMe := "hearsay"

	cfg := irc.NewConfig(botNick, botUser, botMe)

	// https://github.com/fluffle/goirc/blob/v1.3.1/client/connection.go#L144
	cfg.Version = "Bot"
	cfg.SSL = true
	cfg.SSLConfig = &tls.Config{InsecureSkipVerify: true}
	cfg.Server = Server

	c := irc.Client(cfg)

	quit := make(chan struct{})

	// These are handlers and WILL DO STUFF.
	c.HandleFunc(irc.CONNECTED,
		func(c *irc.Conn, l *irc.Line) {
			c.Join(Channel)
			c.Mode(botNick, config.BotMode)
			c.Away(config.CommandPrefix + "help for command list.")
			log.Printf("Joined %s\n", Channel)

			log.Println("Loading deletion scheduler...")
			go commands.DeletionWrapper(db, c)
		})

	c.HandleFunc(irc.PRIVMSG,
		func(c *irc.Conn, l *irc.Line) {
			incomingMessageAuthor := GetNickFromRawMessage(l.Raw)
			incomingMessageContent := GetContentFromRawMessage(l.Raw)
			incomingMessageChannel := GetChannelFromRawMessage(l.Raw)
			messageFinal := storage.Message{
				Nick:      incomingMessageAuthor,
				Content:   incomingMessageContent,
				Channel:   incomingMessageChannel,
				Timestamp: l.Time,
			}

			if strings.HasPrefix(incomingMessageContent, config.CommandPrefix) {
				commandAndArgs := strings.Split(incomingMessageContent, " ")
				receivedCommand := commandAndArgs[0]
				receivedArgs := commandAndArgs[1:]
				log.Printf("Received command %s by %s.\n", receivedCommand, incomingMessageAuthor)

				if cmd, ok := commands.Commands[receivedCommand]; ok {
					c.Privmsg(incomingMessageChannel, cmd.Handler(receivedArgs, incomingMessageAuthor, db))
				} else {
					c.Privmsgf(incomingMessageChannel, "No such command: %s", receivedCommand)
				}
			}

			if !storage.IfOptedOut(incomingMessageAuthor) {
				messagePool = append(messagePool, messageFinal)
				if len(messagePool) == config.MaxMessagePool {
					err := storage.SubmitMessages(messagePool, db) // This function is blocking. Having a large pool might cause the bot to miss messages.
					if err != nil {
						log.Fatalf("Failed to submit messages: %v\n", err.Error())
					} else {
						log.Println("Wrote " + strconv.Itoa(len(messagePool)) + "/" + strconv.Itoa(config.MaxMessagePool) + " messages to database.")
						messagePool = nil
					}
				}
			}
		})

	c.HandleFunc(irc.INVITE,
		func(c *irc.Conn, l *irc.Line) {
			channelToJoin := GetChannelFromInvite(l.Raw)
			c.Join(channelToJoin)
			log.Printf("Joined channel %s\n", channelToJoin)
		})

	c.HandleFunc(irc.DISCONNECTED,
		func(c *irc.Conn, l *irc.Line) {
			close(quit)
		})

	if err := c.Connect(); err != nil {
		fmt.Printf("Connection error: %s\n", err.Error())
		return
	}

	select {
	case <-ctx.Done():
		log.Println("Conext canceled. Sending QUIT...")
		c.Quit("Signing off.")
		c.Close()

	case <-quit:
		log.Println("Received server-side disconnect (such as /kill or unavailability)")
	}
}
