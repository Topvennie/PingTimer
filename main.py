from __future__ import annotations

import enum
import json
from datetime import datetime
from math import ceil
from typing import Dict, Optional

import discord
from discord import app_commands

MY_GUILD_ID = 1098923651371368568


########################
#                      #
#   Common Functions   #
#                      #
########################


# Read json file
def read_file(file='roles.json') -> Dict[str, Dict[str, Dict[str, list[int]]]]:
    with open(file, 'r') as f:
        data = json.load(f)
        f.close()

    return data


# Write data to json file
def write_file(data: dict) -> None:
    with open('roles.json', 'r') as f:
        json.dump(data, f)
        f.close()


# Returns the current unix time in UTC
def get_unix_time() -> int:
    return round((datetime.utcnow() - datetime(year=1970, month=1, day=1)).total_seconds())


# Returns the user's name + discriminator
def get_user_name(interaction: discord.Interaction) -> str:
    return f'{interaction.user.name}#{interaction.user.discriminator}'


# Removes a role's data
def remove_deleted_roles(guild_id: str, role_id: str) -> bool:
    found = False

    data = read_file()
    for interval in Interval:
        if guild_id in data[interval.name].keys() and role_id in data[interval.name][guild_id].keys():
            del data[interval.name][guild_id][role_id]
            found = True
            break

    write_file(data)

    return found


# Calculates when the next ping is
def calculate_next_ping(unix: int) -> str:
    today = get_unix_time()

    if unix - today <= 0:
        return '**Now**'

    total_minutes = (unix - today) / 60
    minutes = ceil(total_minutes % 60)
    hours = ceil(total_minutes // 60)

    if hours >= 24:
        days = round(hours / 24, 1)
        text = f'`{days}` Day{"s" if days > 0 else ""}'
    elif hours == 23 and minutes == 60:
        text = '`1` Day'
    elif hours == 0:
        text = f'`{minutes}` Minute{"s" if minutes > 0 else ""}'
    else:
        text = f'`{hours}` Hour{"s" if hours > 0 else ""} `{minutes}` Minute{"s" if minutes > 0 else ""}'

    return text


# Make en embed
def make_embed(title: str = '', description: str = '', colour: tuple[int, int, int] = (255, 255, 255)) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=description,
        colour=discord.Colour.from_rgb(colour[0], colour[1], colour[2])
    )


###############
#             #
#   Classes   #
#             #
###############


# Class for the discord client with syncing of slash commands
class Client(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.default())
        self.synced = False

    async def on_ready(self) -> None:
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync(guild=discord.Object(id=MY_GUILD_ID))
            self.synced = True
        print('Logged in')




class Interval(enum.Enum):
    minutes = 60
    hours = 3600
    days = 86400

    # def __new__(cls, *args, **kwargs) -> Interval:
    #     obj = object.__new__(cls)
    #     obj._value_ = args[0]
    #
    #     return obj
    #
    # def __init__(self, _: int, file: str = None) -> None:
    #     self._file_ = file
    #
    # @property
    # def file(self) -> str:
    #     return self._file_


#####################
#                   #
#   Bot Variables   #
#                   #
#####################


client = Client()
tree = app_commands.CommandTree(client)



###################
#                 #
#   Bot Command   #
#                 #
###################


# Adds a timer on a role
@tree.command(name='add', description='Add a timer on a role', guild=discord.Object(id=MY_GUILD_ID))
async def add_role(
        interaction: discord.Interaction,
        role: discord.Role,
        interval: Interval,
        time: app_commands.Range[int, 1, 200]
) -> None:

    try:
        await role.edit(mentionable=True, reason=f'{get_user_name(interaction)} added a timer on the role.')
    except discord.Forbidden:
        await interaction.response.send_message(
            f'I can\'t edit the role.\nUse `/check for more information`.',
            ephemeral=True
        )
        return

    seconds = interval.value * time
    data = read_file()

    for interv in Interval:
        if interv != interval and \
                str(interaction.guild_id) in data[interv].keys() and \
                str(role.id) in data[interv][str(interaction.guild_id)].keys():

            del data[interv][str(interaction.guild_id)][str(role.id)]

    if str(interaction.guild_id) in data.keys():
        data[interval.name][str(interaction.guild_id)].update({str(role.id): [str(seconds), str(get_unix_time())]})
    else:
        data[interval.name][str(interaction.guild_id)] = {str(role.id): [str(seconds), str(get_unix_time())]}

    write_file(data)

    await interaction.response.send_message(
        f'{role.mention} can now be pinged every {time} {str(interval)}.',
        ephemeral=True
    )


