from .bot import bot_factory
from .config import BotConfig
import discord


def bot_run():
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
        print("Path: {}".format(file))


def config_run(cfg):
    from os.path import exists, join
    from os import makedirs
    from appdirs import AppDirs

    dirs = AppDirs(appname='EventDiscordBot', appauthor='Bontiv', roaming=True)

    file = join(dirs.user_config_dir, "config.ini")
    makedirs(dirs.user_config_dir, exist_ok=True)
    client_secret = None
    if exists(file):
        client_secret = BotConfig.load_file(file)

    if cfg.config == 'show':
        print("ClientID: {}".format(BotConfig.client_id))
        print("Secret: {}".format(client_secret))

    if cfg.config == 'set':
        import configparser
        config = configparser.ConfigParser()
        config.read(file)
        config['DEFAULT'][cfg.parameter] = cfg.value
        with open(file, 'w') as fp:
            config.write(fp)

def main_run():
    import argparse

    default_parameters = ['client', 'secret']

    args = argparse.ArgumentParser()
    commands = args.add_subparsers(title='Commands', dest='command')
    commands.add_parser('run')
    commands.add_parser('upgrade')
    commands.add_parser('version')
    config = commands.add_parser('config')
    sub_config = config.add_subparsers(title='configuration', dest='config')
    show_config = sub_config.add_parser('show')
    show_config.add_argument('-p', '--parameter', choices=default_parameters)
    set_config = sub_config.add_parser('set')
    set_config.add_argument('parameter', choices=default_parameters)
    set_config.add_argument('value')

    cfg = args.parse_args()
    if cfg.command == 'run':
        bot_run()

    if cfg.command == 'config':
        config_run(cfg)

    if cfg.command == 'version':
        import tabulate
        bot = bot_factory()
        print(tabulate.tabulate(bot.version().items(), headers=['Component', 'Version']))

    if cfg.command == 'upgrade':
        from pip import main
        main(['install', '--upgrade', 'git+https://github.com/bontiv/event-discord-bot.git#egg=DiscordEventBot'])

if __name__ == '__main__':
    main_run()
