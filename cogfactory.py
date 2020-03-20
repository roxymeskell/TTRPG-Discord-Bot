import asyncio
import os
import traceback
import sys
import time

import discord
from discord.ext import commands

def make_cog(group_name):
    class Cog(commands.Cog, name=group_name):
        def __init__(self, bot):
            self.bot = bot
            self.group_name = group_name
            self.member_role_name = f'{group_name} Member'
            self.gm_role_name = f'{group_name} GM'

            if len(bot.guilds) == 0:
                raise commands.ExtensionFailed(message='Bot has no guilds.')
            guild = bot.get_guild(bot.guilds[0].id)
            self.guild = guild
            self.member_role = discord.utils.get(guild.roles, name=self.member_role_name)
            self.gm_role = discord.utils.get(guild.roles, name=self.gm_role_name)

            self.member_role_id = self.member_role.id
            self.gm_role_id = self.gm_role.id
            self.group_id = discord.utils.get(guild.categories, name=group_name).id

            self.group.update(name=self.group_name)
            self.group.add_check(
                commands.check_any(
                    commands.has_role(self.member_role_id),
                    commands.has_permissions(administrator=True)
                )
            )
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
            self.leave.add_check(
                commands.has_role(self.member_role_id)
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

        @commands.Cog.listener()
        async def on_guild_channel_update(self, before, after):
            #if before.type == discord.ChannelType.category and before.name == self.group_name:
            if before.id == self.group_id and before.name != after.name:
                guild = before.guild
                self.group_name = after.name
                self.member_role_name = f'{after.name} Member'
                self.gm_role_name = f'{after.name} GM'
                await guild.get_role(self.member_role_id).edit(
                    reason='Group name updated.',
                    name=f'{after.name} Member'
                )
                await guild.get_role(self.gm_role_id).edit(
                    reason='Group name updated.',
                    name=f'{after.name} GM'
                )
                self.group.update(name=after.name)
                print(f'Group name updated to {after.name}')

        # @commands.group(self.group_name)
        # @commands.check_any(
        #     commands.has_role(self.member_role_id),
        #     commands.has_permissions(administrator=True)
        # )
        @commands.group()
        async def group(self, ctx):
            if ctx.invoked_subcommand is None:
                await ctx.send(f'Invalid `{ctx.command.qualified_name}` command passed...')

        @group.command(
            name='add'
        )
        # @commands.check_any(
        #     commands.has_role(self.gm_role_id),
        #     commands.has_permissions(administrator=True)
        # )
        async def add(self, ctx, u: discord.Member = None): # commands.Greedy[discord.Member]
            if u is None:
                raise commands.BadArgumentError(message='No user provided.')
                return await ctx.send('No user provided.')
            member_role = discord.utils.get(guild.roles, name=self.member_role_name)
            await u.add_roles(member_role)

        @group.command(
            name='kick'
        )
        # @commands.check_any(
        #     commands.has_role(self.gm_role_id),
        #     commands.has_permissions(administrator=True)
        # )
        async def kick(self, ctx, u: discord.Member = None):
            if u is None:
                raise commands.BadArgumentError(message='No user provided.')
            if u == ctx.author:
                raise commands.BadArgumentError(message='Cannot kick self.')
            member_role = discord.utils.get(ctx.guild.roles, name=self.member_role_name)
            gm_role = discord.utils.get(ctx.guild.roles, name=self.gm_role_name)
            await u.remove_roles(member_role, gm_role, reason='Kicked from group.')

        @group.command(
            name='leave'
        )
        # @commands.has_role(self.member_role_name)
        async def leave(self, ctx):
            u = ctx.author
            member_role = discord.utils.get(ctx.guild.roles, name=self.member_role_name)
            gm_role = discord.utils.get(ctx.guild.roles, name=self.gm_role_name)
            await u.remove_roles(member_role, gm_role, reason='Requested to leave group.')
            members = member_role.members
            gms = gm_role.members
            if len(gms) == 0 and len(members) > 0:
              members[0].add_roles(gm_role)

        @group.group(
            name='gm'
        )
        async def gm_group(ctx):
            if ctx.invoked_subcommand is None:
                await ctx.send(f'Invalid `{ctx.command.qualified_name}` command passed...')

        @gm_group.command(
            name='add'
        )
        # @commands.check_any(
        #     commands.has_role(self.gm_role_id),
        #     commands.has_permissions(administrator=True)
        # )
        async def add_gm(ctx, u: discord.Member = None):
            if u is None:
                raise commands.BadArgumentError(message='No user provided.')
            member_role = discord.utils.get(ctx.guild.roles, name=self.member_role)
            gm_role = discord.utils.get(ctx.guild.roles, name=self.gm_role)
            await u.add_roles(member_role, gm_role, reason='Made GM of group.')

        @gm_group.command(
            name='resign'
        )
        # @commands.has_role(self.gm_role_id)
        async def resign_gm(ctx):
            u = ctx.author
            member_role = discord.utils.get(ctx.guild.roles, name=self.member_role)
            gm_role = discord.utils.get(ctx.guild.roles, name=self.gm_role)
            await u.remove_roles(gm_role, reason='Resigned as GM of group.')
            members = member_role.members
            gms = gm_role.members
            if len(gms) == 0 and len(members) > 0:
              members[0].add_roles(gm_role)

    return Cog
