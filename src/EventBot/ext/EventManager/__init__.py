from .PlannerManager import EventManagementCog
from .ReactionsManager import ReactionsCog
from .GameMastering import GameMasterCog
from .BotAdministration import BotManagementCog
from discord.ext.commands import Bot

__requires__ = ['EventBot']


def setup(bot: Bot):
    """
    Insert cog in bot
    :param bot:
    :return:
    """
    bot.add_cog(EventManagementCog(bot))
    bot.add_cog(BotManagementCog(bot))
    bot.add_cog(ReactionsCog(bot))
    bot.add_cog(GameMasterCog(bot))


def teardown(bot: Bot):
    bot.remove_cog(EventManagementCog.__name__)
    bot.remove_cog(BotManagementCog.__name__)
    bot.remove_cog(ReactionsCog.__name__)
    bot.remove_cog(GameMasterCog.__name__)