# help.py
from discord.ext import commands as cmds
import discord
import itertools
import re

from colors import random_color
from cogfactory import GroupCog

__all__ = ['MyHelpCommand', 'EmbedPaginator']

class EmbedPaginator: #(cmds.Paginator):
    # EMBEDED LIMITS:
    # title	256 characters
    # description	2048 characters
    # fields	Up to 25 field objects
    # field.name	256 characters
    # field.value	1024 characters
    # footer.text	2048 characters
    # def __init__(self, **options):
    #     self.super().__init__(**options)
    def __init__(self, max_size=2000):
        self.max_size = max_size
        self.clear()

    def clear(self):
        self.title = None
        self.description = None
        self.footer = None
        self.footer_icon_url = None
        self.thumbnail_url = None
        self.prefix = None
        self.suffix = None
        self._current_name = ''
        self._current_page = {
            'fields': [],
        }
        self._base_count = 0
        self._count = 0
        self._pages = []

    def set_title(self, title):
        if len(title) > 248:
            raise RuntimeError('Description exceeds maximum size 248')
        self.title = title
        self._base_count += len(title) + 1 + 8 # title + newline + space for ' Cont. #'

    def set_description(self, description):
        if len(description) > 2048:
            raise RuntimeError('Description exceeds maximum size 2048')
        self.description = description
        self._base_count += len(description) + 1 # description + newline

    def set_thumbnail(self, url):
        self.thumbnail_url = url

    def set_footer(self, footer, icon_url=None):
        if len(footer) > 2048:
            raise RuntimeError('Footer text exceeds maximum size 2048')
        self.footer = footer
        self.footer_icon_url = icon_url
        self._base_count += len(footer) + 1 # footer + newline

    def set_prefix(self, prefix=None):
        self.prefix = prefix
        if len(self._current_page['fields']) > 0:
            if len(self._current_page['fields'][-1]['value']) == 0:
                self._current_page['fields'][-1]['value'] += prefix
                self._count += len(prefix) + 1
            else:
                self._current_page['fields'][-1]['value'] += '\n%s' % (prefix)
                self._count += len(prefix) + 2 # prefix + 2*newline

    def set_suffix(self, suffix=None):
        if self.suffix is not None and len(self._current_page['fields']) > 0:
            self._current_page['fields'][-1]['value'] += '\n%s' % (self.suffix)
            self._count += len(self.suffix) + 1
        self.suffix = suffix

    def clear_prefix(self):
        self.prefix = None

    def clear_suffix(self):
        if self.suffix is not None and len(self._current_page['fields']) > 0:
            self._current_page['fields'][-1]['value'] += '\n%s' % (self.suffix)
            self._count += len(self.suffix) + 1
        self.suffix = None

    @property
    def _suffix_len(self):
        return len(self.suffix) if self.suffix else 0

    @property
    def _prefix_len(self):
        return len(self.prefix) if self.prefix else 0

    @property
    def _suffix_len(self):
        return len(self.suffix) if self.suffix else 0

    def close_page(self):
        if self.suffix is not None and len(self._current_page['fields']) > 0:
            self._current_page['fields'][-1]['value'] += '\n%s' % (self.suffix)
        if self.title is not None:
            self._current_page['title'] = self.title
            if len(self._pages) > 0:
                self._current_page['title'] += ' Cont. %d' % (len(self._pages) + 1)
        if self.description is not None:
            self._current_page['description'] = self.description
        if self.footer is not None:
            self._current_page['footer'] = { 'text': self.footer}
            if self.footer_icon_url  is not None:
                self._current_page['footer']['icon_url'] = self.footer_icon_url
        if self.thumbnail_url  is not None:
            self._current_page['thumbnail'] = { 'url': self.thumbnail_url }
        self._current_page['color'] = random_color()
        self._current_page['type'] = 'rich'

        self._pages.append(self._current_page)
        self._current_page = { 'fields': [] }
        self._count = 0

    def add_name(self, name='\u200b'):
        if len(name) > 250:
            raise RuntimeError('Field name exceeds maximum size 250')

        if self.suffix is not None and len(self._current_page['fields']) > 0:
            self._current_page['fields'][-1]['value'] += '\n%s' % (self.suffix)
            self._count += len(self.suffix) + 1

        if self._count + self._base_count + len(name) + 1 > self.max_size - self._suffix_len or len(self._current_page['fields']) == 25:
            self.close_page()

        self._current_page['fields'].append({ 'inline': False, 'name': name, 'value': '' })
        self._count += len(name) + 1

    def add_line(self, line='', *, empty=False):
        max_page_size = self.max_size - self._prefix_len - self._suffix_len - 2
        if len(line) > max_page_size:
            raise RuntimeError('Line exceeds maximum page size %s' % (max_page_size))

        if self._count + self._base_count + len(line) + 1 > self.max_size - self._suffix_len:
            self.close_page()

        if len(self._current_page['fields']) == 0:
            self._current_page['fields'].append({ 'inline': False, 'name': '\u200b', 'value': '' })
            self._count += 1
        elif len(self._current_page['fields'][-1]['value']) + len(line) + self._suffix_len + 1 >= 1024:
            self.add_name()

        if len(self._current_page['fields'][-1]['value']) == 0 and self.prefix:
            self._current_page['fields'][-1]['value'] += self.prefix
            self._count += len(self.prefix) + 1

        if len(self._current_page['fields'][-1]['value']) == 0:
            self._current_page['fields'][-1]['value'] += line
            self._count += len(line)
        else:
            self._current_page['fields'][-1]['value'] += '\n%s' % (line)
            self._count += len(line) + 1

        if empty:
            self._current_page['fields'][-1]['value'] += '\n'
            self._count += 1

    @property
    def pages(self):
        """Returns the rendered list of pages."""
        # we have more than just the prefix in our current page
        if self._count > (0 if self.prefix is None else self._prefix_len + 1):
            self.close_page()
        return list(map(lambda p : discord.Embed.from_dict(p), self._pages))

