# bot.py
import os
import traceback
import sys
import time

import discord
from discord.ext import commands
from dotenv import load_dotenv

from cogfactory import make_cog
from colors import random_color

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')
bot.remove_command('help')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    if len(bot.guilds) == 0:
        raise commands.ExtensionFailed(message='Bot has no guilds.')
    guild = bot.get_guild(bot.guilds[0].id)
    for c in guild.categories:
        bot.add_cog(make_cog(c.name)(bot))
    for comm in bot.commands:
        print(f'**{comm.name}** - *{comm.description}*\n')
    return

@bot.command(
    name='help',
    description='The help command!',
    aliases=['commands', 'command']
)
async def help_command(ctx):
    print('Helping!')

    # The third parameter comes into play when
    # only one word argument has to be passed by the user

    # Prepare the embed
    help_embed = discord.Embed(
        title='Help',
        color=random_color()
    )
    help_embed.set_thumbnail(url=bot.user.avatar_url)
    help_embed.set_footer(
        text=f'Requested by {ctx.message.author.name}',
        icon_url=ctx.author.avatar_url
    )

    commands_list = ''
    for comm in bot.commands:
        if comm.cog is None:
            commands_list += f'**{comm.name}** - *{comm.description}*\n'
            if isinstance(comm, commands.Group):
                cog_subcommands = comm.commands
                for comm in cog_subcommands:
                    commands_list += f'\t**{comm.name}** - *{comm.description}*\n'
    help_embed.add_field(
       name='Base Commands',
       value=commands_list,
       inline=False
    ).add_field(
        name='\u200b', value='\u200b', inline=False
    )

    cogs = [c for c in bot.cogs.keys()]
    cog = cogs[0]
    cog_commands = bot.get_cog(cog).get_commands()
    commands_list = ''
    comm = bot.get_command(cog_commands[0].name)
    commands_list += f'**_[group]_** - *{comm.description}*\n'
    print(comm, comm.commands, isinstance(comm, commands.Group), comm.get_command('add'))
    cog_subcommands = comm.commands
    for comm in cog_subcommands:
        commands_list += f'\t**{comm.name}** - *{comm.description}*\n'
        if isinstance(comm, commands.Group):
            cog_subsubcommands = comm.commands
            for comm in cog_subsubcommands:
                commands_list += f'\t\t**{comm.name}** - *{comm.description}*\n'\

    groups_list = ''
    for cog in cogs:
        groups_list += f'**_{cog}_** - *{bot.get_cog(cog).group_name}*\n'

    help_embed.add_field(
       name='Group Commands',
       value=commands_list,
       inline=False
    ).add_field(
        name='Groups',
        value=groups_list,
        inline=False
    ).add_field(
        name='\u200b', value='\u200b', inline=False
    )

    return await ctx.send(embed=help_embed)

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
        existing_group = discord.utils.get(ctx.guild.categories, name=ctx.command)
        if existing_group: # await create_group_cmds(ctx, ctx.command):
            bot.add_cog(make_cog(ctx.command)(bot))
            return await bot.invoke(ctx)
        return await ctx.send(f'{ctx.command} does not exist.')
    print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
    await ctx.send(f'Something sent wrong when trying to execute {ctx.command}.')

@bot.command(name='clear-msgs')
async def clear_msgs(ctx):
    channel = ctx.channel
    await channel.purge()

@bot.command(name='clear-groups')
async def clear_groups(ctx):
    guild = ctx.guild
    names = ''
    for c in guild.categories:
        name = c.name
        for _c in c.channels:
            await _c.delete()
        await c.delete()
        member_role = discord.utils.get(guild.roles, name=f'{name} Member')
        if member_role:
            await member_role.delete()
        gm_role = discord.utils.get(guild.roles, name=f'{name} GM')
        if gm_role:
            await gm_role.delete()
        if not names:
            name = name
        else:
            names += f', {name}'
    for r in list(filter(lambda r: r.name.endswith('Member'), guild.roles)):
        name = r.name.replace(' Member', '')
        await r.delete()
        gm_role = discord.utils.get(guild.roles, name=f'{name} GM')
        if gm_role:
            await gm_role.delete()
        if not names:
            name = name
        else:
            names += f', {name}'
    for r in list(filter(lambda r: r.name.endswith('GM'), guild.roles)):
        name = r.name.replace(' GM', '')
        await r.delete()
        if not names:
            name = name
        else:
            names += f', {name}'
    await ctx.send(f'Deleted channels: {names}')

@bot.command(name='create-group')
async def create_group(ctx, group_name=''):
    await ctx.send(f'Executing {ctx.command} with args: {group_name}')
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
        await category.create_text_channel('General')
        await category.create_voice_channel('General')
        bot.add_cog(make_cog(group_name)(bot))
        #await create_group_cmds(ctx, group_name)

bot.run(TOKEN)
