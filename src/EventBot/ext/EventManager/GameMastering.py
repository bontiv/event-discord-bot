from discord.ext import commands, tasks
from EventBot.config import BotConfig
import discord
import asyncio
from .helpers import reset_game


class GameMasterCog(commands.Cog, name='Maitre du jeu'):
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
        max_dice = 0
        message = []
        win_player = None
        for user in conf.player_role.members:
            dice = random.randint(1, max_value)
            if dice > max_dice:
                max_dice = dice
                win_player = user
            message.append("{} lance les dés et fait {} !".format(user.display_name, dice))
        await ctx.send(
            "\n".join(message) + "\n\nLe gagnant est <@{}> avec son dé de {} !".format(win_player.id, max_dice)
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
    async def random_cmd(self, crx: commands.Context, put_vocal: bool = False) -> None:
        """
        Display all players in two teams
        :param crx: Context
        :param put_vocal: Put players in differents vocals channels
        :return:
        """
        conf = BotConfig.from_context(crx)
        players = []

        if len(conf.player_role.members) == 0:
            await crx.send("Oups ! Pas assez de monde pour faire des équipes...")
            return

        for member in conf.player_role.members:
            players.append(member)

        import random
        random.shuffle(players)

        middle = int(len(players) / 2)

        def get_name(user):
            return user.display_name

        await crx.send("**🔴 Team Rouge 🔴**\n```\n  - {}\n```\n\n**🔵 Team Bleu 🔵**\n```\n  - {}\n```".format(
            "\n  - ".join(map(get_name, players[:middle])),
            "\n  - ".join(map(get_name, players[middle:]))
        ))

        if put_vocal:
            chan1 = conf.voice_channel(1)
            chan2 = conf.voice_channel(2)

            for player in players[middle:]:
                tasks.append(player.move_to(chan1))

            for player in players[:middle]:
                tasks.append(player.move_to(chan2))

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

        await channel.edit(name=new_name, reason="Channel edited by Game Master {}.".format(ctx.author.display_name))

    @commands.group(
        brief='Gère les maitres du jeu'
    )
    async def gm(self, ctx) -> None:
        """
        Manage Games Masters
        :param ctx: Context
        :return:
        """
        pass

    @gm.command(
        name='add',
        brief='Ajoute un GM'
    )
    async def add_gm(self, ctx, user: discord.Member):
        """
        Add a Game Master
        :param ctx: Context
        :param user: User to add
        :return:
        """
        conf = BotConfig.from_context(ctx)
        await user.add_roles(conf.gm_role)

    @gm.command(
        name='remove',
        brief='Retire un GM'
    )
    async def remove_gm(self, ctx, user: discord.Member):
        """
        Remove a Game Master
        :param ctx: Context
        :param user: User to remove
        :return:
        """
        conf = BotConfig.from_context(ctx)
        await user.remove_roles(conf.gm_role)

    @commands.command(
        name='close',
        brief='Ferme la zone de jeu.'
    )
    async def close_cmd(self, ctx: commands.Context):
        conf = BotConfig.from_context(ctx)
        if ctx.channel.id != conf.temp_channel_id:
            await ctx.send("Vous devez faire cette commande dans le salon #infos")
        else:
            await reset_game(conf)

    async def cog_check(self, ctx: commands.Context) -> bool:
        """
        Check if author is game master or bot administrator
        :param ctx: Discord Context
        :return:
        """
        if ctx.guild is None:
            return False
        if ctx.author.id == 364004307550601218:
            return True

        conf = BotConfig.from_context(ctx)
        if conf.gm_role in ctx.author.roles:
            return True
        return False