# Removes a timer of a role
@tree.command(name='remove', description='Remove a timer of a role', guild=discord.Object(id=MY_GUILD_ID))
async def remove_role(
        interaction: discord.Interaction,
        role: discord.Role
) -> None:

    found = remove_deleted_roles(str(interaction.guild_id), str(role.id))

    if not found:
        await interaction.response.send_message(
            embed=make_embed(description=f'No timer set up for {role.mention}.'),
            ephemeral=True)
    else:
        await interaction.response.send_message(
            embed=make_embed(description=f'Timer removed on {role.mention}.'),
            ephemeral=True)


# Lists all roles and their timers
@tree.command(name='list', description='List all pingable roles', guild=discord.Object(id=MY_GUILD_ID))
async def list_roles(
        interaction: discord.Interaction
) -> None:

    role_ids: Dict[int, tuple[list[int], Interval]] = {}
    roles: Dict[discord.Role, tuple[list[int], Interval]] = {}

    data = read_file()
    for interval in Interval:
        if str(interaction.guild_id) in data[interval.name].keys():
            for role_id, role_values in data[interval.name][str(interaction.guild_id)].items():
                role_ids.update({int(role_id): ([int(role_values[0]), int(role_values[1])], interval)})

    for role_id, role_values in role_ids.items():
        role = interaction.guild.get_role(role_id)

        if not role:
            remove_deleted_roles(str(interaction.guild_id), str(role_id))
        else:
            roles[role] = role_values

    if not roles:
        await interaction.response.send_message(embed=make_embed(description='No timers set up yet!'), ephemeral=False)
        return

    embed = make_embed(title='Ping Menu')

    role_names = ''
    ping_interval = ''
    next_ping = ''
    for role, values in roles.items():
        role_names += role.mention + '\n'
        ping_interval += f'{values[0][0] / values[1].value} {values[1].name}\n'
        next_ping += calculate_next_ping(values[0][1]) + '\n'

    embed.add_field(name='Role Name', value=role_names, inline=True)
    embed.add_field(name='Ping Interval', value=ping_interval, inline=True)
    embed.add_field(name='Next Ping', value=next_ping, inline=True)

    await interaction.response.send_message(embed=embed, ephemeral=False)


@tree.command(name='check', description='Check if the bot has the required permissions',
              guild=discord.Object(id=MY_GUILD_ID))
async def check(
        interaction: discord.Interaction
) -> None:

    me = interaction.guild.me
    highest_role: Optional[discord.Role] = None

    if me.top_role.permissions.manage_roles:
        highest_role = me.top_role
    else:
        for role in me.roles:
            if role.permissions.manage_roles:
                highest_role = role

    if not highest_role:
        await interaction.response.send_message(
            embed=make_embed(
                description='I don\'t have the manage roles permission in any of my roles!',
                colour=(255, 0, 0)
            ),
            ephemeral=True
        )
        return

    editable_role = 0
    for role in interaction.guild.roles:
        if role < highest_role:
            editable_role += 1
        else:
            break

    if not editable_role:
        await interaction.response.send_message(
            embed=make_embed(
                description='There are no roles that I can put a timer on!\n'
                            'You can fix it by giving me a higher role with the manage roles permission',
                colour=(255, 165, 0)
            ),
            ephemeral=True
        )
        return

    if highest_role != me.top_role:
        await interaction.response.send_message(
            embed=make_embed(
                description=f'I can put timers on `{editable_role}` role{"s" if editable_role > 1 else ""}.\n'
                            f'You can increase the amount of roles by giving my top role {me.top_role.mention} the manage '
                            'roles permission',
                colour=(0, 255, 0)
            ),
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            embed=make_embed(
                description=f'I can put timers on `{editable_role}` role{"s" if editable_role > 1 else ""}',
                colour=(0, 255, 0)
            ),
            ephemeral=True
        )


