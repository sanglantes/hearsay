// +attribute
// +opt in/out
// +forget (formerly delete)
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

	"+forget": {
		Handler:     forgetHandler,
		Description: forgetHelp,
	},

	"+unforget": {
		Handler:     unforgetHandler,
		Description: unforgetHelp,
	},
}
