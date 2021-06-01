from discord.ext import commands
from EventBot.config import BotConfig
from EventBot.objects import EventMessage
from datetime import datetime, timedelta
from .errors import DateNotAvailable
import discord
import asyncio

class EventManagementCog(commands.Cog, name='Plannification'):
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
            event = EventMessage(conf, message)
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
                event = EventMessage(conf, announce)
                if event.date is None:
                    continue
                print(event.date)
                if begin < event.date < end:
                    raise DateNotAvailable(dt_value, event)

            await ctx.send("Ajout d'un event le {}: {}".format(dt_value.strftime("%d/%m à %H h %M"), name))
            message = await conf.announce.send(
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
            await message.add_reaction("✅")

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
        event = EventMessage(conf, message)
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
