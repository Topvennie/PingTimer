import discord
from discord import app_commands
from common import make_embed, get_user_name, Colour, get_next_ping
from roleTracker import RoleTracker
from typing import Optional, Dict

import enum

MY_GUILD = 806209581855408178


# TODO: Refactor, clean up
def get_ping_interval(interval: int) -> str:
    for seconds, time_unit in time_intervals:
        if interval % seconds == 0:
            return f"{str(interval // seconds)} {time_unit}"


class PingTimer(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

    async def on_ready(self) -> None:
        await self.wait_until_ready()
        print('Logged in')


class Interval(enum.Enum):
    minutes = 60
    hours = 3600
    days = 86400


client = PingTimer()
roleTracker = RoleTracker()
time_intervals = [(interval.value, str(interval.name) for interval in Interval)]


##############
#            #
#   Events   #
#            #
##############


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')


@client.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot:
        return

    if message.raw_role_mentions:
        for role_id in message.raw_role_mentions:
            success = roleTracker.get_role(message.guild.id, role_id)
            if success:
                role = message.guild.get_role(role_id)
                if role:
                    try:
                        await role.edit(
                            mentionable=False,
                            reason=f"{message.author.name}#{message.author.discriminator} pinged the role!"
                        )
                        roleTracker.ping_role(message.guild.id, role_id)
                    except discord.Forbidden:
                        return


@client.event
async def on_guild_remove(guild: discord.Guild) -> None:
    roleTracker.remove_guild(guild.id)


################
#              #
#   Commands   #
#              #
################


@client.tree.command(name="add", description="Set a timer on a role")
async def _add_role(
        interaction: discord.Interaction,
        role: discord.Role,
        time: app_commands.Range[int, 1, 200],
        interval: Interval,
) -> None:
    try:
        await role.edit(mentionable=True, reason=f'{get_user_name(interaction)} added a timer on the role.')
    except discord.Forbidden:
        await interaction.response.send_message(
            embed=make_embed(
                description="Unable to set a timer on the role.\n"
                            "Use `/check` for more information.",
                colour=Colour.RED
            ),
            ephemeral=True
        )
        return

    seconds = interval.value * time
    success = roleTracker.add_role(interaction.guild_id, role.id, seconds)

    if success:
        embed = make_embed(
            description=f"{role.mention} can now be pinged every {time} {str(interval)}",
            colour=Colour.GREEN
        )
    else:
        await role.edit(mentionable=False, reason=f'{get_user_name(interaction)} added a timer on the role.')
        embed = make_embed(
            description="An error occurred while setting a timer.\n"
                        "Please try again.\n"
                        "If this error keeps occurring contact support with `/help`",
            colour=Colour.RED
        )
    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


@client.tree.command(name="remove", description="Delete a timer on a role")
async def _remove_role(
        interaction: discord.Interaction,
        role: discord.Role
) -> None:
    found, success = roleTracker.remove_role(interaction.guild_id, role.id)

    if not found:
        embed = make_embed(
            description=f"No timer set up for {role.mention}.",
            colour=Colour.RED
        )
    elif not success:
        embed = make_embed(
            description="An error occurred when removing the timer.\n"
                        "Please try again.\n"
                        "If this error keeps occurring contact support with `/help`",
            colour=Colour.RED
        )
    else:
        embed = make_embed(
            description=f"Timer removed off {role.mention}",
            colour=Colour.GREEN
        )
    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


@client.tree.command(name="reset", description="Reset a timer on a role")
async def _reset_role(
        interaction: discord.Interaction,
        role: discord.Role
) -> None:
    found, timer, success = roleTracker.remove_role(interaction.guild_id, role.id)

    if not found:
        embed = make_embed(
            description=f"No timer set up for {role.mention}.",
            colour=Colour.RED
        )
    elif not timer:
        embed = make_embed(
            description=f"{role.mention} is already mentionable"
        )
    elif not success:
        embed = make_embed(
            description="An error occurred when resetting the timer.\n"
                        "Please try again.\n"
                        "If this error keeps occurring contact support with `/help`",
            colour=Colour.RED
        )
    else:
        embed = make_embed(
            description=f"Timer reset for {role.mention}",
            colour=Colour.GREEN
        )
    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


@client.tree.command(name='check', description='Check if the bot has the required permissions')
async def _check(
        interaction: discord.Interaction
) -> None:
    me = interaction.guild.me
    highest_role: Optional[discord.Role] = None

    # TODO: Check if sorted in the right order
    if me.top_role.permissions.manage_roles:
        highest_role = me.top_role
    else:
        for role in me.roles:
            if role.permissions.manage_roles:
                highest_role = role
                break

    if not highest_role:
        await interaction.response.send_message(
            embed=make_embed(
                description="I don't have any role that has the `manage roles` permission",
                colour=Colour.RED
            ),
            ephemeral=True
        )
        return

    # TODO: Again check if it's sorted in the right order
    editable_roles = []
    for role in interaction.guild.roles:
        if role < highest_role:
            editable_roles.append(role)
        else:
            break

    if not editable_roles:
        embed = make_embed(
            description=f"There are no roles lower than {highest_role.mention}\n"
                        "You can fix this by giving me a higher role with the `manage roles` permission",
            colour=Colour.RED
        )
    elif highest_role != me.top_role:
        embed = make_embed(
            description=f"I can put timers on `{len(editable_roles)}` role{'' if len(editable_roles) == 1 else 's'}.\n"
                        f"You can increase the amount of roles by my top role {me.top_role.mention} the `manage "
                        f"roles` permission.",
            colour=Colour.GREEN,
            fields=[
                {
                    "name": "Roles",
                    "value": " ".join([role.mention for role in editable_roles])
                }
            ]
        )
    else:
        embed = make_embed(
            description=f"I can put timers on `{len(editable_roles)}` role{'' if len(editable_roles) == 1 else 's'}.",
            colour=Colour.GREEN,
            fields=[
                {
                    "name": "Roles",
                    "value": " ".join([role.mention for role in editable_roles])
                }
            ]
        )
    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


@client.tree.command(name='list', description='List all pingable roles')
async def _list_roles(
        interaction: discord.Interaction
) -> None:
    data = roleTracker.get_roles(interaction.guild_id)
    roles: Dict[discord.Role, list[int]] = {}

    for role_id, role_values in data.items():
        role = interaction.guild.get_role(role_id)

        if not role:
            roleTracker.remove_role(interaction.guild_id, role_id)
        else:
            roles[role] = role_values

    if not roles:
        await interaction.response.send_message(
            embed=make_embed(
                description="No timers set up yet!"
            ),
            ephemeral=True
        )
        return

    role_names = ""
    ping_interval = ""
    next_ping = ""

    for role, values in roles.items():
        role_names += role.mention + '\n',
        ping_interval += get_ping_interval(values[0]),
        next_ping += get_next_ping(values[1]) + '\n'

    embed = make_embed(
        "Ping Menu",
        fields=[
            {
                "name": "Role Name",
                "value": role_names
            },
            {
                "name": "Ping Interval",
                "value": ping_interval
            },
            {
                "name": "Next Ping",
                "value": next_ping
            }
        ]
    )
    await interaction.response.send_message(
        embed=embed,
        ephemeral=False
    )


@client.tree.command(name="info", description="Shows the bots info")
async def _info(
        interaction: discord.Interaction
) -> None:
    embed = make_embed(
        "Info Menu",
        "Prevent users from spamming role pings!",
        fields=[
            {
                "name": "Features",
                "value": "Set timers on roles so that they can only be pinged every so often.\n\n"
                         "Timers can be anywhere from 1 minute to 200 days\n\n"
                         "Open source project! Head over to the [Github Page](https://github.com/Topvennie/PingTimer) "
                         "to contribute!",
            },
            {
                "name": "Support",
                "value": "Quick Troubleshooting:\n\n"
                         "Make sure you have the `manage roles` permission.\n\n"
                         "Check if the bot is allowed to make slash commands and has the `manage roles permission`.\n\n"
                         "Nothing working? Join the [support discord server](https://discord.gg/VNUG8xFZ2k) for more "
                         "help!"
            },
            {
                "name": "Upcoming Features",
                "value": "Dashboard\n\n"
                         "Prevent new users from pinging a role.\n\n"
                         "Role requirements to ping certain roles.",
            }
        ]
    )
    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


@client.tree.command(name="help", description="Shows the help menu")
async def _help(
        interaction: discord.Interaction
) -> None:
    embed = make_embed(
        "Help Menu",
        "▫ `/add [Role] [Amount] [Time Interval]` - Sets a timer on a given role.\n"
        "▫ `/remove [Role]` - Removes the timer on a given role.\n"
        "▫ `/reset [Role]` - Resets the timer on a given role.\n"
        "▫ `/check` - Checks the permissions.\n"
        "▫ `/list` - Gives a list of all the roles and their cooldowns.\n"
        "▫ `/info` - Shows the info menu."
        "▫ `/help` - Shows this menu.\n",
        fields=[
            {
                "name": "Quick Troubleshooting",
                "value": "Run the `/check` command."
                         "Make sure you have the `manage roles` permission.\n\n"
                         "Check if the bot is allowed to make slash commands and has the `manage roles permission`.\n\n"
                         "Nothing working? Join the [support discord server](https://discord.gg/VNUG8xFZ2k) for more "
                         "help!"
            },
            {
                "name": "Hide / commands",
                "value": "Normal members can only use the `/list` command\n\n"
                         "Restrict the other commands to roles with the `manage roles permission` for a better "
                         "experience for your users by going to: \n\n"
                         "`Server Settings` -> `Integrations` -> `PingTimer`"
            }
        ]
    )
    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )
