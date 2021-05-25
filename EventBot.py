# -*- coding: utf-8 -*-

import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio
import typing


class BotConfig:
    """
    Bot configuration
    """

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        """
        Channel for speak, deleted after event
        """
        self.temp_channel_id: int = 843815636257603607

        """
        Main guild ID
        """
        self.guild_id: int = 702217269320614028

        """
        Role ID for players
        """
        self.role_id: int = 843798156914851851

        """
        Role ID for games master
        """
        self.gm_role_id: int = 844127068479422514

        """
        Chanel for announcements of events
        """
        self.announce_id: int = 843822059205034035

        """
        Header for next event brief announcement
        """
        self.heading_id: int = 843812338239012884

        """
        Voice channel where players is put after the end of game
        """
        self.general_voice_id: int = 702217269320614032

        """
        Voices channels (first géneral, them games channels)
        """
        self.voices_chans_ids: typing.Sequence[int] = [843816962760245278, 843816720635527178, 843816832607060028]

    """
    Base permissions
    """
    permissions: typing.ClassVar[discord.Permissions] = discord.Permissions(
        read_messages=True,
        add_reactions=True,
        manage_roles=True,
        manage_messages=True,
        move_members=True
    )

    """
    Bot intents
    """
    intents: typing.ClassVar[discord.Intents] = discord.Intents(
        members=True,
        reactions=True,
        messages=True,
        guilds=True,
        voice_states=True
    )

    """
    Bot client ID
    """
    client_id: typing.ClassVar[str]

    """
    Configuration cache
    """
    _config_cache: typing.ClassVar[typing.Dict[int, 'BotConfig']] = {}

    @property
    def temp_channel(self) -> discord.TextChannel:
        """
        Channel use for text discussions inside the event
        :return: TextChannel
        """
        return self.bot.get_channel(self.temp_channel_id)

    @property
    def guild(self) -> discord.Guild:
        """
        The guild
        :return:
        """
        return self.bot.get_guild(self.guild_id)

    @property
    def player_role(self) -> discord.Role:
        """
        Dialog Role for event players
        :return:
        """
        return self.guild.get_role(self.role_id)

    @property
    def gm_role(self) -> discord.Role:
        """
        Dialog Role for Game Masters
        :return:
        """
        return self.guild.get_role(self.gm_role_id)

    @property
    def announce(self) -> discord.TextChannel:
        """
        Channel use for event announcements
        :return:
        """
        return self.bot.get_channel(self.announce_id)

    @property
    def heading(self) -> discord.VoiceChannel:
        """
        Fake voice channel, use for display event as guild title
        :return:
        """
        return self.bot.get_channel(self.heading_id)

    def general_voice(self) -> discord.VoiceChannel:
        """
        Channel where users are put after event closing
        :return:
        """
        return self.bot.get_channel(self.general_voice_id)

    @property
    def voices_channels(self) -> typing.Iterable[discord.VoiceChannel]:
        """
        Iterable of voices channels for event.
        0 - General discussions
        1 - Game 1
        2 - Game 2
        :return:
        """
        return map(lambda channel_id: self.bot.get_channel(channel_id), self.voices_chans_ids)

    def voice_channel(self, index) -> discord.VoiceChannel:
        """
        Get a an event voice channel (using index)
        :param index: 0 - general, 1 - game 1, 2 - game 2
        :return:
        """
        return self.bot.get_channel(self.voices_chans_ids[index])

    @property
    def reactions_cog(self) -> 'ReactionManager':
        """
        Cog for reaction and opening / close game board
        :return:
        """
        return self.bot.get_cog('reactions')

    @property
    def admin_cog(self) -> 'BotManagement':
        """
        Cog for scheduled tasks and bot administration
        :return:
        """
        return self.bot.get_cog('admin')

    @classmethod
    def from_context(cls, ctx: commands.Context) -> 'BotConfig':
        """
        Get the configuration from context
        :param ctx: Context to parse
        :return:
        """
        return cls.from_guild_id(ctx.bot, ctx.guild.id)

    @classmethod
    def from_guild_id(cls, bot: commands.Bot, guild_id: int):
        """
        Get the configuration from Bot agent and guild ID
        :param bot: Got agent
        :param guild_id: Guild ID to fetch
        :return:
        """
        if guild_id not in cls._config_cache:
            cls._config_cache[guild_id] = BotConfig(bot)
        return cls._config_cache[guild_id]

    @classmethod
    def load_file(cls, file: str) -> str:
        """
        Load cache from configuration file
        :param file: filename to load
        :return: The client secret for this Bot
        """
        from configparser import ConfigParser
        config = ConfigParser()
        config.read(file, encoding='utf-8-sig')

        for section in config.sections():
            # todo: load guild configuration
            pass

        cls.client_id = config['DEFAULT']['client']
        return config['DEFAULT']['secret']

    @classmethod
    def save_file(cls, file: str):
        """
        Save configuration in a file
        :param file: File to write
        :return:
        """
        from configparser import ConfigParser
        config = ConfigParser()
        config['DEFAULT'] = {
            'client': cls.client_id,
        }

        for guild_id in cls._config_cache:
            gconf: BotConfig = cls._config_cache[guild_id]
            config[str(guild_id)] = {
                'temp-channel': str(gconf.temp_channel_id),
                'guild': str(gconf.guild_id),
                'player_role': str(gconf.role_id),
                'gm_role': str(gconf.gm_role_id),
                'announce-channel': str(gconf.announce_id),
                'heading-channel': str(gconf.heading_id),
                'general-voice': str(gconf.general_voice_id),
                'voice-channels': ",".join(map(str, gconf.voices_chans_ids))
            }

        with open(file, 'w', encoding='utf-8-sig') as fp:
            config.write(fp)


