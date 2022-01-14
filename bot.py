import asyncio

import discord
import youtube_dl
from discord.ext import commands
from youtube_dl import YoutubeDL

from constants import TOKEN, FFMPEG_OPTIONS, YDL_OPTIONS, JS_USERS, CHANNELS, DELETE_MESSAGES


class TheEyeBot(commands.Bot):
    def __init__(self, command_prefix):
        super().__init__(command_prefix=command_prefix)
        self.queue = {}

        def add_to_queue(guild: discord.Guild, url: str):
            if guild.id not in self.queue:
                self.queue[guild.id] = []
            self.queue[guild.id].append(url)

        async def play_from_yt(ctx: commands.Context, voice_client: discord.VoiceClient):
            with YoutubeDL(YDL_OPTIONS) as ydl:
                try:
                    if not (url := self.queue.get(voice_client.guild.id).pop(0)):
                        await self.get_command('d')()
                        return
                except Exception as e:
                    return

                try:
                    info = ydl.extract_info(url, download=False)
                except youtube_dl.DownloadError:
                    await ctx.send('No video for this url.')
                    await voice_client.disconnect()
                    return

                info_url = info['formats'][0]['url']
                source = await discord.FFmpegOpusAudio.from_probe(info_url, **FFMPEG_OPTIONS)
                voice_client.play(
                    source,
                    after=lambda e:
                    print(f'Player error: {e}') if e else asyncio.run(play_from_yt(ctx, voice_client))
                )

        @self.command(name='p')
        async def play_audio(ctx: commands.Context, url: str = None):
            if ctx.channel.id != CHANNELS['MUSIC']:
                await ctx.send('Send music-commands in music channel.')
                return

            if not url or not url.startswith('https://www.youtube.com/watch?v='):
                await ctx.send('You need to give me url, moron.')
                return

            if not ctx.author.voice:
                await ctx.send('You have to be in a voice channel, moron.')
                return

            channel: discord.VoiceChannel = ctx.author.voice.channel

            if not ctx.me.voice or ctx.me.voice.channel.id != channel.id:
                await channel.connect()

            server: discord.Guild = ctx.message.guild
            voice_client: discord.VoiceClient = discord.utils.get(self.voice_clients, guild=ctx.guild)

            add_to_queue(server, url)
            await ctx.reply('Video was added to queue.', mention_author=False)

            if not voice_client.is_playing():
                await play_from_yt(ctx, voice_client)

        @self.command(name='s')
        async def stop_music(ctx: commands.Context, skip_music=False):
            voice_client: discord.VoiceClient = discord.utils.get(self.voice_clients, guild=ctx.guild)
            if voice_client and voice_client.is_playing():
                voice_client.stop()
                if not skip_music:
                    self.queue.clear()
                    await ctx.send('Queue was cleaned and music was stopped.')

        @self.command(name='d')
        async def leave(ctx: commands.Context = None):
            try:
                await self.voice_clients[0].disconnect()
            except IndexError:
                pass

        @self.command()
        async def skip(ctx: commands.Context = None):
            await self.get_command('s')(ctx, True)
            voice_client: discord.VoiceClient = discord.utils.get(self.voice_clients, guild=ctx.guild)
            await play_from_yt(ctx, voice_client)

    async def log(self, text):
        log_channel = self.get_channel(CHANNELS['LOG'])
        await log_channel.send(text)

    async def close(self):
        await self.get_command('d')()
        await super().close()

    async def on_command_error(self, context, exception):
        await self.get_command('d')()

    async def on_ready(self):
        await self.log(f'{self.user.name} has connected to server!')

    async def on_message(self, message):
        if message.author.id in DELETE_MESSAGES.values():
            await self.log(
                f'|{message.channel}:{message.channel.id}|\n'
                f'Deleted message: "{message.author}[{message.author.id}]: {message.content}"')
            await message.delete()
            return

        if message.author.id != self.user.id:
            await self.log(f'|{message.channel}:{message.channel.id}|\n'
                           f'{message.author}[{message.author.id}]: {message.content}')

        await self.process_commands(message)

    async def on_voice_state_update(self, member, before, after):
        if before.channel != after.channel:
            if before.channel is None:
                await self.log(f'User {member} joined channel {after.channel}')
            elif after.channel is None:
                await self.log(f'User {member} left channel {before.channel}')
            else:
                await self.log(f'User {member} left channel {before.channel} and joined channel {after.channel}')

        if member.id in JS_USERS.values() and member.voice and member.voice.channel.id != CHANNELS['JS']:
            js_channel = self.get_channel(CHANNELS['JS'])
            await self.log(f'Moving user {member} to {js_channel}')
            await member.move_to(js_channel)


if __name__ == '__main__':
    bot = TheEyeBot(command_prefix='.')
    bot.run(TOKEN)
