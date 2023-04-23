# PingTimer
_Never have someone spamming role pings again_

## About PingTimer
PingTimer is a verified discord bot that allows server owners to add a custom cooldown on a role.\
This allows your community to ping roles but to still have some control over it.


## Invite Links
**With Slash Commands**\
Click [here](https://discord.com/api/oauth2/authorize?client_id=844191455757205554&permissions=268504064&scope=bot%20applications.commands) to invite PingTimer with Slash Commands.

## Command Overview

### Setup
- `/check` - Checks if PingTimer has the required permissions.
- `/info` - Gives you a little more information about the bot.

### Role Management
- `/add [role] [time] [interval]` - Adds a new timer on a role. 
- `/remove [role]` -> Removes the timer of a role.

### User Commands
- `/list` -> Gives an overview of every role that has a timer and the time left on the timer.

### Support
- `/help` -> Displays the help menu.


## Upcoming Features
- Let the bot ping a role every X minutes / hours / days / ...
- Cooldown for new members to ping roles.
- Website.

## Some Examples
Some quick examples on how to add roles.

#### Cooldown of 90 minutes
`/add @role_1 90 minutes`
#### Cooldown of one week
`/!add @role_2 7 days`
#### Cooldown of 8 hours
`/add @role_3 8 hours`

## FAQ
**Q:** I can't add a cooldown on a role!\
**A:** Make sure _you_ have the `manage roles` permission. 

##

**Q:** How do I specify the role for `/add` and `/remove`?\
**A:** Select from the list.

##

**Q:** What intervals are supported?\
**A:** Minutes, Days and hours.

##

**Q:** I can't add any roles\
**A:** Use the command `/check`. If that doesn't help contact support with /help
