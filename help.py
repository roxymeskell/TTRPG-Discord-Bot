# help.py
from discord.ext import commands as Commands
import discord
import itertools
import re

from colors import random_color
from cogfactory import GroupCog

class MyHelpCommand(Commands.HelpCommand):
    """The implementation of the default help command.
    This inherits from :class:`HelpCommand`.
    It extends it with the following attributes.
    Attributes
    ------------
    width: :class:`int`
        The maximum number of characters that fit in a line.
        Defaults to 80.
    sort_commands: :class:`bool`
        Whether to sort the commands in the output alphabetically. Defaults to ``True``.
    dm_help: Optional[:class:`bool`]
        A tribool that indicates if the help command should DM the user instead of
        sending it to the channel it received it from. If the boolean is set to
        ``True``, then all help output is DM'd. If ``False``, none of the help
        output is DM'd. If ``None``, then the bot will only DM when the help
        message becomes too long (dictated by more than :attr:`dm_help_threshold` characters).
        Defaults to ``False``.
    dm_help_threshold: Optional[:class:`int`]
        The number of characters the paginator must accumulate before getting DM'd to the
        user if :attr:`dm_help` is set to ``None``. Defaults to 1000.
    indent: :class:`int`
        How much to indent the commands from a heading. Defaults to ``2``.
    commands_heading: :class:`str`
        The command list's heading string used when the help command is invoked with a category name.
        Useful for i18n. Defaults to ``"Commands:"``
    no_category: :class:`str`
        The string used when there is a command which does not belong to any category(cog).
        Useful for i18n. Defaults to ``"No Category"``
    paginator: :class:`Paginator`
        The paginator used to paginate the help command output.
    """

    def __init__(self, **options):
        self.width = options.pop('width', 80)
        self.indent = options.pop('indent', 2)
        self.sort_commands = options.pop('sort_commands', True)
        self.dm_help = options.pop('dm_help', False)
        self.dm_help_threshold = options.pop('dm_help_threshold', 1000)
        self.commands_heading = options.pop('commands_heading', "Commands:")
        self.no_category = options.pop('no_category', 'No Category')
        self.paginator = options.pop('paginator', None)

        if self.paginator is None:
            self.paginator = Commands.Paginator()

        super().__init__(**options)

    def shorten_text(self, text):
        """Shortens text to fit into the :attr:`width`."""
        if len(text) > self.width:
            return text[:self.width - 3] + '...'
        return text

    def get_ending_note(self):
        """Returns help command's ending note. This is mainly useful to override for i18n purposes."""
        command_name = self.invoked_with
        return "Type `{0}{1} command` for more info on a command.\n" \
               "You can also type `{0}{1} category` for more info on a category.".format(self.clean_prefix, command_name)

    def add_indented_commands(self, commands, *, heading, max_size=None, tabs=1):
        """Indents a list of commands after the specified heading.
        The formatting is added to the :attr:`paginator`.
        The default implementation is the command name indented by
        :attr:`indent` spaces, padded to ``max_size`` followed by
        the command's :attr:`Command.short_doc` and then shortened
        to fit into the :attr:`width`.
        Parameters
        -----------
        commands: Sequence[:class:`Command`]
            A list of commands to indent for output.
        heading: :class:`str`
            The heading to add to the output. This is only added
            if the list of commands is greater than 0.
        max_size: Optional[:class:`int`]
            The max size to use for the gap between indents.
            If unspecified, calls :meth:`get_max_size` on the
            commands parameter.
        """

        if not commands:
            return

        self.paginator.add_line(heading)
        max_size = max_size or self.get_max_size(commands)

        get_width = discord.utils._string_width
        for command in commands:
            if isinstance(command.cog, GroupCog) and command.parent is None:
                name = '[group-name]'
            else:
                name = command.name
            width = max_size - (get_width(name) - len(name))
            entry = '{0}{1:<{width}} {2}'.format(self.indent * tabs * ' ', name, command.short_doc, width=width)
            if isinstance(command, Commands.Group):
                self.add_indented_commands(
                    list(command.commands),
                    heading=self.shorten_text(entry),
                    tabs=tabs+1
                )
            else:
                self.paginator.add_line(self.shorten_text(entry))

    async def send_pages(self):
        """A helper utility to send the page output from :attr:`paginator` to the destination."""
        destination = self.get_destination()
        ctx = self.context
        bot = ctx.bot
        i = 0
        title = 'Help'
        description = ''
        curr_header = ''
        for page in self.paginator.pages:
            try:
                page_spl = re.split(r'([\w ]+:\n)', page.replace('```',''))
                if page_spl[0] == '':
                    page_spl.pop(0)
                if ':\n' not in page_spl[0] and i == 0:
                    description = page_spl.pop(0)
                embed = discord.Embed(
                    title='Help' if i==0 else 'Help cont.',
                    description=description,
                    color=random_color()
                )
                embed.set_thumbnail(url=bot.user.avatar_url)
                embed.set_footer(
                    text=f'Requested by {ctx.message.author.name}',
                    icon_url=ctx.author.avatar_url
                )
                if ':\n' not in page_spl[0] and i == 0:
                    content = page_spl.pop(0)
                    embed.add_field(
                       name=f'{curr_header} Cont.',
                       value=content if 'Commands' not in curr_header else f'```\n{content}\n```',
                       inline=False
                    )
                page_spl = zip(page_spl[0::2], page_spl[1::2])
                for head, content in page_spl:
                    head = head.replace(':\n', '')
                    curr_header = head
                    embed.add_field(
                       name=head if head != 'Note' else '\u200b',
                       value=content if 'Commands' not in head else f'```\n{content}\n```',
                       inline=False
                    )
                await destination.send(embed=embed)
            except:
                await destination.send(page)
            finally:
                i += 1

    def add_command_formatting(self, command):
        """A utility function to format the non-indented block of commands and groups.
        Parameters
        ------------
        command: :class:`Command`
            The command to format.
        """

        if command.description:
            self.paginator.add_line(command.description, empty=True)

        signature = self.get_command_signature(command)
        self.paginator.add_line(f'`{signature}`', empty=True)

        if command.help:
            try:
                self.paginator.add_line(command.help, empty=True)
            except RuntimeError:
                for line in command.help.splitlines():
                    self.paginator.add_line(line)
                self.paginator.add_line()

    def add_indented_command(self, command):
        """A utility function to format the non-indented block of commands and groups.
        Parameters
        ------------
        command: :class:`Command`
            The command to format.
        """

        cmd = command
        tab = 0
        while cmd.parent is not None:
            tab += 1
            cmd = cmd.parent

        if isinstance(command.cog, GroupCog) and tab == 0:
            name = '[group]'
        else:
            name = command.name
        width = max_size - (get_width(name) - len(name))
        entry = '{0}{1:<{width}} {2}'.format(self.indent * tab * ' ', name, command.short_doc, width=width)
        self.paginator.add_line(self.shorten_text(entry))

    def get_destination(self):
        ctx = self.context
        if self.dm_help is True:
            return ctx.author
        elif self.dm_help is None and len(self.paginator) > self.dm_help_threshold:
            return ctx.author
        else:
            return ctx.channel

    async def prepare_help_command(self, ctx, command):
        self.paginator.clear()
        await super().prepare_help_command(ctx, command)

    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot

        if bot.description:
            # <description> portion
            self.paginator.add_line(bot.description, empty=True)

        no_category = '\u200b{0.no_category} Commands:'.format(self)
        def get_category(command, *, no_category=no_category):
            cog = command.cog
            if isinstance(cog, GroupCog) or command.name == 'create-group':
                return 'Group Commands:'
            else:
                return 'General Commands:'
            return cog.qualified_name + 'Commands:' if cog is not None else no_category

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        group_cmds = [c for c in filtered if isinstance(c.cog, GroupCog)]
        group_cmd = group_cmds[0] if len(group_cmds) > 0 else None
        filtered = [c for c in filtered if not isinstance(c.cog, GroupCog)]
        if group_cmd is not None:
            filtered.append(group_cmd)
        max_size = self.get_max_size(filtered)
        to_iterate = itertools.groupby(filtered, key=get_category)

        # Now we can add the commands to the page.
        for category, commands in to_iterate:
            commands = sorted(commands, key=lambda c: c.name) if self.sort_commands else list(commands)
            self.add_indented_commands(commands, heading=category, max_size=max_size, tabs=0)

        cogs = list(filter(lambda c: isinstance(c, GroupCog), bot.cogs.values()))
        self.paginator.add_line('Groups:')
        for cog in cogs:
            self.paginator.add_line(f'**_{cog.name}_**: `{cog.cmd}`')

        note = self.get_ending_note()
        if note:
            self.paginator.add_line('Note:')
            self.paginator.add_line(note)

        await self.send_pages()

    async def send_command_help(self, command):
        self.add_command_formatting(command)
        self.paginator.close_page()
        await self.send_pages()

    async def send_group_help(self, group):
        self.add_command_formatting(group)

        filtered = await self.filter_commands(group.commands, sort=self.sort_commands)
        self.add_indented_commands(filtered, heading=self.commands_heading, tabs=0)

        if filtered:
            note = self.get_ending_note()
            if note:
                self.paginator.add_line('Note:')
                self.paginator.add_line(note)

        await self.send_pages()

    async def send_cog_help(self, cog):
        if cog.description:
            self.paginator.add_line(cog.description, empty=True)

        filtered = await self.filter_commands(cog.get_commands(), sort=self.sort_commands)
        self.add_indented_commands(filtered, heading=self.commands_heading)

        note = self.get_ending_note()
        if note:
            self.paginator.add_line('Note:')
            self.paginator.add_line(note)

        await self.send_pages()
