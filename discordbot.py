import discord
import asyncio
import json
from discord.ext import commands
import config
import random
import datetime
from flask import Flask
from threading import Thread
import os

description = '''An example bot to showcase the discord.ext.commands extension
module.

There are a number of utility commands being showcased here.'''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', description=description, intents=intents, activity=discord.Game("!omi")) # botをプレイ中)
#intents = discord.Intents.all()
#client = discord.Client(command_prefix='!',intents=intents)

# Bot起動時に呼び出される関数
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    
@bot.command()
async def update(ctx, now: str):
    """Inform the date"""
    if(now=="now"):
        async for message in ctx.channel.history(limit=2):
            if bot.user != ctx.author:
                await message.delete(delay=1.2)
        dt_now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
        await ctx.send(f"<@&1272147130743783496>{dt_now.year}年{dt_now.month}月{dt_now.day}日{dt_now.hour}時{dt_now.minute}分{dt_now.second}秒までの更新分を反映しました\n")
    else:
        async for message in ctx.channel.history(limit=1):
            if bot.user != ctx.author:
                await message.delete(delay=1.2)
        await ctx.send(f"<@&1272147130743783496>{now}まで更新したよ！")

@bot.command()
async def add(ctx, left: int, right: int):
    """Adds two numbers together."""
    await ctx.send(left + right)

@bot.command()
async def etatoto(ctx, flag: str):
    """send url"""
    th_id = 1350530010058068038
    if(flag==config.SECRET):
        #await ctx.send("ok")
        thread = bot.get_channel(th_id) #get_channel(id):Returns a channel or thread with the given ID.
        await thread.send(ctx.author.mention)
        

@bot.command()
async def roll(ctx, dice: str):
    """Rolls a dice in NdN format."""
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        await ctx.send('Format has to be in NdN!')
        return

    result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
    await ctx.send(result)

