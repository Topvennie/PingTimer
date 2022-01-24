import asyncio
import json
import logging
from datetime import datetime
from math import ceil

import discord
from discord.ext import commands, tasks
from discord_slash import SlashCommand, SlashContext


########################
#                      #
#   Global variables   #
#                      #
########################

minutes = ["minutes", "minute", "min", "mins", "m"]
hours = ["hours", "hour", "h", "hr", "hrs"]
days = ["days", "d", "ds"]


#######################
#                     #
#   Bot initalizing   #
#                     #
#######################

prefix = "pt!"
bot = commands.Bot(
    command_prefix=prefix,
    help_command=None,
    activity=discord.CustomActivity("Listening for pt!help"),
    allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False, replied_user=False)
)
bot.remove_command("help")
slash = SlashCommand(bot, sync_commands=True)


########################
#                      #
#   Common functions   #
#                      #
########################

# Reads the data of a JSON file
def read_json() -> dict:
    with open("pingtimer.json", "r") as file:
        data = json.load(file)
        file.close()
    return data


# Dump data in a JSON file
def dump_json(data:dict) -> None:
    with open("pingtimer.json", "w") as file:
        json.dump(data, file)
        file.close()


# Returns the current unix time in UTC
def get_unix_time() -> int:
    return round((datetime.utcnow() - datetime(year=1970, month=1, day=1)).total_seconds())


# Returns wether the time period is specified in minutes or hours
def interval(seconds:int) -> str:
    text = ""
    minutes = seconds / 60

    if 1440 <= minutes:
        days = minutes / 1440
        if days.is_integer():
            days = round(days)
        else:
            days = round(days, 1)
        if days == 1:
            text = f"**{str(days)}** Day"
        else:
            text = f"**{str(days)}** Days"
    elif 60 <= minutes < 1440:
        hours = minutes / 60
        if hours.is_integer:
            hours = round(hours)
        else:
            hours = round(hours, 1)
        if hours == 1:
            text = f"**{str(hours)}** Hour"
        else:
            text = f"**{str(hours)}** Hours"
    else:
        if minutes == 1:
            text = f"**{str(round(minutes))}** Minute"
        else:
            text = f"**{str(round(minutes))}** Minutes"

    return text


