from discord.ext import commands
from .config import BotConfig
import discord


class GameContext(commands.Context):
    def __init__(self, *args, **kwargs):
        super(GameContext, self).__init__(*args, **kwargs)
        self._config = None

    @property
    def config(self) -> BotConfig:
        if self._config is None:
            self._config = BotConfig.from_context(self)
        return self._config

    @property
    def player_role(self) -> discord.Role:
        return self.config.player_role

    @property
    def gm_role(self) -> discord.Role:
        return self.config.gm_role

    @property
    def temp_channel(self) -> discord.TextChannel:
        return self.config.temp_channel

    @property
    def announce(self) -> discord.TextChannel:
        return self.config.announce

    @property
    def reactions(self) -> 'ReactionManager':
        return self.config.reactions_cog

    @property
    def admin(self) -> 'BotManagement':
        return self.config.admin_cog


class GameBot(commands.Bot):
    async def get_context(self, message, *, cls=GameContext):
        return await super().get_context(message, cls=cls)

    def version(self):
        from . import VERSION

        versions = dict({'CORE': VERSION})

        for ext_name, extention in self.extensions.items():
            if 'VERSION' in dir(extention):
                print(extention.VERSION)
                versions[ext_name] = extention.VERSION

        return versions

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


def bot_factory() -> GameBot:
    bot = GameBot(
        command_prefix='.',
        intents=BotConfig.intents,
        description='Le bot qui aide pour organiser des soirées jeux !',
        help_command=HelpCommand(),
    )

    # Ajouts des Cog
    bot.load_extension('EventBot.ext.EventManager')

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
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("Oups ! Je n'ai pas trouvé cet utilisateur...")
        elif isinstance(error, commands.CommandNotFound):
            await ctx.send("Oups ! La commande `{}` n'existe pas...".format(ctx.command))
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("Ah non, désolé, je n'ai pas trop envie de t'écouter aujourd'hui...\nLaisse faire les maitres du jeu !")
        else:
            print("ERROR:")
            print(error)
            import traceback
            traceback.print_exception(type(error), error, error.__traceback__)

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

    @bot.command(
        brief='Recharge et met à jour le bot',
        description='Get random number between 0 and <max>.',
    )
    async def upgrade(crt: commands.Context) -> None:
        """
        Upgrade bot
        :param crt: Context
        :return:
        """
        try:
            from pip import main
            main(['install', '--upgrade', 'git+https://github.com/bontiv/event-discord-bot.git#egg=DiscordEventBot'])
        except ImportError:
            pass

        for extension in list(bot.extensions.keys()):
            bot.reload_extension(extension)

    @bot.command(
        name='version',
        brief='Affiche la version'
    )
    async def version_cmd(ctx: commands.Context):
        await ctx.send("```\n" + tabulate.tabulate(ctx.bot.version().items(), headers=['Component', 'Version']) + "```")

    return bot