@bot.command()
async def omi(ctx, game: str, diff: str, op: str, op2: str):
    """Randomly select 3 songs from that game"""
    if(game=='c'):
        f = open("data_c.json", 'r')

        json_data = json.load(f)
        u=[]
        #u2=[]
        #u3=[]
        #u4=[]
        #u5=[]
        for v in json_data.values():
            if(op=="s" and v['diff']==diff):
                if(op2=="or" and v['data'][1]=="ORI"):
                    u.append(v)
                elif(op2=="ge" and v['data'][1]=="撃舞"):
                    u.append(v)
                elif(op2=="ir" and v['data'][1]=="イロ"):
                    u.append(v)
                elif(op2=="va" and v['data'][1]=="VAR"):
                    u.append(v)
                elif(op2=="to" and v['data'][1]=="東方"):
                    u.append(v)
                elif(op2=="ni" and v['data'][1]=="nico"):
                    u.append(v)
                elif(op2=="pa" and v['data'][1]=="P&A"):
                    u.append(v)
                elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="11"):
                if(op2=="or" and v['data'][1]=="ORI"):
                    u.append(v)
                elif(op2=="ge" and v['data'][1]=="撃舞"):
                    u.append(v)
                elif(op2=="ir" and v['data'][1]=="イロ"):
                    u.append(v)
                elif(op2=="va" and v['data'][1]=="VAR"):
                    u.append(v)
                elif(op2=="to" and v['data'][1]=="東方"):
                    u.append(v)
                elif(op2=="ni" and v['data'][1]=="nico"):
                    u.append(v)
                elif(op2=="pa" and v['data'][1]=="P&A"):
                    u.append(v)
                elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="11+"):
                if(v['diff']!="11"):
                    if(op2=="or" and v['data'][1]=="ORI"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="撃舞"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VAR"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="nico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="P&A"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="12"):
                if(v['diff']!="11" and v['diff']!="11+"):
                    if(op2=="or" and v['data'][1]=="ORI"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="撃舞"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VAR"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="nico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="P&A"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="12+"):
                if(v['diff']!="11" and v['diff']!="11+" and v['diff']!="12"):
                    if(op2=="or" and v['data'][1]=="ORI"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="撃舞"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VAR"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="nico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="P&A"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="13"):
                if(v['diff']!="11" and v['diff']!="11+" and v['diff']!="12" and v['diff']!="12+"):
                    if(op2=="or" and v['data'][1]=="ORI"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="撃舞"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VAR"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="nico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="P&A"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="13+"):
                if(v['diff']!="11" and v['diff']!="11+" and v['diff']!="12" and v['diff']!="12+" and v['diff']!="13"):
                    if(op2=="or" and v['data'][1]=="ORI"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="撃舞"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VAR"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="nico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="P&A"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="14"):
                if(v['diff']=="14" or v['diff']=="14+" or v['diff']=="15" or v['diff']=="15+"):
                    if(op2=="or" and v['data'][1]=="ORI"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="撃舞"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VAR"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="nico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="P&A"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="14+"):
                if(v['diff']=="14+" or v['diff']=="15" or v['diff']=="15+"):
                    if(op2=="or" and v['data'][1]=="ORI"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="撃舞"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VAR"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="nico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="P&A"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="15"):
                if(v['diff']=="15" or v['diff']=="15+"):
                    if(op2=="or" and v['data'][1]=="ORI"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="撃舞"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VAR"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="nico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="P&A"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="15+"):
                if(v['diff']=="15+"):
                    if(op2=="or" and v['data'][1]=="ORI"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="撃舞"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VAR"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="nico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="P&A"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="15+"):
                if(op2=="or" and v['data'][1]=="ORI"):
                    u.append(v)
                elif(op2=="ge" and v['data'][1]=="撃舞"):
                    u.append(v)
                elif(op2=="ir" and v['data'][1]=="イロ"):
                    u.append(v)
                elif(op2=="va" and v['data'][1]=="VAR"):
                    u.append(v)
                elif(op2=="to" and v['data'][1]=="東方"):
                    u.append(v)
                elif(op2=="ni" and v['data'][1]=="nico"):
                    u.append(v)
                elif(op2=="pa" and v['data'][1]=="P&A"):
                    u.append(v)
                elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="15"):
                if(v['diff']!="15+"):
                    if(op2=="or" and v['data'][1]=="ORI"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="撃舞"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VAR"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="nico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="P&A"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="14+"):
                if(v['diff']!="15" and v['diff']!="15+"):
                    if(op2=="or" and v['data'][1]=="ORI"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="撃舞"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VAR"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="nico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="P&A"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="14"):
                if(v['diff']!="14+" and v['diff']!="15" and v['diff']!="15+"):
                    if(op2=="or" and v['data'][1]=="ORI"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="撃舞"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VAR"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="nico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="P&A"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="13+"):
                if(v['diff']=="11" or v['diff']=="11+" or v['diff']=="12" or v['diff']=="12+" or v['diff']=="13" or v['diff']=="13+"):
                    if(op2=="or" and v['data'][1]=="ORI"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="撃舞"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VAR"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="nico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="P&A"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="13"):
                if(v['diff']=="11" or v['diff']=="11+" or v['diff']=="12" or v['diff']=="12+" or v['diff']=="13"):
                    if(op2=="or" and v['data'][1]=="ORI"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="撃舞"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VAR"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="nico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="P&A"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="12+"):
                if(v['diff']=="11" or v['diff']=="11+" or v['diff']=="12" or v['diff']=="12+"):
                    if(op2=="or" and v['data'][1]=="ORI"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="撃舞"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VAR"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="nico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="P&A"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="12"):
                if(v['diff']=="11" or v['diff']=="11+" or v['diff']=="12"):
                    if(op2=="or" and v['data'][1]=="ORI"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="撃舞"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VAR"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="nico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="P&A"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="11+"):
                if(v['diff']=="11" or v['diff']=="11+"):
                    if(op2=="or" and v['data'][1]=="ORI"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="撃舞"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VAR"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="nico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="P&A"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="11"):
                if(v['diff']=="11"):
                    if(op2=="or" and v['data'][1]=="ORI"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="撃舞"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VAR"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="nico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="P&A"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
    elif(game=='o'):
        f = open("data_o.json", 'r')

        json_data = json.load(f)
        u=[]
        for v in json_data.values():
            if(op=="s" and v['diff']==diff):
                if(op2=="on" and v['data'][1]=="オンゲキ"):
                    u.append(v)
                elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                    u.append(v)
                elif(op2=="va" and v['data'][1]=="VARIETY"):
                    u.append(v)
                elif(op2=="to" and v['data'][1]=="東方Project"):
                    u.append(v)
                elif(op2=="ni" and v['data'][1]=="niconico"):
                    u.append(v)
                elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                    u.append(v)
                elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                    u.append(v)
                elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="11"):
                if(op2=="on" and v['data'][1]=="オンゲキ"):
                    u.append(v)
                elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                    u.append(v)
                elif(op2=="va" and v['data'][1]=="VARIETY"):
                    u.append(v)
                elif(op2=="to" and v['data'][1]=="東方Project"):
                    u.append(v)
                elif(op2=="ni" and v['data'][1]=="niconico"):
                    u.append(v)
                elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                    u.append(v)
                elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                    u.append(v)
                elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="11+"):
                if(v['diff']!="11"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="12"):
                if(v['diff']!="11" and v['diff']!="11+"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="12+"):
                if(v['diff']!="11" and v['diff']!="11+" and v['diff']!="12"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="13"):
                if(v['diff']!="11" and v['diff']!="11+" and v['diff']!="12" and v['diff']!="12+"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="13+"):
                if(v['diff']!="11" and v['diff']!="11+" and v['diff']!="12" and v['diff']!="12+" and v['diff']!="13"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="14"):
                if(v['diff']!="11" and v['diff']!="11+" and v['diff']!="12" and v['diff']!="12+" and v['diff']!="13" and v['diff']!="13+"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="14+"):
                if(v['diff']!="11" and v['diff']!="11+" and v['diff']!="12" and v['diff']!="12+" and v['diff']!="13" and v['diff']!="13+" and v['diff']!="14"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="15"):
                if(v['diff']=="15" or v['diff']=="15+"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="15+"):
                if(v['diff']=="15+"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="15+"):
                if(op2=="on" and v['data'][1]=="オンゲキ"):
                    u.append(v)
                elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                    u.append(v)
                elif(op2=="va" and v['data'][1]=="VARIETY"):
                    u.append(v)
                elif(op2=="to" and v['data'][1]=="東方Project"):
                    u.append(v)
                elif(op2=="ni" and v['data'][1]=="niconico"):
                    u.append(v)
                elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                    u.append(v)
                elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                    u.append(v)
                elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="15"):
                if(v['diff']!="15+"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="14+"):
                if(v['diff']!="15" and v['diff']!="15+"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="14"):
                if(v['diff']!="14+" and v['diff']!="15" and v['diff']!="15+"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="13+"):
                if(v['diff']=="11" or v['diff']=="11+" or v['diff']=="12" or v['diff']=="12+" or v['diff']=="13" or v['diff']=="13+"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="13"):
                if(v['diff']=="11" or v['diff']=="11+" or v['diff']=="12" or v['diff']=="12+" or v['diff']=="13"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="12+"):
                if(v['diff']=="11" or v['diff']=="11+" or v['diff']=="12" or v['diff']=="12+"):
                    if(op2=="or" and v['data'][1]=="ORI"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="撃舞"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VAR"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="nico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="P&A"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="12"):
                if(v['diff']=="11" or v['diff']=="11+" or v['diff']=="12"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="11+"):
                if(v['diff']=="11" or v['diff']=="11+"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="11"):
                if(v['diff']=="11"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
    await ctx.send(f"本日の{ctx.author.mention}の課題曲\n")
    for a in range(3):
        answer = random.choice(u)
        await ctx.send("{0}\t Title: {1}\t Difficulty: {2}\t Level: {3}\t Genre: {4}\t CN: {5}\n".format(a+1,answer['name'],answer['diff'],answer['data'][0],answer['data'][1],answer['data'][2]))
        '''
        for a in range(3):
            answer = random.choice(u)
            a1 = answer.values['name']
            await ctx.send(a1)
            #print(answer['name'],end="\t")
            for i in range(3):
                a2 = answer.values['data'][i]
                await ctx.send(a2)
                #print("{}".format(answer['data'][i]),end="\t")
            print("\n")
        '''

@bot.command()
async def joined(ctx, member: discord.Member):
    """Says when a member joined."""
    await ctx.send(f'{member.name} joined {discord.utils.format_dt(member.joined_at)}')

@bot.group()
async def cool(ctx):
    """Says if a user is cool.

    In reality this just checks if a subcommand is being invoked.
    """
    if ctx.invoked_subcommand is None:
        await ctx.send(f'No, {ctx.subcommand_passed} is not cool')

@cool.command(name='bot')
async def _bot(ctx):
    """Is the bot cool?"""
    await ctx.send('Yes, the bot is cool.')

# Flaskサーバーをセットアップ
app = Flask('')

@app.route('/')
def home():
    # Renderからのアクセスに対して応答を返す
    return "I'm alive"

def run():
    # Webサーバーを起動する
    # hostを0.0.0.0に、portを環境変数PORTから取得（Renderが自動で設定）
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    # RenderのURLを環境変数から取得（なければ何もしない）
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        while True:
            try:
                requests.get(render_url)
                print("Sent keep-alive ping.")
            except Exception as e:
                print(f"Failed to send keep-alive ping: {e}")
            time.sleep(14 * 60) # 14分ごとにスリープ

def start_bot():
    bot.run(config.DISCORD_TOKEN)

if __name__ == "__main__":
    # Webサーバーを別のスレッドで起動
    server_thread = Thread(target=run)
    server_thread.start()
    ping_thread = Thread(target=keep_alive)
    ping_thread.start()
    
    # メインスレッドでBotを起動
    start_bot()