# Calculates when the next ping is
def nt_ping(unix:int) -> str:
    text = ""
    today = get_unix_time()
    if unix - today <= 0:
        text = "**Now**"
        return text
    else:
        minutes_one = (unix - today) / 60
        hours = ceil(minutes_one // 60)
        minutes = ceil(minutes_one % 60)
        if hours == 23 and minutes == 60:
            text = "`1` Day"
        elif hours >= 24:
            days = hours / 24
            if days.is_integer():
                days = round(days)
            else:
                days = round(days, 1)
            text = f"`{str(days)}` Day(s)"
        elif hours == 0:
            text = f"`{str(minutes)}` Minute(s)"
        else:
            text = f"`{str(hours)}` Hour(s) `{str(minutes)}` Minute(s)"
    return text


# Removes a role from the JSON file
def remove_deleted_roles(guild_id:int, role_id:int) -> None:
    data = read_json()
    del data[str(guild_id)][str(role_id)]
    dump_json(data)


#######################
#                     #
#   Async functions   #
#                     #
#######################

async def send_embed(channel:discord.TextChannel, description:str=None) -> None:
    embed = discord.Embed(
        description=description,
        colour=discord.Colour.from_rgb(255,255,255)
    )
    try:
        await channel.send(embed=embed)
    except:
        return


# Allows a role to be mentioned again
async def mention(role:discord.Role, guild_id:int) -> None:
    data = read_json()
    if int(data[str(guild_id)][str(role.id)][1]) - 60 <= get_unix_time():
        try:
            await role.edit(mentionable=True, reason="Cooldown expired!")
        except:
            return



####################
#                  #
#   Bot commands   #
#                  #
####################

# Adds a new ping timer
@bot.command(aliases=["add", "a"])
@commands.has_guild_permissions(manage_roles=True)
async def _add(ctx, role:discord.Role=None, *, given_time:str=None) -> None:
    if role is None or given_time is None:
        await send_embed(ctx.channel, "There are some required arguments missing!\nUse the `help` command if you need some help!")
        return

    time = ""
    is_minutes = False
    is_hours = False
    is_days = False

    in_words = ""

    if role.is_default():
        await send_embed(ctx.channel, f"Unfortunately I can't add a timer on {role.mention}")
        return

    me = ctx.guild.me
    if me.top_role <= role:
        await send_embed(ctx.channel, f"I can't add {role.mention} because it's higher in the role hierarchy than my highest role {me.top_role.mention}.")
        return

    if not me.guild_permissions.manage_roles:
        await send_embed(ctx.channel, "I need the `manage roles` permission in order to add roles.\nUse the `help` command if you need some help!")
        return

    for item in minutes:
        if item in given_time:
            is_minutes = True
            in_words = "minute(s)"
    for item in hours:
        if item in given_time and not is_minutes:
            is_hours = True
            in_words = "hour(s)"
    for item in days:
        if item in given_time and not is_minutes and not is_hours:
            is_days = True
            in_words = "day(s)"

    if not is_minutes and not is_hours and not is_days:
        await send_embed(ctx.channel, "Make sure to use a valid time interval!\nUse the `help` command if you need some help!")
        return

    for letter in given_time:
        if letter.isnumeric():
            time += letter

    if len(time) == 0:
        await send_embed(ctx.channel, "Don't forget to specify an amount!\nUse the `help` command if you need some help!")
        return

    time = int(time)
    if time <= 0:
        await send_embed(ctx.channel, "The given time interval has to be greater than 0!\nUse the `help` command if you need some help!")
        return

    try:
        await role.edit(mentionable=False, reason=f"{ctx.author.name}#{ctx.author.discriminator} added a timer on the role.")
    except discord.Forbidden:
        await send_embed(ctx.channel, "I can't seem to edit the role.\nUse the `check` command to find out why!")
        return

    if is_minutes:
        sec_time = time * 60
    elif is_hours:
        sec_time = time * 3600
    elif is_days:
        sec_time = time * 86400


    data = read_json()
    try:
        guild_data = data[str(ctx.guild.id)]
        guild_data.update({str(role.id) : [str(sec_time), str(get_unix_time())]})
        data[str(ctx.guild.id)] = guild_data
    except KeyError:
        data[str(ctx.guild.id)] = {str(role.id) : [str(sec_time), str(get_unix_time())]}
    dump_json(data)

    await send_embed(ctx.channel, f"{role.mention} can now be pinged every {str(time)} {in_words}")


# Removes a timer on a role
@bot.command(aliases=["remove", "r"])
@commands.has_guild_permissions(manage_roles=True)
async def _remove(ctx, role:discord.Role=None) -> None:
    if role is None:
        await send_embed(ctx.channel, "There are some required arguments missing!\nUse the `help` command if you need some help!")
        return

    data = read_json()

    try:
        del data[str(ctx.guild.id)][str(role.id)]
        dump_json(data)
    except KeyError:
        await send_embed(ctx.channel, f"You don't have a timer set up for {role.mention}.")
        return

    try:
        await role.edit(mentionable=True, reason=f"{ctx.author.name}#{ctx.author.discriminator} removed the timer on {role.name}.")
        description = f"The timer on {role.mention} has been removed."
    except discord.Forbidden:
        if role.mentionable:
            description = f"The timer on {role.mention} has been removed.\nRight now the role is mentionable! You can change that in the role permissions."
        else:
            description = f"The timer on {role.mention} has been removed."

    await send_embed(ctx.channel, description)


# Returns a list of every pingable role and how long until the next ping
@bot.command(aliases=["list", "ping", "l", "p", "pings", "roles"])
async def _list(ctx) -> None:
    role_names=""
    ping_interval=""
    next_ping=""
    data = read_json()
    try:
        data = data[str(ctx.guild.id)]
    except KeyError:
        await send_embed(ctx.channel, "There aren't any timers set up!")
        return

    embed = discord.Embed(
        title = "Ping menu",
        colour = discord.Colour.from_rgb(255, 255, 255)
        )
    for item in data:
        role = ctx.guild.get_role(int(item))
        if role is None:
            remove_deleted_roles(ctx.guild.id, item)
            continue
        role_names += role.mention + "\n"
        ping_interval += interval(int(data[item][0])) + "\n"
        next_ping += nt_ping(int(data[item][1])) + "\n"

    embed.add_field(name="Role Name", value=role_names, inline=True)
    embed.add_field(name="Ping Interval", value=ping_interval, inline=True)
    embed.add_field(name="Next Ping", value=next_ping, inline=True)
    try:
        await ctx.send(embed=embed)
    except:
        return


@bot.command(aliases=["check", "c"])
@commands.has_permissions(manage_roles=True)
async def _check(ctx) -> None:
    me = ctx.guild.me
    manage_roles_permission = me.guild_permissions.manage_roles

    all_roles_array = []
    all_roles = ""
    for role in ctx.guild.roles:
        if role < me.top_role and not role.is_default():
            all_roles_array.insert(0, role.mention)

    if len(all_roles_array) > 0:
        for role in all_roles_array:
            all_roles += f"{role} "

    if manage_roles_permission and len(all_roles_array) > 1:
        title = "PingTimer is functional!"
        description = "You're able to set timers on roles. Underneath you can find a list of all the available roles that you can add."
    else:
        title = "PingTimer is **not** functional!"
        if manage_roles_permission:
            description = "I currently have the lowest role in the server. This means that I can't set any timers as there are no roles underneath me.\nYou can solve this by moving my up the role hierarchy."
        else:
            description = "I don't have the `manage roles` permission which is required for me to function properly!\nYou can solve this by giving my highest role the `manage roles` permission."

    embed = discord.Embed(
        title=title,
        colour=discord.Colour.from_rgb(255, 255, 255),
        description=description
    )

    if manage_roles_permission and all_roles != "":
        embed.add_field(name=f"Roles [{len(all_roles_array)}]", value=all_roles, inline=False)

    try:
        await ctx.send(embed=embed)
    except:
        return


@bot.command(aliases=["contact"])
@commands.has_permissions(manage_roles=True)
async def _contact(ctx) -> None:
    await send_embed(ctx.channel, "If need help with something, want to report a bug, suggest something, ... do __not__ hesitate to contact me!\nMy discord name is vincent#3609")


@bot.command(aliases=["invite"])
async def _invite(ctx) -> None:
    embed = discord.Embed(
        colour = discord.Colour.from_rgb(255, 255, 255),
        description = """▫️Click [here](https://discord.com/api/oauth2/authorize?client_id=844191455757205554&permissions=268504064&scope=bot%20applications.commands) to invite the bot **with** slash commands.\n
                        ▫️Click [here](https://discord.com/api/oauth2/authorize?client_id=844191455757205554&permissions=268504064&scope=bot) to invite the bot **without** slash commands.\n
                        ▫️If you don't know what slash commands are you can find more information [here](https://support.discord.com/hc/en-us/articles/1500000368501-Slash-Commands-FAQ)"""
    )
    try:
        await ctx.send(embed=embed)
    except:
        pass


@bot.command(aliases=["other", "o"])
@commands.has_permissions(manage_roles=True)
async def _other(ctx) -> None:
    embed = discord.Embed(
        colour=discord.Colour.from_rgb(255, 255, 255)
    )
    embed.add_field(name="Additional remarks", value=f"""▫️PingTimer fully supports slash commands! This means you can use each command by using a `/` instead of `pt`! If none of the slash commands show up kick the bot and reinvite him using the right `pt!invite` link.
                    ▫️Only members with the `manage roles` permission can add or remove roles.\n
                    ▫️I require the `manage roles` in order to add timers on roles!\n
                    ▫️If you want to edit the timer on a role then you can either remove and add it again or simply use `{prefix}add [role] [new time interval]`.\n
                    ▫️You can specify a role by either mentioning it or giving it's id.\n
                    ▫️Anyone who has the 'mention @ everyone @ here and all roles' permission will be able to ping the roles at all times!\n
                    ▫️To specify a time interval you can use minutes, hours or days. __Not__ a combination of them. A couple of examples:\n
                    `{prefix}add @role_1 20minutes` | `{prefix}add @role_2 1 day` | `{prefix}add @role_3 36 hours`""", inline=False)

    try:
        await ctx.send(embed=embed)
    except:
        return


@bot.command(aliases=["help", "setup", "how", "start", "h"])
@commands.has_permissions(manage_roles=True)
async def _help(ctx) -> None:
    embed = discord.Embed(
        title="Help menu",
        colour=discord.Colour.from_rgb(255, 255, 255),
        description="Replace [ ] with the desired value"
    )
    embed.add_field(name="Commands", value=f"""▫️`{prefix}add [role] [time interval]` - Sets a timer on a given role.\n
                    ▫️`{prefix}remove [role]` - Removes the timer on a given role.\n
                    ▫️`{prefix}list` - Lists all the roles with a timer. Everyone can use this command.\n
                    ▫️`{prefix}check` - Will check if the bot has the required permissions and give a list of roles you can add.\n
                    ▫️`{prefix}other` - Shows some additional remarks\n
                    ▫️`{prefix}invite` - Gives the invite links for the bot.\n
                    ▫️`{prefix}contact` - Use this command to report any bugs or to suggest something!""", inline=False)

    embed.set_footer(text="PingTimer fully supports slash commands!")

    try:
        await ctx.send(embed=embed)
    except:
        return


@bot.command(aliases=["stats"])
@commands.is_owner()
async def _stats(ctx) -> None:
    amount_of_guilds = 0
    amount_of_roles = 0
    data = read_json()

    for guild_id in data:
        amount_of_guilds += 1

        for role_id in data[guild_id]:
            amount_of_roles += 1

    await send_embed(ctx.channel, f"Keeping track of {amount_of_roles} roles in {amount_of_guilds} guilds.\nIn total we're in {len(bot.guilds)} guilds.")


@bot.command()
@commands.is_owner()
async def do_it(ctx) -> None:
    for guild in bot.guilds:
        try:
            await guild.owner.send("hi")
        except:
            pass



#################
#               #
#   Listeners   #
#               #
#################

# Listens to messages to see if someone mentions someone
@bot.event
async def on_message(message:discord.Message) -> None:
    if message.author.bot == True:
        return
    if message.content.startswith(prefix):
        await bot.process_commands(message)
        return
    if len(message.content) <= 21:
        return
    if message.raw_role_mentions is not None:
        data = read_json()
        try:
            guild_data = data[str(message.guild.id)]
        except KeyError:
            return
        for item in guild_data.keys():
            if int(item) in message.raw_role_mentions:
                role = message.guild.get_role(int(item))
                try:
                    await role.edit(mentionable=False, reason=f"{message.author.name}#{message.author.discriminator} pinged the role!")
                except:
                    return
                guild_data[item][1] = str(get_unix_time() + int(guild_data[item][0]))
                data[str(message.guild.id)] = guild_data
                Timer(int(guild_data[item][0]), mention, role, message.guild.id)
                dump_json(data)


# Called when gets kicked from a guild
@bot.event
async def on_guild_remove(guild:discord.Guild) -> None:
    data = read_json()
    try:
        del data[str(guild.id)]
    except KeyError:
        pass

    dump_json(data)


# Activates when the bot is ready
@bot.event
async def on_ready() -> None:
    await bot.wait_until_ready()

    amount_of_guilds = 0
    amount_of_roles = 0
    data = read_json()

    for guild_id, guild_roles in list(data.items()):
        guild = bot.get_guild(int(guild_id))
        if guild is None:
            del data[guild_id]
            continue

        amount_of_guilds += 1

        for role_id, v in list(guild_roles.items()):
            role = guild.get_role(int(role_id))
            if role is None:
                del data[guild_id][role_id]
                continue

            try:
                await role.edit(mentionable=True, reason="Bot restart")
                data[guild_id][role_id][1] = 0
            except:
                pass

            amount_of_roles += 1

    dump_json(data)

    clean_data.start()
    logging.info(f"Bot started! Keeping track of {amount_of_roles} roles in {amount_of_guilds} guilds.")


@bot.event
async def on_command_error(ctx, error):
    logging.error(f"Error in {ctx.guild.name} by {ctx.author.name}#{ctx.author.discriminator}. {error}")


######################
#                    #
#   Slash commands   #
#                    #
######################

# Slash command to add a timer
@slash.slash(name="add", description="Adds a timer on a role.")
@commands.has_permissions(manage_roles=True)
async def __add(ctx:SlashContext, role:discord.Role, *, timer:str):
    time = ""
    is_minutes = False
    is_hours = False
    is_days = False

    in_words = ""

    if role.is_default():
        await ctx.send(embed=discord.Embed(colour=discord.Colour.from_rgb(255,255,255), description=f"Unfortunately I can't add a timer on {role.mention}"))
        return

    me = ctx.guild.me
    if me.top_role <= role:
        await ctx.send(embed=discord.Embed(colour=discord.Colour.from_rgb(255,255,255), description=f"I can't add {role.mention} because it's higher in the role hierarchy than my highest role {me.top_role.mention}."))
        return

    if not me.guild_permissions.manage_roles:
        await ctx.send(embed=discord.Embed(colour=discord.Colour.from_rgb(255,255,255), description="I need the `manage roles` permission in order to add roles.\nUse the `help` command if you need some help!"))
        return

    for item in minutes:
        if item in timer:
            is_minutes = True
    for item in hours:
        if item in timer and not is_minutes:
            is_hours = True
    for item in days:
        if item in timer and not is_minutes and not is_hours:
            is_days = True

    if not is_minutes and not is_hours and not is_days:
        await ctx.send(embed=discord.Embed(colour=discord.Colour.from_rgb(255,255,255), description="Make sure to use a valid time interval!\nUse the `help` command if you need some help!"))
        return

    for letter in timer:
        if letter.isnumeric():
            time += letter

    if len(time) == 0:
        await ctx.send(embed=discord.Embed(colour=discord.Colour.from_rgb(255,255,255), description="Don't forget to specify an amount!\nUse the `help` command if you need some help!"))
        return

    time = int(time)
    if time <= 0:
        await ctx.send(embed=discord.Embed(colour=discord.Colour.from_rgb(255,255,255), description="The given time interval has to be greater than 0!\nUse the `help` command if you need some help!"))
        return

    try:
        await role.edit(mentionable=False, reason=f"{ctx.author.name}#{ctx.author.discriminator} added a timer on {role.name}.")
    except discord.Forbidden:
        await ctx.send(embed=discord.Embed(colour=discord.Colour.from_rgb(255,255,255), description="I can't seem to edit the role.\nUse the `check` command to find out why!"))
        return

    if is_minutes:
        sec_time = time * 60
        if time == 1:
            in_words = "minute"
        else:
            in_words = f"{str(time)} minutes"
    elif is_hours:
        sec_time = time * 3600
        if time == 1:
            in_words = "hour"
        else:
            in_words = f"{str(time)} hours"
    elif is_days:
        sec_time = time * 86400
        if time == 1:
            in_words = "day"
        else:
            in_words = f"{str(time)} days"

    data = read_json()
    try:
        guild_data = data[str(ctx.guild.id)]
        guild_data.update({str(role.id) : [str(sec_time), str(get_unix_time())]})
        data[str(ctx.guild.id)] = guild_data
    except KeyError:
        data[str(ctx.guild.id)] = {str(role.id) : [str(sec_time), str(get_unix_time())]}
    dump_json(data)

    await ctx.send(embed=discord.Embed(colour=discord.Colour.from_rgb(255,255,255), description=f"{role.mention} can now be pinged every {in_words}"))


# Slash command to remove a timer
@slash.slash(name="remove", description="Removes a timer on a role.")
@commands.has_permissions(manage_roles=True)
async def __remove(ctx, role:discord.Role) -> None:
    data = read_json()

    try:
        del data[str(ctx.guild.id)][str(role.id)]
        dump_json(data)
    except KeyError:
        await ctx.send(embed=discord.Embed(colour=discord.Colour.from_rgb(255,255,255), description=f"You don't have a timer set up for {role.mention}."))
        return

    try:
        await role.edit(mentionable=True, reason=f"{ctx.author.name}#{ctx.author.discriminator} removed the timer on {role.name}.")
        description = f"The timer on {role.mention} has been removed."
    except discord.Forbidden:
        if role.mentionable:
            description = f"The timer on {role.mention} has been removed.\nRight now the role is mentionable! You can change that in the role permissions."
        else:
            description = f"The timer on {role.mention} has been removed."

    await ctx.send(embed=discord.Embed(colour=discord.Colour.from_rgb(255,255,255), description=description))


# Slash command to return a list of every pingable role and how long until the next ping
@slash.slash(name="list", description="Shows the remaining time on every role.")
async def __list(ctx) -> None:
    role_names=""
    ping_interval=""
    next_ping=""
    data = read_json()
    try:
        data = data[str(ctx.guild.id)]
    except KeyError:
        await ctx.send(embed=discord.Embed(colour=discord.Colour.from_rgb(255,255,255), description="There aren't any timers set up!"))
        return

    embed = discord.Embed(
        title = "Ping menu",
        colour = discord.Colour.from_rgb(255, 255, 255)
        )
    for item in data:
        role = ctx.guild.get_role(int(item))
        if role is None:
            remove_deleted_roles(ctx.guild.id, item)
            continue
        role_names += role.mention + "\n"
        ping_interval += interval(int(data[item][0])) + "\n"
        next_ping += nt_ping(int(data[item][1])) + "\n"

    embed.add_field(name="Role Name", value=role_names, inline=True)
    embed.add_field(name="Ping Interval", value=ping_interval, inline=True)
    embed.add_field(name="Next Ping", value=next_ping, inline=True)
    try:
        await ctx.send(embed=embed)
    except:
        return


# Slash command to check if the bot has the required permissions
@slash.slash(name="check", description="Checks if PingTimer has all the required permissions.")
@commands.has_permissions(manage_roles=True)
async def __check(ctx) -> None:
    me = ctx.guild.me
    manage_roles_permission = me.guild_permissions.manage_roles

    all_roles_array = []
    all_roles = ""
    for role in ctx.guild.roles:
        if role < me.top_role and not role.is_default():
            all_roles_array.insert(0, role.mention)

    if len(all_roles_array) > 0:
        for role in all_roles_array:
            all_roles += f"{role} "

    if manage_roles_permission and len(all_roles_array) > 1:
        title = "PingTimer is functional!"
        description = "You're able to set timers on roles. Underneath you can find a list of all the available roles that you can set a timer on."
    else:
        title = "PingTimer is **not** functional!"
        if manage_roles_permission:
            description = "I currently have the lowest role in the server. This means that I can't set any timers as there are no roles underneath me.\nYou can solve this by moving my up the role hierarchy."
        else:
            description = "I don't have the `manage roles` permission which is required for me to function properly!\nYou can solve this by giving my highest role the `manage roles` permission."

    embed = discord.Embed(
        title=title,
        colour=discord.Colour.from_rgb(255, 255, 255),
        description=description
    )

    if manage_roles_permission and all_roles != "":
        embed.add_field(name=f"Roles [{len(all_roles_array)}]", value=all_roles, inline=False)

    try:
        await ctx.send(embed=embed)
    except:
        return


# Slash command to make contact with me
@slash.slash(name="contact", description="Shows how to contact me for help.")
@commands.has_permissions(manage_roles=True)
async def __contact(ctx) -> None:
    try:
        await ctx.send(embed=discord.Embed(colour=discord.Colour.from_rgb(255,255,255), description="If need help with something, want to report a bug, suggest something, ... do __not__ hesitate to contact me!\nMy discord name is vincent#3609"))
    except:
        return


# Slash command to give the invite links
@slash.slash(name="invite", description="Gives the invite links")
async def __invite(ctx) -> None:
    embed = discord.Embed(
        colour = discord.Colour.from_rgb(255, 255, 255),
        description = """▫️Click [here](https://discord.com/api/oauth2/authorize?client_id=844191455757205554&permissions=268504064&scope=bot%20applications.commands) to invite the bot **with** slash commands.\n
                        ▫️Click [here](https://discord.com/api/oauth2/authorize?client_id=844191455757205554&permissions=268504064&scope=bot) to invite the bot **without** slash commands.\n
                        ▫️If you don't know what slash commands are you can find more information [here](https://support.discord.com/hc/en-us/articles/1500000368501-Slash-Commands-FAQ)"""
    )

    try:
        await ctx.send(embed=embed)
    except:
        return


# Slash command to display the other help menu
@slash.slash(name="other", description="Shows some additional remarks.")
@commands.has_permissions(manage_roles=True)
async def __other(ctx) -> None:
    embed = discord.Embed(
        colour=discord.Colour.from_rgb(255, 255, 255)
    )
    embed.add_field(name="Additional remarks", value=f"""▫️PingTimer fully supports slash commands! This means you can use each command by using a `/` instead of `pt!`
                    ▫️Only members with the `manage roles` permission can add or remove roles.\n
                    ▫️I require the `manage roles` in order to add timers on roles!\n
                    ▫️If you want to edit the timer on a role then you can either remove and add it again or simply use `{prefix}add [role] [new time interval]`.\n
                    ▫️You can specify a role by either mentioning it or giving it's id.\n
                    ▫️Anyone who has the 'mention @ everyone @ here and all roles' permission will be able to ping the roles at all times!\n
                    ▫️To specify a time interval you can use minutes, hours or days. __Not__ a combination of them. A couple of examples:\n
                    `{prefix}add @role_1 20minutes` | `{prefix}add @role_2 1 day` | `{prefix}add @role_3 36 hours`""", inline=False)

    try:
        await ctx.send(embed=embed)
    except:
        return


# Slash command to display the help menu
@slash.slash(name="help", description="Shows the help menu.")
@commands.has_permissions(manage_roles=True)
async def __help(ctx) -> None:
    embed = discord.Embed(
        title="Help menu",
        colour=discord.Colour.from_rgb(255, 255, 255),
        description="Replace [ ] with the desired value"
    )
    embed.add_field(name="Commands", value=f"""▫️`{prefix}add [role] [time interval]` - Sets a timer on a given role.\n
                    ▫️`{prefix}remove [role]` - Removes the timer on a given role.\n
                    ▫️`{prefix}list` - Lists all the roles with a timer. Everyone can use this command.\n
                    ▫️`{prefix}check` - Will check if the bot has the required permissions and give a list of roles you can add.\n
                    ▫️`{prefix}other` - Shows some additional remarks\n
                    ▫️`{prefix}contact` - Use this command to report any bugs or to suggest something!""", inline=False)

    embed.set_footer(text="PingTimer fully supports slash commands!")

    try:
        await ctx.send(embed=embed)
    except:
        return


############
#          #
#   Tasks  #
#          #
############

@tasks.loop(hours=168)
async def clean_data():
    amount_of_guilds = 0
    amount_of_roles = 0
    data = read_json()

    for guild_id, guild_roles in list(data.items()):
        guild = bot.get_guild(int(guild_id))
        if guild is None:
            del data[guild_id]
            amount_of_guilds += 1
            continue

        for role_id in guild_roles:
            role = guild.get_role(int(role_id))
            if role is None:
                del data[guild_id][role_id]
                amount_of_roles += 1
                continue

    logging.info(f"Weekly data clean. Removed {amount_of_guilds} guild(s) and {amount_of_roles} role(s).")


###################
#                 #
#   Timer class   #
#                 #
###################

# Class to wait a certain amount of seconds and then execute a command
class Timer:

    def __init__(self, timeout:int, callback, role:discord.Role, guild_id:int) -> None:
        self._timeout = timeout
        self._callback = callback
        self._role = role
        self._guild_id = guild_id
        self._task = asyncio.ensure_future(self._job())

    async def _job(self) -> None:
        await asyncio.sleep(self._timeout)
        await self._callback(self._role, self._guild_id)


#############
#           #
#   Start   #
#           #
#############

def start() -> None:
    with open("token.txt", "r") as file:
        token = file.readline()
    bot.run(token)


if __name__ == "__main__":
    logging.basicConfig(filename='info.log', encoding='utf-8', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.INFO)

    start()
