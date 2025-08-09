# hearsay
An authorship attribution and NLP bot for IRC. Built in Go (1.24.4) and Python 3.

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Examples](#examples)
- [License](#license)

## Features
- Store and track messages from IRC channels
- Attribute a given message to the most likely user (`+attribute <message>`)
- Flesch-Kincaid readability scores (`+readability`)
- Extensive opt and privacy features (opt-out by default)
- Go-based IRC handling. Python-based NLP processing

## Installation
hearsay uses the [GoIRC](https://github.com/fluffle/goirc) client for IRC connections and handling, [go-sqlite3](https://github.com/mattn/go-sqlite3) for persistent storage, and [scikit-learn](https://scikit-learn.org/) for machine learning tasks. A local Python HTTP [API](https://fastapi.tiangolo.com/) relays NLP information back to the Go client.

It is highly recommended to use the provided Docker configuration to run hearsay. To build and run the bot, run `sudo docker compose up --build --detach` in the base directory.

> [!IMPORTANT]
> The bot is automatically configured to connect to `irc.zoite.net`. Change this before running the bot. See [Configuration](#configuration) for more.

This might take a while.

## Configuration
The configuration file is located in `bot/config.yaml`. Before anything else, the default values must be changed to match your and your server's expectations.

```yaml
bot:
  prefix: "+"
  mode: "+B"
  server: "irc.zoite.net:6697"
  channel: "#antisocial"

storage:
  message_pool_size: 20
  message_quota: 400
  people_quota: 5

scheduler:
  deletion_days: 1
```

- `prefix`: The bot prefix. If a message starts with this symbol or string, it will be activated. In case of prefix conflict with existing bots, change this.
- `mode`: This are the positive or (exclusive) negative modes to be set on the bot. `+B` is a common mode for server bots.
- `server`: Server and port to connect to on start-up.
- `channel`: Channel to connect to on start-up.
- `message_pool_size`: By default, hearsay does not submit an incoming message to the database when received. Instead, it waits for a message pool to fill up before creating a transaction where all (in this case 20) messages are submitted. This prevents frequent I/O. Depending on server size, you might want to adjust this value, but 20 is a good middle ground.
- `message_quota`: This is an important setting. Before users can access NLP commands, they must fulfil a message quota. If the message quota is too low, the bot will make inaccurate assessments. Four-hundred is on the lower side.
- `people_quota`: Before authorship attribution commands can be used, five people must fulfil the `message_quota`. With a lower `people_quota`, the author population becomes less diverse. Five is a good start for small to medium big servers.
- `deletion_days`: When a user issues the `forget` command, all their data will be purged. To prevent accidental deletions, their request is put on a schedule. After one day, their data will be deleted. Note that `deletion_days` cannot be lower than one.

## Usage

To get help on a command, use the `help` command. This will display. Available commands are attribute, opt, forget, unforget, help, readability, retrain, and about.

- `attribute`: Attribute a message to a chatter who is opted in and fulfils the message quota. Usage: `+attribute <message>`
- `opt`:  Opt in or out from data collection and model training. If no arguments are submitted, your current opt status will be returned. Usage: `+opt [in|out] (default: out)`
- `forget`: Permanently purge all your data. Usage: `+forget`
- `unforget`: Cancel a scheduled data deletion. Usage: `+unforget`
- `help`: Get information on a command. Usage: `help [command]`
- `readability`: Calculate the Flesch-Kincaid readability score of your messages (10,000 limit). Usage: `+readability`
- `retrain`: Refit the SVM classification model. This can be done every 2 hours. Add the --cm flag for evaluation statistics (heavy). Usage: `+retrain [--cm]`
- `about`: Information about hearsay. Usage: `+about`

## Examples
Coming soon.

## License
This project is unlicensed. The bot may be used in any and all ways, with or without credit.