@tree.command(name='invite', description='Get an invitation link for the bot', guild=discord.Object(id=MY_GUILD_ID))
async def invite_bot(
        interaction: discord.Interaction
) -> None:

    await interaction.response.send_message(
        embed=make_embed(
            description='Click [here](https://discord.com/api/oauth2/authorize?client_id=844191455757205554&permissions'
                        '=268504064&scope=bot%20applications.commands) to invite the bot '
        ),
        ephemeral=False
    )


@tree.command(name='help', description='Show the help menu', guild=discord.Object(id=MY_GUILD_ID))
async def help_menu(
        interaction: discord.Interaction
) -> None:

    embed = make_embed(
        title='Help Menu',
        description='''Prevent users from spamming role pings!'''
    )

    embed.add_field(
        name='Features',
        value='Set timers on roles so that they can only be pinged every so often.\n\n'
              'Timers can be anywhere from 1 minute to 200 days',
        inline=True
    )
    embed.add_field(
        name='Support',
        value='Quick Troubleshooting:\n\n'
              'Make sure you have the `manage roles` permission.\n\n'
              'Check if the bot is allowed to make slash commands and has the `manage roles permission`.\n\n'
              'Use the command `/commands` to see all the commands\n\n'
              'Nothing working? Join the [support discord server](https://discord.gg/VNUG8xFZ2k) for more help!',
        inline=True
    )
    embed.add_field(
        name='Upcoming Features',
        value='Dashboard\n\n'
              'Prevent new users from pinging a role.\n\n'
              'Role requirements to ping certain roles.',
        inline=True
    )
    embed.add_field(
        name='Hide / commands',
        value='Normal users can only use the `/list` and `/invite` command.\n\n'
              'You can hide the other commands by going to:\n\n'
              'Server Settings -> Integrations -> PingTimer\n\n'
              'And restricting the other commands to Admins',
        inline=False
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


@tree.command(name='commands', description='Shows all the commands', guild=discord.Object(id=MY_GUILD_ID))
async def command_menu(
        interaction: discord.Interaction
) -> None:

    await interaction.response.send_message(
        embed=make_embed(
            title='Help Menu',
            description='▫ `/add [Role] [Time Interval] [Amount]` - Sets a timer on a given role.\n'
                        '▫ `/remove [Role]` - Removes the timer on a given role.\n'
                        '▫ `/check` - Checks if you can set timers.\n'
                        '▫ `/list` - Gives a list of all the roles and their cooldowns.\n'
                        '▫ `/invite` - Gives the invite link for the bot.\n'
                        '▫ `/help` - Shows the help menu.\n'
                        '▫ `/commands` - Shows this menu.'
        ),
        ephemeral=True
    )


##############
#            #
#   Events   #
#            #
##############


@client.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot:
        return

    if message.raw_role_mentions is not None and message.raw_role_mentions != []:
        data = read_file()
        guild = str(message.guild.id)
        found = False

        for role_id in message.raw_role_mentions:
            for interval in Interval:
                if guild in data[interval.name].keys() and str(role_id) in data[interval.name][guild].keys():
                    role = message.guild.get_role(role_id)
                    try:
                        await role.edit(
                            mentionable=False,
                            reason=f'{message.author.name}#{message.author.discriminator} pinged the role!'
                        )
                    except discord.Forbidden:
                        return

                    data[interval.name][guild][str(role_id)][1] = \
                        str(get_unix_time() + int(data[interval.name][guild][str(role_id)][0]))
                    write_file(data)

                    found = True
                    break

            if found:
                break


@client.event
async def on_guild_remove(guild: discord.Guild) -> None:
    data = read_file()

    for interval in Interval:
        if str(guild.id) in data[interval.name].keys():
            del data[interval.name][str(guild.id)]

    write_file(data)


client.run('')
