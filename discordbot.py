import discord
import json
from discord.ext import commands
import config
import random

description = '''An example bot to showcase the discord.ext.commands extension
module.

There are a number of utility commands being showcased here.'''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', description=description, intents=intents, activity=discord.Game("bot")) # botをプレイ中)
#intents = discord.Intents.all()
#client = discord.Client(intents=intents)

# Bot起動時に呼び出される関数
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


@bot.command()
async def add(ctx, left: int, right: int):
    """Adds two numbers together."""
    await ctx.send(left + right)

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
        f = open("data.json", 'r')

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
                if(v['diff']!="11" or v['diff']!="11+"):
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
                if(v['diff']!="11" or v['diff']!="11+" or v['diff']!="12"):
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
                if(v['diff']!="11" or v['diff']!="11+" or v['diff']!="12" or v['diff']!="12+"):
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
                if(v['diff']!="11" or v['diff']!="11+" or v['diff']!="12" or v['diff']!="12+" or v['diff']!="13"):
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
                if(v['diff']!="15" or v['diff']!="15+"):
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
                if(v['diff']!="14+" or v['diff']!="15" or v['diff']!="15+"):
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
                #u2.append(v['diff'])
                #u3.append(v['data'][0])
                #u4.append(v['data'][1])
                #u5.append(v['data'][2])
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

bot.run(config.DISCORD_TOKEN)
'''
@client.event
async def on_ready():
    print("Ready!")

# メッセージの検知
@client.event
async def on_message(message):
    # 自身が送信したメッセージには反応しない
    if message.author == client.user:
        return

    # ユーザーからのメンションを受け取った場合、あらかじめ用意された配列からランダムに返信を返す
    if client.user in message.mentions:

        ansewr_list = ["さすがですね！","知らなかったです！","すごいですね！","センスが違いますね！","そうなんですか？"]
        answer = random.choice(ansewr_list)
        print(answer)
        await message.channel.send(answer)

# Bot起動
client.run(config.DISCORD_TOKEN)
'''
