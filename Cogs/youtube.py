import nest_asyncio
nest_asyncio.apply()

from datetime import datetime
from io import BytesIO
from PIL import Image
import subprocess
import requests
import discord
import asyncio
import re
import os

from yt_dlp import YoutubeDL

from discord.ext import commands

from biliup.plugins.bili_webup import BiliBili, Data


from twitchAPI import Twitch

from Cogs.settings import (VERSION, TWITCH_APP_ID,
                           TWITCH_APP_SECRET, BILI_JCT, BILI_SESSDATA, BILI_ACCESS_TOKEN, BILI_DEDEUSERID, BILI_DEDEUSERID_CKMD5)

twitch = Twitch(TWITCH_APP_ID, TWITCH_APP_SECRET)

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
    'external_downloader' : 'aria2c',
}

game_mode = {
    0: "osu!",
    1: "osu!taiko",
    2: "osu!catch",
    3: "osu!mania",
}


class VideoInfo:
    def __init__(self):
        self.mode = None
        self.title = None


class Youtube(commands.Cog):
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

    async def parseargs(self, msg) -> VideoInfo:
        info = VideoInfo()
        i = 0
        for arg in msg:
            # 第一个参数是视频链接，不需要解析
            if i == 0:
                info.video = arg
            elif arg.startswith("-"):
                if arg == "-mode":
                    info.mode = int(msg[i + 1])
                elif arg == "-t":
                    info.title = msg[i + 1]
                else:
                    pass
            else:
                pass
            i += 1

        return info

    @commands.command()
    async def yt(self, ctx, *args):
        video_info = await self.parseargs(args)
        if video_info.video is not None:
            # get video info
            with YoutubeDL(options) as dl:
                try:
                    info = dl.extract_info(
                        video_info.video, download=False)

                    # write video info to format.json
                    with open("format.json", "w") as f:
                        f.write(str(info))

                    # get information from data
                    _id = info['id']
                    title = info['title']
                    channel = info['uploader']
                    channel_url = info['channel_url']

                    thumbnail_url = ""
                    if info['thumbnail'] is not None:
                        thumbnail_url = info['thumbnail']
                        thumbnail_path = f"Videos/{_id}.png"
                        response = requests.get(thumbnail_url)
                        response.raise_for_status()
                        image = Image.open(BytesIO(response.content))
                        image.save(thumbnail_path, format="PNG")
                        print(f"Thumbnail saved to {thumbnail_path}")

                    description = f"[{game_mode[video_info.mode]}] {video_info.title}"

                    # if description > 80 characters, drop error
                    if len(description) > 80:
                        await ctx.channel.send(f"Title is too long ({len(description)} current, 80 max)")
                        return

                    # create embed
                    embed = discord.Embed(
                        description=description
                    )

                    embed.set_author(name=f"{title}", url=video_info.video)
                    embed.add_field(
                        name='VIDEO INFORMATION', value=f"**Channel**: [{channel}]({channel_url})", inline=False)
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
                    await loop.run_in_executor(None, dl.download, [video_info.video])
                    file_name = dl.prepare_filename(info)
                    video_info.path = file_name
                    embed.set_footer(text="Download video successfully")
                    await msg.edit(embed=embed)
                except Exception as e:
                    embed.set_footer(text=f"Download video failed: {e}")
                    await msg.edit(embed=embed)
                    return

                try:
                    embed.set_footer(text="Uploading video...")

                    video = Data()

                    video.title = description

                    video.desc = info['description'] if info['description'] is not None else ""

                    tagList = []
                    tagList.append(game_mode[video_info.mode])

                    video.set_tag(tagList)

                    video.source = video_info.video
                    video.tid = 136

                    with BiliBili(video) as bili:
                        bili.login("bili.cookie", {
                            'cookies': {
                                'SESSDATA': BILI_SESSDATA,
                                'bili_jct': BILI_JCT,
                                'DedeUserID__ckMd5': BILI_DEDEUSERID_CKMD5,
                                'DedeUserID': BILI_DEDEUSERID
                            }, 'access_token': BILI_ACCESS_TOKEN})

                        video_part = bili.upload_file(
                            video_info.path, lines='AUTO', tasks=3)  # 上传视频，默认线路AUTO自动选择，线程数量3。
                        video.append(video_part)
                        if os.path.exists(thumbnail_path):
                            video.cover = bili.cover_up(f"{thumbnail_path}").replace('http:', '')
                        ret = bili.submit()
                        print(ret)

                    embed.set_footer(text="Upload video successfully")
                    await msg.edit(embed=embed)
                except Exception as e:
                    error_msg = e.__str__()
                    embed.set_footer(
                        text=f"Upload video failed: {error_msg}")
                    await msg.edit(embed=embed)
                    return

                remove_stuff(file_name)
                remove_stuff(thumbnail_path)
        else:
            await ctx.channel.send("Video link is required")


def remove_stuff(file_name):
    if os.path.exists(file_name):
        os.remove(file_name)


def setup(bot):
    bot.add_cog(Youtube(bot))
