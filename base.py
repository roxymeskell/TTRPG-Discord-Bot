# base.py
from discord.ext import commands
import discord
import traceback
import sys
import time

from cogfactory import make_cog
from colors import colors, random_color

class Base(commands.Cog, name='Base'):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Logged in as {self.bot.user.name} - {self.bot.user.id}')
        if len(self.bot.guilds) == 0:
            raise commands.ExtensionFailed(message='Bot has no guilds.')
        guild = self.bot.get_guild(self.bot.guilds[0].id)
        for c in guild.categories:
            self.bot.add_cog(make_cog(c.name)(self.bot))

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command.
        ctx   : Context
        error : Exception"""

        if hasattr(ctx.command, 'on_error'):
            return

        ignored = (commands.CommandNotFound, commands.UserInputError)
        error = getattr(error, 'original', error)

        if isinstance(error, ignored):
            return

        err_embed = discord.Embed(
            title='Error',
            description=f'There was an error executing `{ctx.command}`.',
            color=colors['DARK_RED']
        )
        #err_embed.set_thumbnail(url=self.bot.user.avatar_url)
        err_embed.set_footer(
            text=f'Command executed by {ctx.message.author.name}',
            icon_url=ctx.author.avatar_url
        )

        if isinstance(error, commands.DisabledCommand):
            err_embed.add_field(
                name='Message',
                value=f'{ctx.command} has been disabled.',
                inline=False
            )
            return await ctx.send(embed=err_embed)
        elif isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.author.send(f'`{ctx.command}` can not be used in Private Messages.')
            except:
                pass
        elif isinstance(error, commands.BadArgument):
            if ctx.command.qualified_name == 'tag list':
                err_embed.add_field(
                    name='Message',
                    value=f'I could not find that member. Please try again.',
                    inline=False
                )
                return await ctx.send(embed=err_embed)
        elif isinstance(error, commands.CommandNotFound):
            err_embed.add_field(
                name='Message',
                value=f'{ctx.command} not found.\nYou should check with an admin if you think it should.',
                inline=False
            )
            return await ctx.send(embed=err_embed)
            # await ctx.send(f'{ctx.command} not found. Looking to see if it should exist...')
            # existing_group = discord.utils.get(ctx.guild.categories, name=ctx.command)
            # if existing_group: # await create_group_cmds(ctx, ctx.command):
            #     self.bot.add_cog(make_cog(ctx.command)(self.bot))
            #     return await self.bot.invoke(ctx)
            # return await ctx.send(f'{ctx.command} does not exist.')
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        excep = traceback.format_exception_only(type(error), error)
        excepArr = excep[0].split(': ', 1)
        excep[0] = excepArr[1]
        err_embed.add_field(
            name=excepArr[0],
            value=''.join(excep).replace('\'', '`'),
            inline=False
        )
        if error.__traceback__ is not None:
            tb_str = ''.join(traceback.format_tb(error.__traceback__)).replace('\t', '  ')
            err_embed.add_field(
                name='Traceback (most recent call last):',
                value=f'```\n{tb_str[0:800]}\n```',
                inline=False
            )
        #traceback.format_exception(type(error), error, error.__traceback__)
        await ctx.send(embed=err_embed)

    @commands.command(
        name='create-group',
        help='Creates a new TTRPG group.',
        description='Creates a new TTRPG group.',
        aliases=['make-group', 'new-group', 'make', 'new', 'create']
    )
    async def create_group(self, ctx, group_name=''):
        await ctx.send(f'Executing {ctx.command} with args: {group_name}')
        if not group_name:
            group_name = hex(int(time.time())-(31536000*50)).replace('0x','').upper()
        guild = ctx.guild
        existing_group = discord.utils.get(guild.categories, name=group_name)
        if not existing_group:
            member_role = await guild.create_role(
                name=f'{group_name} Member',
                reason=f'Created group {group_name}'
            )
            gm_role = await guild.create_role(
                name=f'{group_name} GM',
                color=discord.Color.dark_purple(),
                reason=f'Created group {group_name}'
            )
            category = await guild.create_category(
                group_name,
                reason=f'Created group {group_name}.',
                overwrites={
                    guild.default_role: discord.PermissionOverwrite(
                        view_channel=False,
                        send_messages=False,
                        send_tts_messages=False,
                        connect=False,
                        speak=False
                    ),
                    member_role: discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        send_tts_messages=True,
                        connect=True,
                        speak=True
                    ),
                    gm_role: discord.PermissionOverwrite(
                        #create_instant_invite=True,
                        view_channel=True,
                        send_messages=True,
                        send_tts_messages=True,
                        connect=True,
                        speak=True,
                        manage_channels=True,
                        manage_permissions=True,
                        move_members=True,
                        mute_members=True,
                        deafen_members=True,
                        stream=True,
                        priority_speaker=True
                    ),
                }
            )
            await category.create_text_channel('general', reason=f'Created group {group_name}.')
            await category.create_voice_channel('general', reason=f'Created group {group_name}.')
            print(member_role, gm_role)
            await ctx.author.add_roles(member_role, gm_role, reason=f'Created group {group_name}.')
            self.bot.add_cog(make_cog(group_name)(self.bot))


def setup(bot):
    bot.add_cog(Base(bot))