async def reset_game(ctx: commands.Context) -> None:
    """
    Reset get board
    :param ctx: a Discord Context
    :return:
    """
    config = BotConfig.from_context(ctx)
    print("Reset channel {}".format(config.temp_channel.name))
    await config.temp_channel.delete_messages(await config.temp_channel.history().flatten())
    await config.temp_channel.send("Ce salon est automatiquement effacé à la fin de la journée. Il sert à partager les liens des tables.\nBon jeu !")

    tasks = []

    for vocal in config.voices_channels:
        for member in vocal.members:
            print("Disconnect {}".format(member))
            tasks.append(member.move_to(None))

    for member in config.player_role.members:
        print("Remove {} from {}".format(config.player_role, member))
        tasks.append(member.remove_roles(config.player_role))

    if config.reactions_cog is not None and config.reactions_cog.message is not None:
        tasks.append(config.reactions_cog.message.delete())
        tasks.append(config.reactions_cog.set_message(None))

    await asyncio.gather(*tasks)


class HelpCommand(commands.DefaultHelpCommand):
    """
    Help command
    """
    def __init__(self):
        super(HelpCommand, self).__init__(
            no_category='Autres commandes',
            commands_heading='Commandes :',
            brief='Affiche cet aide',
        )

    def get_ending_note(self) -> str:
        """
        Get str for the help ending
        :return:
        """
        return "Utilisez .help commande pour plus d'information sur une commande.\nVous pouvez aussi utiliser .help catégorie pour plus d'informations sur une catégorie."


class EventMessage:
    """
    Class for parsing a announce and get an event
    """
    def __init__(self, message: discord.Message = None):
        """
        Parse a message and get event data
        :param message: A discord message to parse as an event
        """
        import re

        self.id = None
        self.date = None
        self.name = "Soirée jeux"
        self.games_masters = []
        self.players = None
        self.message = message

        if message is not None:
            self.id = message.id
            date_element = re.search(r'([0-9]{2})/([0-9]{2}) à ([0-9]{2}) h ([0-9]{2})', message.content)
            name_parse = re.search(r'\*\*(.*)\*\*', message.content)
            if name_parse is not None:
                self.name = name_parse.group(1)
            if date_element is not None:
                now = datetime.now()
                day = int(date_element.group(1))
                month = int(date_element.group(2))
                hour = int(date_element.group(3))
                minutes = int(date_element.group(4))
                year = now.year + 1 if now.month > month else now.year
                self.date = datetime(year=year, month=month, day=day, hour=hour, minute=minutes)

            self.games_masters = re.findall('<@([^>]*)>', message.content)


