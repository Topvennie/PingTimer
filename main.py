from typing import Optional

from discord import app_commands
from discord.ext import tasks

from common_functions import *
from roleTracker import RoleTracker

MY_GUILD = discord.Object(id=1098923651371368568)


###############
#             #
#   Classes   #
#             #
###############

# PingTimer client class
class PingTimer(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    # Sync commands and start tasks
    async def setup_hook(self) -> None:
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)
        self.expired_cooldown_role.start()
        self.cleanup.start()

    # Make role mentionable when cooldown expires
    @tasks.loop(seconds=60)
    async def expired_cooldown_role(self) -> None:
        data = roleTracker.get_expired_ping_cooldowns()
        for guild_id, role_id in data:
            guild = self.get_guild(guild_id)
            if not guild:
                await roleTracker.remove_guild(guild_id)
                continue

            role = guild.get_role(role_id)
            if role:
                try:
                    await role.edit(
                        mentionable=True,
                        reason=f"Timer expired"
                    )
                except discord.Forbidden:
                    continue
            else:
                await roleTracker.remove_role(guild_id, role_id)

    @expired_cooldown_role.before_loop
    async def before_expired_cooldown_role(self) -> None:
        await self.wait_until_ready()

    # Remove deleted guilds / roles
    @tasks.loop(hours=168)
    async def cleanup(self) -> None:
        data = await roleTracker.get_data()
        amount_of_guilds = 0
        amount_of_roles = 0
        for guild_id, roles in data.items():
            guild = client.get_guild(int(guild_id))
            if not guild:
                await roleTracker.remove_guild(int(guild_id))
                continue

            amount_of_guilds += 1
            for role_id, values in roles.items():
                role = guild.get_role(int(role_id))
                if not role:
                    await roleTracker.remove_role(int(guild_id), int(role_id))
                else:
                    amount_of_roles += 1
        print(f"Cleanup: Tracking {amount_of_roles} roles in {amount_of_guilds} guilds")
        print('-' * 10)

    @cleanup.before_loop
    async def before_cleanup(self) -> None:
        await self.wait_until_ready()


# Different intervals users can use
class Interval(enum.Enum):
    minutes = 60
    hours = 3600
    days = 86400


#################
#               #
#   Variables   #
#               #
#################

client = PingTimer()
roleTracker = RoleTracker()
time_intervals = [(interval.value, str(interval.name)) for interval in Interval]


##############
#            #
#   Events   #
#            #
##############

# Reset cooldowns that have expired and remove deleted guilds / roles
@client.event
async def on_ready():
    await client.wait_until_ready()
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    data = await roleTracker.get_data()
    unix = get_unix_time()
    amount_of_guilds = 0
    amount_of_roles = 0
    for guild_id, roles in data.items():
        guild = client.get_guild(int(guild_id))
        if not guild:
            await roleTracker.remove_guild(int(guild_id))
            continue

        amount_of_guilds += 1
        for role_id, values in roles.items():
            role = guild.get_role(int(role_id))
            if role:
                if int(values[1]) < unix:
                    try:
                        await role.edit(
                            mentionable=True,
                            reason=f"Timer expired"
                        )
                    except discord.Forbidden:
                        continue
                amount_of_roles += 1
            else:
                await roleTracker.remove_role(int(guild_id), int(role_id))
    print(f"Startup: Tracking {amount_of_roles} roles in {amount_of_guilds} guilds")
    print('-' * 10)


# Set timer on role when tracked role is mentioned
@client.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot:
        return

    for role in message.role_mentions:
        success = await roleTracker.get_role(message.guild.id, role.id)
        if success:
            try:
                await role.edit(
                    mentionable=False,
                    reason=f"{message.author.name}#{message.author.discriminator} pinged the role!"
                )
                await roleTracker.ping_role(message.guild.id, role.id)
            except discord.Forbidden:
                return


# Remove guild data when bot is kicked from guild
@client.event
async def on_guild_remove(guild: discord.Guild) -> None:
    await roleTracker.remove_guild(guild.id)


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
    await roleTracker.add_role(interaction.guild_id, role.id, seconds)

    embed = make_embed(
        description=f"{role.mention} can now be pinged every {time} {str(interval.name)}",
        colour=Colour.GREEN
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
    found = await roleTracker.remove_role(interaction.guild_id, role.id)

    if not found:
        embed = make_embed(
            description=f"No timer set up for {role.mention}.",
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
    found, timer = await roleTracker.reset_role(interaction.guild_id, role.id)

    if not found:
        embed = make_embed(
            description=f"No timer set up for {role.mention}.",
            colour=Colour.RED
        )
    elif not timer:
        embed = make_embed(
            description=f"{role.mention} is already mentionable"
        )
    else:
        try:
            await role.edit(
                mentionable=True,
                reason=f"{interaction.user.name}#{interaction.user.discriminator} reset the timer!"
            )
            embed = make_embed(
                description=f"Timer reset for {role.mention}",
                colour=Colour.GREEN
            )
        except discord.Forbidden:
            embed = make_embed(
                description="Unable to reset timer",
                colour=Colour.RED
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
        roles = ""
        for role in editable_roles:
            if len(roles) < 2000:
                if not role.is_default():
                    roles += f"{role.mention} "
            else:
                roles += "..."
                break
        embed = make_embed(
            description=f"I can put timers on `{len(editable_roles)}` role{'' if len(editable_roles) == 1 else 's'}.",
            colour=Colour.GREEN,
            fields=[
                {
                    "name": "Roles",
                    "value": roles
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
    data = await roleTracker.get_roles(interaction.guild_id)
    roles: Dict[discord.Role, list[int]] = {}

    for role_id, role_values in data.items():
        role = interaction.guild.get_role(role_id)

        if not role:
            await roleTracker.remove_role(interaction.guild_id, role_id)
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
        role_names += f"{role.mention}\n"
        ping_interval += get_ping_interval(values[0], time_intervals)
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
        "▫ `/info` - Shows the info menu.\n"
        "▫ `/help` - Shows this menu.\n",
        fields=[
            {
                "name": "Quick Troubleshooting",
                "value": "Run the `/check` command."
                         "Make sure you have the `manage roles` permission.\n\n"
                         "Check if the bot is allowed to make slash commands and has the `manage roles permission`.\n\n"
                         "Need more help? Join the [support discord server](https://discord.gg/VNUG8xFZ2k) for more "
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


if __name__ == "__main__":
    with open("token.txt", "r") as file:
        token = file.readline()

    client.run(token)
