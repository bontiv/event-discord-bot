from .helpers import reset_game
from EventBot.config import BotConfig
from EventBot.objects import EventMessage
from discord.ext import commands, tasks
from datetime import datetime
import asyncio, discord, typing


class BotManagementCog(commands.Cog, description='Gestion du bot (commande admins)', name='admin'):
    """
    Bot management (administration)
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.update_task.start()

    def cog_unload(self):
        self.update_task.cancel()

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
        conf = BotConfig.from_context(ctx)
        event, tasks = await self.update(conf)
        if event is None:
            tasks.append(ctx.send("Pas de soirée à venir"))
        elif event.is_open:
            tasks.append(ctx.send("Prochaine soirée le {}. L'événement est ouvert. Fermeture {}.".format(
                event.date.strftime("%d/%m à %H:%M"),
                event.close_date.strftime("%d/%m à %H:%M")
            )))
        else:
            tasks.append(ctx.send("Prochaine soirée le {}. L'événement n'est pas encore ouvert. Ouverture {}.".format(
                event.date.strftime("%d/%m à %H:%M"),
                event.open_date.strftime("%d/%m à %H:%M")
            )))

        await asyncio.gather(*tasks)

    @tasks.loop(minutes=10)
    async def update_task(self):
        """
        Task to automate open and close events
        :return:
        """
        tasks_all = []
        for conf in BotConfig.get_all():
            event, tasks = await self.update(conf)
            tasks_all += tasks
        await asyncio.gather(*tasks_all, return_exceptions=True)

    @update_task.before_loop
    async def before_update_task(self):
        """
        Wait for bot ready before start update loop
        :return:
        """
        await self.bot.wait_until_ready()

    @staticmethod
    async def update(conf: BotConfig) -> typing.Tuple[EventMessage, typing.List[typing.Coroutine]]:
        """
        Update and monitor the next event.
        :param ctx: Context
        :return:
        """
        next_event = await conf.get_next_announce()
        tasks = []
        heading = conf.heading.name

        if next_event is None:
            heading = "📅Pas de soirée à venir"
            tasks.append(conf.reactions_cog.set_message(None))

        elif next_event.can_close and next_event.is_open:
            print("Close event")
            tasks.append(reset_game(conf))

        elif next_event.can_open and not next_event.is_open:
            tasks.append(conf.reactions_cog.set_message(next_event.message))
            for gm in next_event.games_masters:
                member = conf.guild.get_member(gm)
                if member is None:
                    member = await conf.guild.fetch_member(gm)
                if member is not None:
                    tasks.append(member.add_roles(conf.gm_role))
            print("Open event")

        if next_event is not None:
            if next_event.date > datetime.now():
                diff_dates = next_event.date - datetime.now()
                if diff_dates.days == 0:
                    heading = next_event.date.strftime("📅Aujourd'hui à %H:%M")
                elif diff_dates.days == 1:
                    heading = next_event.date.strftime("📅Demain à %H:%M")
                else:
                    heading = next_event.date.strftime("📅Soirée %d/%m à %H:%M")
            else:
                heading = next_event.date.strftime("📅Événement en cours")

        if heading != conf.heading.name:
            print("Current Name: {}\nNext Name: {}".format(conf.heading.name, heading))
            tasks.append(conf.heading.edit(name=heading, reason="Bot update next event."))

        return next_event, tasks

    async def cog_check(self, ctx: commands.Context) -> bool:
        """
        Check if author is bot administrator
        :param ctx: Context
        :return:
        """
        if ctx.guild is None:
            return False
        return ctx.author.guild_permissions.administrator