class MyHelpCommand(cmds.HelpCommand):
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
        options['verify_checks'] = True

        if self.paginator is None:
            self.paginator = EmbedPaginator() #cmds.Paginator()

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

    async def add_indented_commands(self, commands, *, max_size=None, tabs=1):
        max_size = max_size or self.get_max_size(commands)

        get_width = discord.utils._string_width
        for command in commands:
            if isinstance(command.cog, GroupCog) and command.parent is None:
                name = '[group-name]'
            else:
                name = command.name
            width = max_size - (get_width(name) - len(name))
            entry = '{0}{1:<{width}} {2}'.format(self.indent * tabs * ' ', name, command.short_doc, width=width)
            if isinstance(command, cmds.Group):
                subcommands = await self.filter_commands(command.commands, sort=self.sort_commands)
                self.paginator.add_line(self.shorten_text(entry))
                await self.add_indented_commands(
                    list(subcommands),
                    tabs=tabs+1
                )
            else:
                self.paginator.add_line(self.shorten_text(entry))

    async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            await destination.send(embed=page)

    def add_command_formatting(self, command):
        """A utility function to format the non-indented block of commands and groups.
        Parameters
        ------------
        command: :class:`Command`
            The command to format.
        """

        self.paginator.set_title(f'Command Help "{command.qualified_name}"')

        if command.description:
            self.paginator.set_description(command.description)

        self.paginator.add_name('Command')
        signature = self.get_command_signature(command)
        self.paginator.set_prefix('```')
        self.paginator.set_suffix('```')
        self.paginator.add_line(f'{signature}', empty=True)
        self.paginator.clear_prefix()
        self.paginator.clear_suffix()

        if command.help:
            try:
                self.paginator.add_line(command.help, empty=True)
            except RuntimeError:
                for line in command.help.splitlines():
                    self.paginator.add_line(line)
                self.paginator.add_line()

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
        self.paginator.set_thumbnail(url=str(ctx.bot.user.avatar_url))
        self.paginator.set_title('Help')
        self.paginator.set_footer(
            f'Requested by {ctx.message.author.name}',
            icon_url=str(ctx.author.avatar_url)
        )
        await super().prepare_help_command(ctx, command)

    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot

        if bot.description:
            # <description> portion
            self.paginator.add_description(bot.description)

        no_category = '\u200b{0.no_category} Commands'.format(self)
        def get_category(command, *, no_category=no_category):
            cog = command.cog
            if isinstance(cog, GroupCog) or command.name == 'create-group':
                return 'Group Commands'
            else:
                return 'General Commands'
            return cog.qualified_name + 'Commands' if cog is not None else no_category

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        group_cmds = [c for c in filtered if isinstance(c.cog, GroupCog)]
        group_cmd = group_cmds[0] if len(group_cmds) > 0 else None
        filtered = [c for c in filtered if not isinstance(c.cog, GroupCog)]
        if group_cmd is not None:
            filtered.append(group_cmd)
        max_size = self.get_max_size(filtered)
        to_iterate = itertools.groupby(filtered, key=get_category)

        # Now we can add the commands to the page.
        self.paginator.set_prefix('```')
        self.paginator.set_suffix('```')
        for category, commands in to_iterate:
            commands = sorted(commands, key=lambda c: c.name) if self.sort_commands else list(commands)
            self.paginator.add_name(category)
            await self.add_indented_commands(commands, max_size=max_size, tabs=0)
        self.paginator.clear_prefix()
        self.paginator.clear_suffix()

        self.paginator.add_name('Groups')
        for c in group_cmds:
            self.paginator.add_line(f'**{c.cog.name}**: `{c.cog.cmd}`')

        # cogs = list(filter(lambda c: isinstance(c, GroupCog), bot.cogs.values()))
        # self.paginator.add_line('Groups:')
        # for cog in cogs:
        #     self.paginator.add_line(f'**_{cog.name}_**: `{cog.cmd}`')

        note = self.get_ending_note()
        if note:
            self.paginator.add_name()
            self.paginator.add_line(note)

        await self.send_pages()

    async def send_command_help(self, command):
        self.add_command_formatting(command)
        self.paginator.close_page()
        await self.send_pages()

    async def send_group_help(self, group):
        self.add_command_formatting(group)

        #self.paginator.add_name(self.commands_heading)
        self.paginator.add_name('Subcommands')
        filtered = await self.filter_commands(group.commands, sort=self.sort_commands)
        self.paginator.set_prefix('```')
        self.paginator.set_suffix('```')
        await self.add_indented_commands(filtered, tabs=0)
        self.paginator.clear_prefix()
        self.paginator.clear_suffix()

        if filtered:
            note = self.get_ending_note()
            if note:
                self.paginator.add_name()
                self.paginator.add_line(note)

        await self.send_pages()

    async def send_cog_help(self, cog):
        self.paginator.set_title(f'Cog Help "{cog.qualified_name}"')
        if cog.description:
            self.paginator.set_description(cog.description)

        self.paginator.add_name(self.commands_heading)
        filtered = await self.filter_commands(cog.get_commands(), sort=self.sort_commands)
        self.paginator.set_prefix('```')
        self.paginator.set_suffix('```')
        await self.add_indented_commands(filtered, tabs=0)
        self.paginator.clear_prefix()
        self.paginator.clear_suffix()

        note = self.get_ending_note()
        if note:
            self.paginator.add_name()
            self.paginator.add_line(note)

        await self.send_pages()
