from discord.ext import commands
import requests


class Main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        r = requests.get("http://ip-api.com/json/")
        data = r.json()
        country = data['country']
        # regionName = data['regionName']
        city = data['city']
        isp = data['isp']

        await ctx.send(f'**{round(self.bot.latency*1000)}** ms on **{country}** server by **{isp}** in **{city}**')

def setup(bot):
    bot.add_cog(Main(bot))
