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

var Commands = make(map[string]Command)

func init() {
	Commands["attribute"] = Command{attributeHandler, attributeHelp}
	Commands["opt"] = Command{optHandler, optHelp}
	Commands["forget"] = Command{forgetHandler, forgetHelp}
	Commands["unforget"] = Command{unforgetHandler, unforgetHelp}
	Commands["help"] = Command{helpHandler, helpHelp}
}
