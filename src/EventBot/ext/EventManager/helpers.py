import datetime

from EventBot.config import BotConfig
from EventBot.objects import EventMessage
import asyncio
import typing
from discord.ext import commands


async def reset_game(config: BotConfig) -> None:
    """
    Reset get board
    :param config: a Bot Configuration
    :return:
    """
    print("Reset channel {}".format(config.temp_channel.name))

    after = datetime.datetime.now()
    after -= datetime.timedelta(days=13)

    await config.temp_channel.delete_messages(await config.temp_channel.history(after=after).flatten())

    async for message in config.temp_channel.history():
        await message.delete()
    await config.temp_channel.send("Ce salon est automatiquement effacé à la fin de la journée. Il sert à partager les liens des tables.\nBon jeu !")

    tasks = []

    for vocal in config.voices_channels:
        for member in vocal.members:
            print("Disconnect {}".format(member))
            tasks.append(member.move_to(None))

    for role in [config.player_role, config.gm_role]:
        for member in role.members:
            print("Remove {} from {}".format(role, member))
            tasks.append(member.remove_roles(role))

    if config.reactions_cog is not None and config.reactions_cog.message is not None:
        tasks.append(config.reactions_cog.message.delete())
        tasks.append(config.reactions_cog.set_message(None))

    await asyncio.gather(*tasks)


async def get_announces(ctx: commands.Context) -> typing.Sequence[EventMessage]:
    """
    Get all currents events
    :param ctx: Command context
    :return: List of Event Message
    """
    conf = BotConfig.from_context(ctx)
    events = []

    async for message in conf.announce.history():
        event = EventMessage(conf, message)
        if event.date is not None:
            events.append(event)
    return events
