import os #os module used to read evs such as .env
import discord #the discord lib
from discord.ext import commands #grabs commands helpe from the lib's extension
from dotenv import load_dotenv # grabs a function that reads your .env file

load_dotenv() #READS .env file and loads DISCORD_TOKEN into the environment variables
TOKEN=os.getenv("DISCORD_TOKEN") #look up dicord token and store it in a variable TOKEN

intents=discord.Intents.default() # intents are permissions for what events discord sends your bot default is standard.

bot=commands.Bot(command_prefix="!",intents=intents) # this creates bots with intents as the permissions defined above.
#command_prefix is the prefix that will be used to call commands in the bot. For example, if you set it to "!", then you would call a command like "!ping". it's a placeholder.

@bot.event #decorator says handle event
async def setup_hook(): #runs once when bot starts
    await bot.tree.sync() #registery for all slash commands.
    #sync uploads list to discord,async defines a function that uses await and await is needed because syncing involves talking to discord over the internet.

@bot.event
async def on_ready(): #on ready when bot connected to discord.
    print(f"Logged in as {bot.user}")
#writes in terminal your bot whatever name works.

@bot.tree.command(name="ping", description="Check if the bot is alive")#slash command:name = user typing,description= what is shown in the menu.
async def ping(interaction:discord.Interaction): #run interaction when someone pings.
    await interaction.response.send_message(f"Pong!{round(bot.latency*1000)}ms")
    #it is the reply the bot says and bot.latency is the connection delay.

bot.run(TOKEN) #GO!
#Load the token from .env
#Create the bot with its permissions
#Register the handlers and the /ping command
#bot.run() connects, setup_hook syncs commands, on_ready prints the message
#Someone types /ping and your function replies