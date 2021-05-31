import discord
from datetime import datetime, timedelta


class EventMessage:
    """
    Class for parsing a announce and get an event
    """

    def __init__(self, config: 'BotConfig', message: discord.Message = None):
        """
        Parse a message and get event data
        :param message: A discord message to parse as an event
        """
        import re

        self.date = None
        self.close_date = None
        self.open_date = None
        self.name = "Soirée jeux"
        self.games_masters = []
        self.players = None
        self.message = message
        self.config = config

        if message is not None:
            self.id = message.id
            date_element = re.search(r'([0-9]{2})/([0-9]{2}) à ([0-9]{2}) h ([0-9]{2})', message.content)
            name_parse = re.search(r'\*\*(.*)\*\*', message.content)
            if name_parse is not None:
                self.name = name_parse.group(1)
            if date_element is not None:
                now = datetime.now()
                day = int(date_element.group(1))
                month = int(date_element.group(2))
                hour = int(date_element.group(3))
                minutes = int(date_element.group(4))
                year = now.year + 1 if now.month > month else now.year
                self.date = datetime(year=year, month=month, day=day, hour=hour, minute=minutes)
                self.close_date = self.date + timedelta(hours=4)
                self.open_date = self.date - timedelta(hours=1)

            self.games_masters = re.findall('<@([^>]*)>', message.content)

    @property
    def is_open(self) -> bool:
        """
        Is the event open ?
        :return:
        """
        return self.config.reactions_cog.message is not None and self.config.reactions_cog.message.id == self.message.id

    async def open(self) -> None:
        """
        Open this event
        :return:
        """
        await self.config.reactions_cog.set_message(self.message)

    @property
    def can_close(self) -> bool:
        """
        Is this event expired ?
        :return:
        """
        return datetime.now() > self.close_date

    @property
    def can_open(self) -> bool:
        """
        Can this event be opened ?
        :return:
        """
        return self.open_date < datetime.now() < self.close_date
