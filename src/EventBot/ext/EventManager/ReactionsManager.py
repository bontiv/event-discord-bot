from discord.ext import commands
from EventBot.config import BotConfig
import discord, asyncio, typing


class ReactionsCog(commands.Cog, name='reactions'):
    def __init__(self, bot: commands.Bot):
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

        tasks = []
        players = []

        if self.message is not None:
            conf = BotConfig.from_guild_id(self.bot, message.guild.id)
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
