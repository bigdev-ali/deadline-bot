import database
from datetime import datetime,timezone #understandable
from zoneinfo import ZoneInfo #zoneifo allows you to work with timezones.
from discord import app_commands #for slash commands with input parameters
import os #os module used to read evs such as .env
import discord #the discord lib
from discord.ext import commands #grabs commands helper from the lib's extension
from dotenv import load_dotenv # grabs a function that reads your .env file

load_dotenv() #READS .env file and loads DISCORD_TOKEN into the environment variables
TOKEN=os.getenv("DISCORD_TOKEN") #look up dicord token and store it in a variable TOKEN

intents=discord.Intents.default() # intents are permissions for what events discord sends your bot default is standard.

bot=commands.Bot(command_prefix="!",intents=intents) # this creates bots with intents as the permissions defined above.
#command_prefix is the prefix that will be used to call commands in the bot. For example, if you set it to "!", then you would call a command like "!ping". it's a placeholder.
LOCAL_TZ=ZoneInfo("Asia/Karachi") #this is the timezone for PAK, you can change it to your own timezone if you want.
@bot.event #decorator says handle event
async def setup_hook(): #runs once when bot starts
    await database.init_db() #makes connection with database
    await bot.tree.sync() #registery for all slash commands.
    #sync uploads list to discord,async defines a function that uses await and await is needed because syncing involves talking to discord over the internet.

@bot.event
async def on_ready(): #on ready when bot connected to discord.
    print(f"Logged in as {bot.user}")
#writes in terminal your bot whatever name works.

@bot.tree.command(name="ping", description="Check if the bot is alive")#slash command:name = user typing ping,description= what is shown in the menu.
async def ping(interaction:discord.Interaction): #run interaction when someone pings.
    await interaction.response.send_message(f"Pong!{round(bot.latency*1000)}ms")
    #it is the reply the bot says and bot.latency is the connection delay.

@bot.tree.command(name="add",description="Add a deadline") #slash command:name = user typing add,description= what is shown in the menu.
@app_commands.describe( #adds helper input box for the user
    title="What is due", 
    due="When is it due (YYYY-MM-DD HH:MM) in Pakistan time",
)
async def add(interaction:discord.Interaction,title:str,due:str): #runs interaction when someone does add.
    try:# when add interaction takes place reply take title and due as they are part of the input box
         local_dt = datetime.strptime(due, "%Y-%m-%d %H:%M").replace(tzinfo=LOCAL_TZ)
         #checks if user data format is correct or not and ,replace attaches PST to it
    except ValueError:
        await interaction.response.send_message(
            "Wrong date format. Use YYYY-MM-DD HH:MM, like 2026-10-25 23:59",
            ephemeral=True,
        ) #if user data format is wrong just write a message to the user.
        return

    utc_dt = local_dt.astimezone(timezone.utc) #convert UTC into local
    deadline_id = await database.add_deadline(
        interaction.user.id, title, utc_dt.isoformat() #stores as isotext because of no format
    ) #saves the deadline in the database and returns the id of the row that was created.
    await interaction.response.send_message(
        f"Saved **{title}** (ID {deadline_id}), due <t:{int(utc_dt.timestamp())}:F>"
        #outputs the message to the user with the title and id of the deadline and the due date in a human readable format.
    )
@bot.tree.command(name="list", description="Show your upcoming deadlines") #a slash command for list.
async def list_deadlines(interaction: discord.Interaction): #no input box so just interaction.
    rows = await database.get_deadlines(interaction.user.id) #rows store deadlines in DEADLINE table

    if not rows:
        await interaction.response.send_message(
            "No upcoming deadlines. Add one with /add", ephemeral=True
        ) #if no deadline reply with this
        return

    lines = []
    for deadline_id, title, due_at in rows:
        ts = int(datetime.fromisoformat(due_at).timestamp())
        lines.append(f"**{deadline_id}.** {title} - <t:{ts}:F> (<t:{ts}:R>)")
#else create an array add the deadline in a readable format and reply with it and join lines glues line together ephmeral is True to keep deadlines private.
    await interaction.response.send_message("\n".join(lines), ephemeral=True)
bot.run(TOKEN) #GO!
#Load the token from .env
#Create the bot with its permissions
#Register the handlers and the /ping command
#bot.run() connects, setup_hook syncs commands, on_ready prints the message
#Someone types /ping and your function replies
#User runs /add title:"OS assignment" due:"2026-10-25 23:59"
#We parse the text into a date (or reject it politely)
#We label it Pakistan time, then convert to UTC
#We save the row and get its ID
#We reply with a confirmation Discord formats for the viewer