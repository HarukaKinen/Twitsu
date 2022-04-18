import discord
import re
import os
import asyncio
from yt_dlp import YoutubeDL

from discord.ext import commands

from bilibili_api import sync, video_uploader, Credential

from twitchAPI import Twitch

from Cogs.settings import (VERSION, TWITCH_APP_ID, TWITCH_APP_SECRET, BILI_JCT, BILI_SESSDATA)

twitch = Twitch(TWITCH_APP_ID, TWITCH_APP_SECRET)

credential = Credential(sessdata=BILI_SESSDATA, bili_jct=BILI_JCT)


class dl_logger(object):
    def debug(self, msg):
        print(f'Debug: {msg}')
        # pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(f'Error: {msg}')


options = {
    'forcethumbnail': False,
    'forcetitle': False,
    'forcedescription': False,
    'outtmpl': u'Videos/%(id)s.%(ext)s',
}


class Twitch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    '''
    {
        "copyright": "int, 投稿类型。1 自制，2 转载。",
        "source": "str, 视频来源。投稿类型为转载时注明来源，为原创时为空。",
        "desc": "str, 视频简介。",
        "desc_format_id": 0,
        "dynamic": "str, 动态信息。",
        "mission_id": "int, 参加活动 ID，若不参加不要提供该项",
        "interactive": 0,
        "open_elec": "int, 是否展示充电信息。1 为是，0 为否。",
        "no_reprint": "int, 显示未经作者授权禁止转载，仅当为原创视频时有效。1 为启用，0 为关闭。",
        "subtitles": {
            "lan": "str: 字幕投稿语言，不清楚作用请将该项设置为空",
            "open": "int: 是否启用字幕投稿，1 or 0"
        },
        "tag": "str, 视频标签。使用英文半角逗号分隔的标签组。示例：标签 1, 标签 2, 标签 3",
        "tid": "int, 分区 ID。可以使用 channel 模块进行查询。",
        "title": "str: 视频标题",
        "up_close_danmaku": "bool, 是否关闭弹幕。",
        "up_close_reply": "bool, 是否关闭评论。",
        "dtime": "int?: 可选，定时发布时间戳（秒）"
    }
    '''

    @commands.command()
    async def t(self, ctx, msg=None, match=None, stage=None, team1=None, team2=None):
        if msg is not None:
            # get id in msg
            video_url = "https://www.twitch.tv/videos/" + \
                re.findall('\d+', msg)[0]

            # get video info
            with YoutubeDL(options) as dl:
                try:
                    info = dl.extract_info(
                        video_url, download=False)

                    # get information from data
                    _id = info['id']
                    title = info['title']
                    timestamp = info['timestamp']
                    channel = info['uploader']
                    channel_url = "https://www.twitch.tv/" + \
                        info['uploader_id']
                    thumbnail_url = info['thumbnail']
                    description = f"{match} {stage}: ({team1}) vs ({team2})" if match is not None else ""

                    # create embed
                    embed = discord.Embed(
                        description=description
                    )

                    embed.set_author(name=f"{title}", url=video_url)
                    embed.add_field(
                        name='VIDEO INFORMATION', value=f"**Chaneel**: [{channel}]({channel_url})\n**Published at**: <t:{timestamp}>", inline=False)
                    embed.set_image(url=thumbnail_url)
                    embed.set_footer(
                        text="Fetching video information Successfully")

                    # sned embed
                    msg = await ctx.channel.send(embed=embed)

                except Exception as e:
                    await ctx.channel.send(f"Fetch video infomation failed: {e}")
                    return

                try:
                    embed.set_footer(text="Downloading video...")
                    await msg.edit(embed=embed)
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, dl.download, [video_url])
                    embed.set_footer(text="Download video successfully")
                    await msg.edit(embed=embed)
                except Exception as e:
                    embed.set_footer(text=f"Download video failed: {e}")
                    await msg.edit(embed=embed)
                    return

                description = f"{description}\n{match if match is not None else ''}\n\nAuto upload by Twitsu v{VERSION}\ngithub.com/HarukaKinen/Twitsu"

                try:
                    meta = {
                        "copyright": 2,
                        "source": video_url,
                        "desc": description,
                        "desc_format_id": 0,
                        "dynamic": "",
                        "interactive": 0,
                        "open_elec": 1,
                        "no_reprint": 1,
                        "subtitles": {
                            "lan": "",
                            "open": 0
                        },
                        "tag": f"osu!, {match if match is not None else ''}",
                        "tid": 136,
                        "title": f"[osu!] {match} {stage}: ({team1}) vs ({team2})" if match is not None else title,
                        "up_close_danmaku": False,
                        "up_close_reply": False
                    }

                    page = video_uploader.VideoUploaderPage(path=f"Videos/{_id}.mp4", title=title[0:80], description=description)
                    uploader = video_uploader.VideoUploader([page], meta, credential)

                    @uploader.on("__ALL__")
                    async def event(data):
                        print(data)

                    embed.set_footer(text="Uploading video...")
                    await msg.edit(embed=embed)
                    await uploader.start()

                    embed.set_footer(text="Upload video successfully")
                    await msg.edit(embed=embed)
                except Exception as e:
                    error_msg = e.__str__()
                    embed.set_footer(text=f"Upload video failed: {error_msg}")
                    await msg.edit(embed=embed)
                    return

                remove_stuff(_id)

def remove_stuff(id):
    if os.path.exists(f"Videos/{id}.mp4"):
        os.remove(f"Videos/{id}.mp4")

def setup(bot):
    bot.add_cog(Twitch(bot))