async def get_announces(ctx: commands.Context) -> typing.Sequence[EventMessage]:
    """
    Get all currents events
    :param ctx: Command context
    :return: List of Event Message
    """
    conf = BotConfig.from_context(ctx)
    events = []

    async for message in conf.announce.history():
        event = EventMessage(message)
        if event.date is not None:
            events.append(event)
    return events


async def get_next_announce(ctx: commands.Context) -> EventMessage:
    """
    Get next event (by date)
    :param ctx: Command context
    :return: The Event Message
    """
    first_event = None
    conf = BotConfig.from_context(ctx)

    async for message in conf.announce.history():
        event = EventMessage(message)
        if event.date is None:
            continue
        if first_event is None or event.date < first_event.date:
            first_event = event

    return first_event


class DateNotAvailable(BaseException):
    """
    Exception when a date is not available for scheduling
    """
    def __init__(self, date, event):
        self.date = date
        self.event = event


class GameMasterHelper(commands.Cog, name='Maitre du jeu'):
    """
    Game Master commands
    """

    @commands.command(
        brief='Lance un dé pour tous les joueurs'
    )
    async def diceall(self, ctx, max_value: int = 100) -> None:
        """
        Throw dice, get random numbers for all payers
        :param ctx: Context
        :param max_value: Max dice value
        :return:
        """
        if max_value < 0:
            await ctx.send("Heu non, on ne peut pas lancer un dé de {}".format(max_value))
            return

        conf = BotConfig.from_context(ctx)

        import random
        await ctx.send(
            "\n".join(["{} lance les dés et fait {} !".format(user.display_name, random.randint(1, max_value))
                       for user in conf.player_role.members])
        )

    @commands.command(
        brief='Expulse un joueur de la soirée'
    )
    async def kick(self, ctx, user: discord.Member) -> None:
        """
        Kick a player
        :param ctx: Context
        :param user: Player to kick
        :return:
        """
        conf = BotConfig.from_context(ctx)
        conf.reactions_cog.ban_member(user.id)

        await asyncio.gather(
            user.remove_roles(conf.player_role),
            user.move_to(None)
        )

    @commands.command(
        name='random',
        brief='Fait deux équipes avec les joueurs',
        description='Take all players and put them into two teams. The blue and the red team.'
    )
    async def random_cmd(self, crx: commands.Context) -> None:
        """
        Display all players in two teams
        :param crx: Context
        :return:
        """
        conf = BotConfig.from_context(crx)
        names = []

        if len(conf.player_role.members) == 0:
            await crx.send("Oups ! Pas assez de monde pour faire des équipes...")
            return

        for member in conf.player_role.members:
            names.append(member.display_name)

        import random
        random.shuffle(names)

        middle = int(len(names) / 2)
        await crx.send("**Team Rouge**\n```\n  - {}\n```\n\n**Team Bleu**\n```\n  - {}\n```".format(
            "\n  - ".join(names[:middle]),
            "\n  - ".join(names[middle:])
        ))

    @commands.command(
        brief='Réparti les joueurs dans les deux salons vocaux'
    )
    async def randomteam(self, ctx: commands.Context) -> None:
        """
        Put player into two voices channels
        :param ctx: Context
        :return:
        """
        conf = BotConfig.from_context(ctx)
        general_voice = ctx.guild.get_channel(conf.voice_channel(0))
        players = []
        tasks = []

        if len(general_voice.members) == 0:
            await ctx.send("Oups ! Pas assez de monde pour faire des équipes...")
            return

        for member in general_voice.members:
            players.append(member)

        import random
        random.shuffle(players)

        middle = int(len(players) / 2)
        chan1 = ctx.guild.get_channel(conf.voice_channel(1))
        chan2 = ctx.guild.get_channel(conf.voice_channel(2))

        for player in players[middle:]:
            tasks.append(player.move_to(chan1))

        for player in players[:middle]:
            tasks.append(player.move_to(chan2))

        await asyncio.gather(*tasks)

    @commands.command(
        brief='Défini les noms des salons vocaux de jeu'
    )
    async def game(self, ctx: commands.Context, chanid: int, name: str = None) -> None:
        """
        Change voice channel names
        :param ctx: Context
        :param chanid: Channel to change (1 or 2)
        :param name: Name of the game
        :return:
        """
        conf = BotConfig.from_context(ctx)
        if not 0 < chanid < len(conf.voices_chans_ids):
            raise ValueError("chanid must be between 1 and {}".format(len(conf.voices_chans_ids)))

        icons = "🔴🔵"
        new_name = "{}Jeu {}".format(
            icons[chanid % len(icons)],
            chanid
        )

        if name is not None:
            new_name += " : " + name

        channel = conf.voice_channel(chanid)
        if channel.name == new_name:
            return

        await channel.edit(name=new_name)

    @commands.command(
        brief='Ajoute un autre maitre du jeu'
    )
    async def gm(self, ctx, user: discord.Member) -> None:
        """
        Add Game Master role to Player
        :param ctx: Context
        :param user: User
        :return:
        """
        conf = BotConfig.from_context(ctx)
        await user.add_roles(conf.gm_role)

    async def cog_check(self, ctx: commands.Context) -> bool:
        """
        Check if author is game master or bot administrator
        :param ctx: Discord Context
        :return:
        """
        try:
            if ctx.guild is None:
                return False
            if ctx.author.id == 364004307550601218:
                return True

            conf = BotConfig.from_context(ctx)

            check = commands.check_any(commands.has_role(conf.gm_role))
            await check.predicate(ctx)
            return True
        except (commands.CheckFailure, commands.CheckAnyFailure):
            return False


