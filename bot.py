# bot.py
import os
import traceback
import sys
import time

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')

async def create_group_cmds(ctx, group_name):
    guild = ctx.guild
    existing_group = discord.utils.get(guild.categories, name=group_name)
    if not existing_group:
      return False

    member_role = discord.utils.get(guild.roles, name=f'{group_name} Member')
    if member_role is None:
        member_role = await guild.create_role(
            name=f'{group_name} Member',
            reason='Role for group did not exist.'
        )
    gm_role = discord.utils.get(guild.roles, name=f'{group_name} GM')
    if gm_role is None:
        gm_role = await guild.create_role(
            name=f'{group_name} GM',
            color=discord.Color.dark_purple(),
            reason='Role for group did not exist.'
        )

    @commands.group(group_name)
    async def group(ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid `group` command passed...')

    @group.command('add')
    @commands.check_any(commands.has_role(gm_role), commands.has_permissions(administrator=True))
    async def add(ctx, u: discord.Member = None): # commands.Greedy[discord.Member]
        if not u:
            return await ctx.send('No user provided.')
        await u.add_roles(member_role)

    @group.command('kick')
    @commands.check_any(commands.has_role(gm_role), commands.has_permissions(administrator=True))
    async def kick(ctx, u: discord.Member = None):
        if not u:
            return await ctx.send('No user provided.')
        if u == ctx.author:
            return await ctx.send('Cannot kick self.')
        await u.remove_roles(member_role, gm_role, reason='Kicked from group.')

    @group.command('leave')
    @commands.has_role(member_role)
    async def add(ctx):
        u = ctx.author
        await u.remove_roles(member_role, gm_role, reason='Requested to leave group.')
        members = filter(lambda m: member_role in m.roles, guild.members)
        gms = filter(lambda m: gm_role in m.roles, members)
        if len(gms) == 0 and len(members) > 0:
          members[0].add_roles(gm_role)

    @group.group('gm')
    async def gm_group(ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid `group gm` command passed...')

    @gm_group.command('add')
    @commands.check_any(commands.has_role(gm_role), commands.has_permissions(administrator=True))
    async def add_gm(ctx, u: discord.Member = None):
        if not u:
            return await ctx.send('No user provided.')
        await u.add_roles(member_role, gm_role, reason='Made GM of group.')

    @gm_group.command('resign')
    @commands.has_role(gm_role)
    async def add(ctx):
        u = ctx.author
        await u.remove_roles(gm_role, reason='Resigned as GM of group.')
        members = filter(lambda m: m != u and member_role in m.roles, guild.members)
        gms = filter(lambda m: gm_role in m.roles, members)
        if len(gms) == 0 and len(members) > 0:
          members[0].add_roles(gm_role)

    bot.add_command(group)
    return True

@bot.event
async def on_command_error(ctx, error):
    """The event triggered when an error is raised while invoking a command.
    ctx   : Context
    error : Exception"""

    if hasattr(ctx.command, 'on_error'):
        return

    ignored = (commands.CommandNotFound, commands.UserInputError)
    error = getattr(error, 'original', error)

    if isinstance(error, ignored):
        return
    elif isinstance(error, commands.DisabledCommand):
        return await ctx.send(f'{ctx.command} has been disabled.')
    elif isinstance(error, commands.NoPrivateMessage):
        try:
            return await ctx.author.send(f'{ctx.command} can not be used in Private Messages.')
        except:
            pass
    elif isinstance(error, commands.BadArgument):
        if ctx.command.qualified_name == 'tag list':
            return await ctx.send('I could not find that member. Please try again.')
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(f'{ctx.command} not found. Looking to see if it should exist...')
        if await create_group_cmds(ctx, ctx.command):
            await bot.invoke(ctx)
    print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
    await ctx.send(f'Something sent wrong when trying to execute {ctx.command}.')

@bot.command(name='create-group')
async def create_group(ctx, group_name=''):
    ctx.send(f'Executing {ctx.command} with args: {group_name}')
    if not group_name:
        group_name = hex(int(time.time())-(31536000*50)).replace('0x','').upper()
    guild = ctx.guild
    existing_group = discord.utils.get(guild.categories, name=group_name)
    if not existing_group:
        member_role = await guild.create_role(
            name=f'{group_name} Member',
            reason='New group created.'
        )
        gm_role = await guild.create_role(
            name=f'{group_name} GM',
            color=discord.Color.dark_purple(),
            reason='New group created.'
        )
        ctx.author.add_roles(member_role, gm_role)
        print(f'Creating a new category: {group_name}')
        category = await guild.create_category(
            group_name,
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
                    manage_permissions=True,
                    move_members=True,
                    mute_members=True,
                    deafen_members=True,
                    stream=True,
                    priority_speaker=True
                ),
            }
        )
        await category.create_text_channel('General')
        await category.create_voice_channel('General')
        await create_group_cmds(ctx, group_name)

bot.run(TOKEN)
