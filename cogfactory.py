import os
import traceback
import sys
import re
import time

import discord
from discord.ext import commands

class NullSubcommand(commands.CommandError):
    pass

def check_for_subcommand(ctx):
    if ctx.invoked_subcommand is None:
        raise NullSubcommand(message=f'Invalid `{ctx.command.qualified_name}` command passed.')
        return False
    return True

class GroupCog(commands.Cog):
    def _get_name(self):
        return self.__name
    def _get_cmd_name(self):
        return self.__cmd_name
    def _set_name(self, val):
        self.__name = val
        self.__cmd_name = re.sub(
            r'[^a-zA-Z0-9]+',
            r'-',
            re.sub(r'[\'"`]', '', self.__name.lower())
        )
        cmds = self.group.commands
        self.group.update(name=self.__cmd_name)
        for c in cmds:
            self.group.add_command(c)
    name = property(_get_name, _set_name)
    group_name = property(_get_name, _set_name)
    cmd = property(_get_cmd_name)

    def _get_cat_id(self):
        return self.__cat_id
    def _set_cat_id(self, val):
        self.__cat_id = val
    group_id = property(_get_cat_id, _set_cat_id)

    def _get_member_role_id(self):
        return self.__member_role_id
    def _set_member_role_id(self, val):
        self.__member_role_id = val
        self.group.add_check(
            commands.check_any(
                commands.has_role(self.member_role_id),
                commands.has_permissions(administrator=True)
            )
        )
        self.leave.add_check(
            commands.has_role(self.member_role_id)
        )
    member_role_id = property(_get_member_role_id, _set_member_role_id)

    def _get_gm_role_id(self):
        return self.__member_role_id
    def _set_gm_role_id(self, val):
        self.__gm_role_id = val
        self.add.add_check(
            commands.check_any(
                commands.has_role(self.gm_role_id),
                commands.has_permissions(administrator=True)
            )
        )
        self.kick.add_check(
            commands.check_any(
                commands.has_role(self.gm_role_id),
                commands.has_permissions(administrator=True)
            )
        )
        self.add_gm.add_check(
            commands.check_any(
                commands.has_role(self.gm_role_id),
                commands.has_permissions(administrator=True)
            )
        )
        self.resign_gm.add_check(
            commands.has_role(self.gm_role_id)
        )
    gm_role_id = property(_get_gm_role_id, _set_gm_role_id)

    def _get_member_role_name(self):
        return f'{self.__name} Member'
    member_role_name = property(_get_member_role_name)

    def _get_gm_role_name(self):
        return f'{self.__name} GM'
    gm_role_name = property(_get_gm_role_name)

    def _get_guild(self):
        return self.__guild
    def _set_guild(self, val):
        self.__guild = val
        member_role = discord.utils.get(self.guild.roles, name=self.member_role_name)
        gm_role = discord.utils.get(self.guild.roles, name=self.gm_role_name)
        cat = discord.utils.get(self.guild.categories, name=self.group_name)
        if not member_role:
            raise commands.ExtensionFailed(message='No member role for group.')
        if not gm_role:
            raise commands.ExtensionFailed(message='No GM role for group.')
        if not cat:
            raise commands.ExtensionFailed(message='No category channel for group.')
        self.member_role_id = member_role.id
        self.gm_role_id = gm_role.id
        self.group_id = cat.id
    guild = property(_get_guild, _set_guild)

    def setup(self, bot, name=None):
        if name is None:
            raise commands.ExtensionFailed(message='Group cog not given name.')
        self.cog_name = name
        self.name = name
        self.bot = bot
        if len(bot.guilds) == 0:
            raise commands.ExtensionFailed(message='Bot has no guilds.')
        self.guild = bot.get_guild(bot.guilds[0].id)

    async def cog_check(self, ctx: commands.Context):
        return ctx.author.guild_permissions.administrator or discord.utils.get(ctx.author.roles, name=self.member_role_name) is not None

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if before.id == self.group_id and before.name != after.name:
            guild = before.guild
            member_role = discord.utils.get(guild.roles, name=self.member_role_name)
            gm_role = discord.utils.get(guild.roles, name=self.gm_role_name)
            self.group_name = after.name
            await member_role.edit(
                reason='Group name updated.',
                name=f'{after.name} Member'
            )
            await gm_role.edit(
                reason='Group name updated.',
                name=f'{after.name} GM'
            )
            print(f'Group name updated to {self.cmd}')
        elif before.category is not None and before.category.id == self.group_id and (after.category is None or after.category.id != self.group_id):
            await after.delete()

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if channel.id == self.group_id:
            for c in channel.channels:
                await c.delete()
            guild = channel.guild
            member_role = discord.utils.get(guild.roles, name=self.member_role_name)
            gm_role = discord.utils.get(guild.roles, name=self.gm_role_name)
            await member_role.delete()
            await gm_role.delete()
            self.bot.remove_cog(self.cog_name)

    @commands.group(
        description='Provides commands for a specific group.',
        brief='Commands for specific TTRPG groups'
    )
    async def group(self, ctx):
        """Provides commands for a specific group."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)
            raise NullSubcommand(message=f'Invalid `{ctx.command.qualified_name}` command passed with no subcommand.')

    @group.command(
        name='add',
        description='Add member(s) to group.',
        brief='Add member(s)'
    )
    async def add(self, ctx, users: commands.Greedy[discord.Member]): # commands.Greedy[discord.Member]
        """Add a new member or members to the group.

        **Args:**
        `users` Users to add to group.
        """
        member_role = discord.utils.get(ctx.guild.roles, name=self.member_role_name)
        for user in users:
            await user.add_roles(member_role)
        # if user is None:
        #     await ctx.send_help(ctx.command)
        #     raise commands.BadArgument(message='No user provided.')
        # member_role = discord.utils.get(ctx.guild.roles, name=self.member_role_name)
        # await user.add_roles(member_role)

    @group.command(
        name='kick',
        description='Remove member from group.',
        brief='Remove member'
    )
    async def kick(self, ctx, user: discord.Member = None):
        """Remove member from the group.
        *Only accessible to GMs of group.*

        **Args:**
        `user` User to remove from group.
        """
        if user is None:
            await ctx.send_help(ctx.command)
            raise commands.BadArgument(message='No user provided.')
        if user == ctx.author:
            await ctx.send_help(ctx.command)
            raise commands.BadArgument(message='Cannot kick self.')
        member_role = discord.utils.get(ctx.guild.roles, name=self.member_role_name)
        gm_role = discord.utils.get(ctx.guild.roles, name=self.gm_role_name)
        await user.remove_roles(member_role, gm_role, reason='Kicked from group.')

    @group.command(
        name='leave',
        description='Remove self from group.',
        brief='Leave group'
    )
    async def leave(self, ctx):
        """Remove yourself from the group."""
        u = ctx.author
        member_role = discord.utils.get(ctx.guild.roles, name=self.member_role_name)
        gm_role = discord.utils.get(ctx.guild.roles, name=self.gm_role_name)
        await u.remove_roles(member_role, gm_role, reason='Requested to leave group.')
        members = member_role.members
        gms = gm_role.members
        if len(gms) == 0 and len(members) > 0:
          members[0].add_roles(gm_role)

    @group.group(
        name='gm',
        description='GM specific commands.',
        brief='GM specific commands'
    )
    #@commands.check(check_for_subcommand)
    async def gm_group(ctx):
        """Provides GM specific commands for the group."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)
            raise NullSubcommand(message=f'Invalid `{ctx.command.qualified_name}` command passed with no subcommand.')

    @gm_group.command(
        name='add',
        description='Add a user as a GM.',
        brief='Add GM'
    )
    async def add_gm(ctx, user: discord.Member = None):
        """Add member as GM of the group.
        *Only accessible to GMs of the group.*

        **Args:**
        `user` User to add as GM.
        """
        if user is None:
            raise commands.BadArgument(message='No user provided.')
        member_role = discord.utils.get(ctx.guild.roles, name=self.member_role)
        gm_role = discord.utils.get(ctx.guild.roles, name=self.gm_role)
        await user.add_roles(member_role, gm_role, reason='Made GM of group.')

    @gm_group.command(
        name='resign',
        description='Remove self as GM of group.',
        brief='Remove self as GM'
    )
    async def resign_gm(ctx):
        """Remove self as GM of the group.
        *Only accessible to GMs of the group.*
        """
        u = ctx.author
        member_role = ctx.guild.get_role(self.member_role_id)
        gm_role = ctx.guild.get_role(self.gm_role_id)
        await u.remove_roles(gm_role, reason='Resigned as GM of group.')
        members = member_role.members
        gms = gm_role.members
        if len(gms) == 0 and len(members) > 0:
          members[0].add_roles(gm_role)


def make_cog(group_name):
    class Cog(GroupCog, name=group_name):
        def __init__(self, bot):
            self.setup(bot, group_name)
    return Cog