class EventManagement(commands.Cog, name='Plannification'):
    """
    Event planner
    """

    @commands.command(
        brief="Liste les soirées",
        description='Liste toutes les soirées à venir, géré par moi.',
    )
    async def list(self, ctx: commands.Context) -> None:
        """
        Send back to user the list of events
        :param ctx: Context
        :return:
        """
        import tabulate
        all_events = []
        conf = BotConfig.from_context(ctx)

        async for message in conf.announce.history():
            event = EventMessage(message)
            all_events.append([
                event.id,
                event.date.strftime("%d/%m - %H:%M") if event.date is not None else "-",
                event.name
            ])

        await ctx.send("Liste des événements :\n```\n" + tabulate.tabulate(
            all_events,
            headers=['ID', 'Date', 'Nom']
        ) + "\n```\n")

    @commands.command(
        brief='Planifie une soirée',
        description="Planifie une soirée prochainement.\nLe format est JJ/MM pour la date et HH:MM pour l'heure."
    )
    async def add(self, ctx: commands.Context, date, time, name="Soirée jeux") -> None:
        """
        Add an event
        :param ctx: Context
        :param date: Date of event
        :param time: Time of event
        :param name: The name of the event
        :return:
        """
        try:
            dt_value = datetime.strptime("{} {}".format(date, time), "%d/%m %H:%M")
            conf = BotConfig.from_context(ctx)

            begin = dt_value - timedelta(hours=4)
            end = dt_value + timedelta(hours=4)

            async for announce in conf.announce.history():
                event = EventMessage(announce)
                if event.date is None:
                    continue
                print(event.date)
                if begin < event.date < end:
                    raise DateNotAvailable(dt_value, event)

            await ctx.send("Ajout d'un event le {}: {}".format(dt_value, name))
            await conf.announce.send(
                """
                **{name}**
                Événement prévu le {date} !
                Maitre du jeu : <@{gm}>
                Cliquez sur ✅ pour participer.
                """.format(
                    name=name,
                    gm=ctx.author.id,
                    date=dt_value.strftime("%d/%m à %H h %M")
                ))

        except DateNotAvailable as e:
            await ctx.send("Oups ! On ne peux pas réserver à 4h d'une réservation existante. Il y a une résa le {}.".format(
                e.event.date.strftime("%d/%m à %H h %M")
            ))

        except ValueError:
            await ctx.send("Le format de la date n'est pas respectée.")
            return

    @add.error
    async def add_error(ctx, error) -> None:
        """
        Error handler for add command
        :param error: Raised error
        :return:
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Oups ! Il manque {}. Vérifiez avec la commande est .add <date> <heure> <nom>.\ndate en JJ/MM/YY et heure en HH:MM".format(error.param))
        if isinstance(error, DateNotAvailable):
            await ctx.send("Désolé, je ne peux pas réserver le {}, un événement est déjà prévu le {}.".format(
                error.date.strftime("%d/%m à %H h %M"),
                error.event.date.strftime("%d/%m à %H h %M")
            ))
        else:
            raise error

    @commands.command(
        name='delete',
        brief='Supprime un evenement',
        description='Supprime l\'événement avec l\'ID donné. Voir .list pour les ID des événements.'
    )
    async def delete_cmd(self, ctx, event: int) -> None:
        """
        Delete an event (bot command)
        :param ctx: Context
        :param event: The event ID
        :return:
        """
        try:
            await self.delete(ctx, event)
            conf = BotConfig.from_context(ctx)
            (event, tasks) = await conf.admin_cog.update(ctx)
            await asyncio.gather(*tasks)

        except discord.NotFound:
            await ctx.send("L'ID de l'événement est invalide. Aucun événement trouvé...")
        except commands.CheckFailure:
            await ctx.send("Oups ! Tu n'as pas le droit de faire ça.")

    @staticmethod
    async def delete(ctx: commands.Context, event_id: int) -> None:
        """
        Delete an event (internal function)
        :param ctx: Context
        :param event_id: The event ID
        :return:
        """
        conf = BotConfig.from_context(ctx)
        message = await conf.announce.fetch_message(event_id)
        event = EventMessage(message)
        if event.date is None:
            print("DELETE: Event sans date")
            raise commands.CheckFailure(message="Event without date.")

        if not ctx.author.guild_permissions.administrator and ctx.author.id not in event.games_masters:
            print("DELETE: Cannot delete.")
            print(event.games_masters)
            print(ctx.author.id)
            raise commands.CheckFailure(message="Forbidden")

        await message.delete()

    async def cog_check(self, ctx: commands.Context):
        """
        Cog only available in guild context
        :param ctx: Context
        :return:
        """
        return ctx.guild is not None


class BotManagement(commands.Cog, description='Gestion du bot (commande admins)', name='admin'):
    """
    Bot management (administration)
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name='open',
        brief='Ouvre la zone de jeu',
        description='Ouvre immédiatement la zone de jeu avec les inscriptions sur le message cité',
    )
    async def open_cmd(self, ctx: commands.Context, message: int) -> None:
        """
        Open the game board
        :param ctx: Context
        :param message: The event ID
        :return:
        """
        conf = BotConfig.from_context(ctx)
        message_discord = await conf.announce.fetch_message(message)

        await conf.reactions_cog.set_message(message_discord)

    @commands.command(
        name='announce',
        brief='Annonce la prochaine soirée',
        description='Annonce directement la prochaine soirée jeu',
    )
    async def announce_cmd(self, ctx: commands.Context, date, time) -> None:
        """
        Add an announce for event.
        May be deprecated in future version. Use the add command instead.
        :param ctx: Context
        :param date: Date of event
        :param time: Time of event
        :return:
        """
        conf = BotConfig.from_context(ctx)
        dt_value = datetime.strptime("{} {}".format(date, time), "%d/%m/%y %H:%M")
        message = await self.announce(conf, dt_value, ctx.author)

        await asyncio.gather(
            message.add_reaction("✅"),
            conf.heading.edit(name=dt_value.strftime("📅Soirée %d/%m à %H:%M")),
            conf.reactions_cog.set_message(message),
            ctx.author.add_roles(conf.gm_role)
        )

    @staticmethod
    async def announce(config: BotConfig, date: datetime, gm: discord.Member) -> discord.Message:
        """
        Add an announce.
        May be deprecated in future version. Use the add command.
        :param config: Bot configuration
        :param date: date of announce
        :param gm: Game Master of event
        :return:
        """
        return await config.announce.send("Prochaine soirée jeux : le {} à {} !\nMaitres du jeu: <@{}>\nCliquez sur ✅ pour participer.".format(
            date.strftime("%d/%m"),
            date.strftime("%H h %M"),
            gm.id
        ))

    @commands.command(
        name='update',
        brief='Prend le prochain event et défini les rôles / header des channels'
    )
    async def update_cmd(self, ctx) -> None:
        """
        Force manual update of next event (reaction monitoring and heading channel)
        :param ctx: Context
        :return:
        """
        (event, tasks) = await self.update(ctx)
        if event is None:
            tasks.append(ctx.send("Pas de soirée à venir"))
        else:
            tasks.append(ctx.send("Prochaine soirée le {}.".format(event.date.strftime("%d/%m à %H:%M"))))

        await asyncio.gather(*tasks)

    @staticmethod
    async def update(ctx: commands.Context) -> typing.Tuple[EventMessage, typing.List[typing.Coroutine]]:
        """
        Update and monitor the next event.
        :param ctx: Context
        :return:
        """
        conf = BotConfig.from_context(ctx)
        next_event = await get_next_announce(ctx)
        tasks = []
        print("Current Name: {}".format(conf.heading.name))
        tasks.append(conf.reactions_cog.set_message(next_event.message))

        if next_event is None:
            tasks.append(conf.heading.edit(name="Pas de soirée à venir"))
        else:
            tasks.append(conf.heading.edit(name=next_event.date.strftime("📅Soirée %d/%m à %H:%M")))

        return next_event, tasks

    async def cog_check(self, ctx: commands.Context) -> bool:
        """
        Check if author is bot administrator
        :param ctx: Context
        :return:
        """
        if ctx.guild is None:
            return False
        if ctx.author.id == 364004307550601218:
            return True
        try:
            commands.has_guild_permissions(administrator=True).predicate(ctx)
            return True
        except (commands.CheckFailure, commands.CheckAnyFailure):
            return False


