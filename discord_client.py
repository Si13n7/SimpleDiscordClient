#!/usr/bin/env python3


import discord
from discord.ext import commands
import asyncio
import datetime
import json
import os
import sys


# -------------------------------------------------- #
#                   Global Classes                   #
# -------------------------------------------------- #

class Config:
    def __init__(self):
        self.config = {
            'application': {
                'token': '',
                'game': '',
                'status': 'dnd',
                'afk': True
            },
            'activity': {
                'channel_id': '',
                'enabled': False
            },
            'command': {
                'prefix': '!'
            }
        }
        self.load('/etc/discord-client/')
        self.load(os.path.expanduser('~') + '/.config/discord-client/')
        self.load(os.path.dirname(os.path.realpath(__file__)))

    def get(self, key, default=None):
        return self.config.get(key, default)

    def load(self, path):
        if not path.endswith('/'):
            path += '/'
        path += 'config.json'

        try:
            with open(path) as file:
                self._update(self.config, json.load(file))
        except FileNotFoundError:
            pass
        except ValueError as error:
            print('Warning: {0} ({1})'.format(error, path), file=sys.stderr)

    def _update(self, old_dict, new_dict):
        for key, value in new_dict.items():
            if key in old_dict and isinstance(old_dict[key], dict) and isinstance(value, dict):
                self._update(old_dict[key], value)
            else:
                old_dict[key] = value


# -------------------------------------------------- #
#                   Global Vars                      #
# -------------------------------------------------- #

config = Config()

application = config.get('application')
activity = config.get('activity')
command = config.get('command')

cmd_prefix = command['prefix']
if cmd_prefix is None:
    cmd_prefix = '!'
client = commands.Bot(command_prefix=cmd_prefix)


# -------------------------------------------------- #
#                   Global Methods                   #
# -------------------------------------------------- #

async def log_activity():
    channel_id = activity['channel_id']
    if not len(channel_id) > 0:
        print("Activity log is disabled!")
        print("The channel ID can not be empty.")
        return

    voice_states = {}
    while not client.is_closed:
        for member in client.get_all_members():
            if member.id == client.user.id:
                continue

            if member.id not in voice_states:
                voice_states[member.id] = member.voice_channel
                continue

            if voice_states[member.id] != member.voice_channel:
                if member.voice_channel is None:
                    channel = voice_states[member.id]
                    color = 0xff0000
                    text = "Left"
                else:
                    channel = member.voice_channel
                    color = 0x00ff00
                    text = "Joined"
                embed = discord.Embed(title="{}#{}:".format(member.name, member.discriminator),
                                      description="{} voice channel #{}".format(text, channel),
                                      colour=color)
                embed.add_field(name="Timestamp:", value=str(datetime.datetime.now()))
                embed.set_thumbnail(url=member.avatar_url)
                await client.send_message(destination=client.get_channel(channel_id), embed=embed)

                voice_states[member.id] = member.voice_channel
        await asyncio.sleep(0.25)


@client.event
async def on_ready():
    game = application['game']
    status = application['status']
    afk = application['afk']
    if len(game) > 0 or len(status) > 0:
        await client.change_presence(game=discord.Game(name=str(game)), status=discord.Status(str(status)), afk=afk)
    print("Discord client (v{}) has been started!".format(discord.__version__))


@client.command(pass_context=True)
async def userinfo(ctx, user: discord.Member):
    embed = discord.Embed(colour=0x00ffff)
    embed.add_field(name="Name:", value="{}#{}:".format(user.name, user.discriminator), inline=True)
    if user.nick is not None:
        embed.add_field(name="Nickname (#{}):".format(ctx.message.server.name), value=user.nick, inline=True)
    embed.add_field(name="Identifier:", value=user.id, inline=True)
    embed.add_field(name="Status:", value=user.status, inline=True)
    if user.voice_channel is not None:
        embed.add_field(name="Voice Channel:", value=user.voice_channel)
    embed.add_field(name="Highest Role:",  value=user.top_role)
    embed.add_field(name="Joined Server:", value=user.joined_at)
    embed.set_thumbnail(url=user.avatar_url)
    await client.say(embed=embed)


# -------------------------------------------------- #
#                     Main Call                      #
# -------------------------------------------------- #

def main():
    if activity['enabled']:
        client.loop.create_task(log_activity())

    token = application['token']
    if len(token) > 0:
        client.run(str(token))
    else:
        print("Discord client not started!")
        print("The application token can not be empty!")
        sys.exit(1)


if __name__ == '__main__':
    main()
