// +attribute
// +opt in/out
// +delete
// +mystats
// +explain
// +compare
// +topwords

package commands

import "database/sql"

type CommandFunc func(args []string, author string, db *sql.DB) string
type Command struct {
	Handler     CommandFunc
	Description string
}

var Commands = map[string]Command{
	"+attribute": {
		Handler:     attributeHandler,
		Description: attributeHelp,
	},

	"+opt": {
		Handler:     optHandler,
		Description: optHelp,
	},
}
