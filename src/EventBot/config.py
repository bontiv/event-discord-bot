from discord.ext import commands
import discord
import typing
from .objects import EventMessage


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
        self.heading_id: int = 847163122657656892

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
    client_id: typing.ClassVar[str] = None

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

    async def get_next_announce(self):
        """
        Get next event (by date)
        :return: The Event Message
        """
        first_event = None

        async for message in self.announce.history():
            event = EventMessage(self, message)
            if event.date is None:
                continue
            if first_event is None or event.date < first_event.date:
                first_event = event

        return first_event

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
    def get_all(cls) -> typing.Iterable['BotConfig']:
        """
        Get all guild configs
        :return:
        """
        return cls._config_cache.values()

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
        return config['DEFAULT']['secret'] if 'secret' in config['DEFAULT'] else None

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

