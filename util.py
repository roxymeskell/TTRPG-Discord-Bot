# util.py
from discord.ext import commands
import discord

from cogfactory import make_cog, GroupCog
from colors import random_color

class Util(commands.Cog, name='Util'):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context):
        return ctx.author.permissions_in(ctx.channel).administrator

    @commands.command(
        name='clear-msgs',
        help='Clears all messages in channel.',
        description='Clears all messages in channel.'
    )
    async def clear_msgs(self, ctx):
        channel = ctx.channel
        await channel.purge()

    @commands.command(
        name='clear-groups',
        help='Clears all categories, channels, and roles associated with groups.',
        description='Clears all groups, channels, and roles associated with groups.'
    )
    async def clear_groups(self, ctx):
        guild = ctx.guild
        names = ''
        # Go through cogs
        cogs = list(filter(lambda c: isinstance(c[1], GroupCog), self.bot.cogs.items()))
        for c in cogs:
            name = c[1].name
            cat = discord.utils.get(guild.categories, id=c[1].group_id)
            for _c in cat.channels:
                await _c.delete()
            await cat.delete()
            member_role = discord.utils.get(guild.roles, name=f'{name} Member')
            if member_role:
                await member_role.delete()
            gm_role = discord.utils.get(guild.roles, name=f'{name} GM')
            if gm_role:
                await gm_role.delete()
            if not names:
                names = name
            else:
                names += f', {name}'
            self.bot.remove_cog(c[0])

        # Go through category channels
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
                names = name
            else:
                names += f', {name}'

        # Go through roles
        for r in list(filter(lambda r: r.name.endswith('Member'), guild.roles)):
            name = r.name.replace(' Member', '')
            await r.delete()
            gm_role = discord.utils.get(guild.roles, name=f'{name} GM')
            if gm_role:
                await gm_role.delete()
            if not names:
                names = name
            else:
                names += f', {name}'
        for r in list(filter(lambda r: r.name.endswith('GM'), guild.roles)):
            name = r.name.replace(' GM', '')
            await r.delete()
            if not names:
                names = name
            else:
                names += f', {name}'
        await ctx.send(f'Deleted channels: {names}')

def setup(bot):
    bot.add_cog(Util(bot))
