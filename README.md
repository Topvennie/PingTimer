# PingTimer
_Never have someone spamming role pings again_

## About PingTimer
PingTimer is a verified discord bot that allows server owners to add a custom cooldown on a role.\
This allows your community to ping roles but to still have some control over it.


## Invite Links
**With Slash Commands**\
Click [here](https://discord.com/api/oauth2/authorize?client_id=844191455757205554&permissions=268504064&scope=bot%20applications.commands) to invite PingTimer with Slash Commands.\
Slash commands allows you to replace the prefix by a `/` and gives a small on what arguments the command expects.

**Without Slash Commands**\
Click [here](https://discord.com/api/oauth2/authorize?client_id=844191455757205554&permissions=268504064&scope=bot) to invite PingTmer without Slash Commands.


## Command Overview
The prefix is `pt!`.\
If you invited PingTimer **with Slash Commands** then you replace `pt!` by `/` for every command.\
Replace `[]` _including the brackets themselves_ with the desired value.


### Setup
- `pt!check` -> Checks if PingTimer has the required permissions.
- `pt!other` -> Gives you a little bit more information about the bot, the requirements, ...

### Role Management
- `pt!add [role] [time interval]` -> Adds a new cooldown on a role. 
- `pt!remove [role]` -> Removes the cooldown of a role

### User Commands
- `pt!list` -> Gives an overview of every role that has a cooldown and the time left of the cooldown.
- `pt!invite` -> Gives you the invite link for the bot.

### Support
- `pt!contact` -> Gives you my discord information in case you need more support.


## Upcoming Features
- Let the bot ping a role every X minutes / hours / days / ...
- Ping a role for example every Sunday at 12:00
- Custom prefix

## Some Examples
Some quick examples on how to add roles.

#### Cooldown of 90 minutes
`pt!add @role_1 90 minutes`
#### Cooldown of one week
`pt!add @role_1 7 days`
#### Cooldown of 8 hours
`pt!add @role_1 8 hours`

## FAQ
**Q:** I can't add a cooldown on a role!\
**A:** Make sure _you_ have the `manage roles` permission. 

##

**Q:** How do I specify the role for `pt!add` and `pt!remove`?\
**A:** You can either ping the role, use the [role id](https://discordhelp.net/role-id) or use its name.

##

**Q:** What can I use as time interval for the command `pt!add`?\
**A:** You can either use minutes, hours or days. _Not_ a combination of them. You can see some examples in the "Some Examples" section

##

**Q:** I can't add any roles\
**A:** Use the command `pt!check`. Does it say that Pingtimer is functional? If not follow the given instructions.

##

**Q:** How do I make the bot ping a role every day at midnight?\
**A:** That's an upcoming feature and thusfor not possible at the moment.