class ReactionManager(commands.Cog, name='reactions'):
    def __init__(self, bot: commands.Bot):
        super(ReactionManager, self).__init__()
        self.message = None
        self.banlist = []
        self.bot = bot

    def ban_member(self, user_id: int) -> None:
        """
        Add a user in event ban list
        :param user_id:
        :return:
        """
        self.banlist.append(user_id)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        """
        A reaction is added in a message
        :param payload: The reaction raw payload
        :return:
        """
        if self.message is None or payload.message_id != self.message.id or payload.guild_id is None or payload.user_id == self.bot.user.id:
            return

        if payload.emoji.name != "✅":
            print("Not THE emoji")
            channel = self.bot.get_channel(payload.channel_id)  # type: discord.TextChannel
            if channel.guild is not None:
                message = await channel.fetch_message(payload.message_id)
                await message.remove_reaction(payload.emoji, payload.member)
                return

        if payload.member.id in self.banlist:
            await payload.member.send("Désolé, mais vous ne pouvez plus participez à cet événemet.")
            return

        print("All is OK")
        conf = BotConfig.from_guild_id(self.bot, payload.guild_id)
        await payload.member.add_roles(conf.player_role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        """
        A reaction is removed for a message
        :param payload: The raw Payload
        :return:
        """
        if self.message is None or payload.message_id != self.message.id or payload.guild_id is None:
            return

        if payload.emoji.name != "✅":
            print("Not THE emoji WHAT ?!")
            return

        print("All is OK")
        conf = BotConfig.from_guild_id(self.bot, payload.guild_id)
        member = conf.guild.get_member(payload.user_id)
        await member.remove_roles(conf.player_role)

    async def set_message(self, message: typing.Optional[discord.Message]) -> None:
        """
        Set the message to monitor
        :param message: Discord message
        :return:
        """
        self.message = message
        self.banlist.clear()
        conf = BotConfig.from_guild_id(self.bot, message.guild.id)

        tasks = []
        players = []

        if self.message is not None:
            tasks.append(message.add_reaction("✅"))

            for reaction in self.message.reactions:
                if reaction.emoji == "✅":
                    async for user in reaction.users():
                        if user.id != self.bot.user.id:
                            tasks.append(user.add_roles(conf.player_role))
                            players.append(user.id)
                else:
                    async for user in reaction.users():
                        tasks.append(self.message.remove_reaction(reaction.emoji, user))

        for player in conf.player_role.members:
            if player.id not in players:
                tasks.append(player.remove_roles(conf.player_role))

        await asyncio.gather(*tasks)


def bot_factory() -> commands.Bot:
    bot = commands.Bot(
        command_prefix='.',
        intents=BotConfig.intents,
        description='Le bot qui aide pour organiser des soirées jeux !',
        help_command=HelpCommand(),
    )

    # Ajouts des Cog
    bot.add_cog(EventManagement(bot))
    bot.add_cog(BotManagement(bot))
    bot.add_cog(ReactionManager(bot))
    bot.add_cog(GameMasterHelper(bot))

    @bot.listen()
    async def on_message(message: discord.Message) -> None:
        """
        Self response.
        May be replaced by a decorator in future version
        :param message: Message received
        :return:
        """
        if message.guild is not None or message.content.startswith(bot.command_prefix):
            return

        print("Message {0.author} ({0.guild}): {0.content}".format(message))
        if message.author.id == bot.user.id:
            return

        if message.guild is not None:
            return

        if message.author.id == 314464396262768651:  # Nephenie
            await message.reply("Je ne suis qu'un bot. Par contre pour info, Rémi t'aime ;)")
        elif message.author.id == 364004307550601218:
            await message.reply("Yey patron !")
        else:
            await message.reply("Hey ! Je suis qu'un bot, je ne vais tout de même pas te répondre.")

        await message.reply("Tu es perdu ? .help !")

    @bot.listen()
    async def on_command_error(ctx, error: Exception) -> None:
        """
        Base actions and message on common errors
        :param ctx: Context
        :param error: The error
        :return:
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Oups ! Il manque {} dans la commande. Vérifiez avec `.help {}` !".format(
                error.param,
                ctx.command
            ))
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("Oups ! Permission refusé pour {}...".format(ctx.command))
        elif isinstance(error, commands.CommandNotFound):
            await ctx.send("Oups ! La commande `{}` n'existe pas...".format(ctx.command))
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("Ah non, désolé, je n'ai pas trop envie de t'écouter aujourd'hui...\nLaisse faire les maitres du jeu !")
        else:
            print("ERROR:")
            print(error)
            import traceback
            traceback.print_exception(type(error), error, error.__traceback__)

    @bot.command()
    @commands.check_any(commands.has_guild_permissions(administrator=True), commands.has_role(844127068479422514))
    async def reset(ctx: commands.Context) -> None:
        """
        Command to close the game board.
        May be moved in the GameMaster Cog in future version.
        :param ctx: Context
        :return:
        """
        conf = BotConfig.from_context(ctx)
        if ctx.channel.id != conf.temp_channel_id:
            await ctx.send("Vous devez faire cette commande dans le salon #infos")
        else:
            await reset_game(ctx)

    @reset.error
    async def reset_error(ctx, error) -> None:
        """
        Error handler for reset command
        :param ctx: Context
        :param error: Raised error
        :return:
        """
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Oups ! Tu ne peux pas faire cette commande...")
        else:
            raise error

    @bot.command(
        brief='Lance un dé',
        description='Get random number between 0 and <max>.',
    )
    async def dice(crt: commands.Context, max_value: int = 100) -> None:
        """
        Throw a dice of max value (min is 0)
        :param crt: Context
        :param max: The max dice value
        :return:
        """
        if max_value <= 0:
            await crt.send("Heu non, on ne peut pas lancer un dé de {}".format(max_value))
        else:
            import random
            await crt.send("{} lance les dés et fait {} !".format(crt.author.display_name, random.randint(0, max_value)))

    return bot


def main_run():
    """
    Main class to execute the Bot
    :return:
    """
    from appdirs import AppDirs
    dirs = AppDirs(appname='EventDiscordBot', appauthor='Bontiv', roaming=True)
    bot = bot_factory()

    @bot.listen()
    async def on_ready() -> None:
        """
        Action when the bot is ready
        :return:
        """
        print("Ready please visit:")
        url = discord.utils.oauth_url(client_id=BotConfig.client_id, permissions=BotConfig.permissions)
        print(url)  # Print URL for connect the bot on a guild
        BotConfig.from_guild_id(bot, 702217269320614028)

    from os.path import exists, join
    from os import makedirs

    file = join(dirs.user_config_dir, "config.ini")
    makedirs(dirs.user_config_dir, exist_ok=True)
    if exists(file):
        bot.run(BotConfig.load_file(file))
    else:
        print("Configuration missing !")


if __name__ == '__main__':
    main_run()
