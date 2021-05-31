from .bot import bot_factory
from .config import BotConfig
import discord


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
