import database
import logging
from datetime import datetime,timezone,timedelta #understandable and timedelta is basically change in time.
from zoneinfo import ZoneInfo #zoneifo allows you to work with timezones.
from discord import app_commands #for slash commands with input parameters
import os #os module used to read evs such as .env
import discord #the discord lib
from discord.ext import commands,tasks #grabs commands helper from the lib's extension and tasks is a helper for running background tasks like sending reminders.
from dotenv import load_dotenv # grabs a function that reads your .env file

load_dotenv() #READS .env file and loads DISCORD_TOKEN into the environment variables
logging.basicConfig( #creates logging once for the whole program
    level=logging.INFO, #only show INFO nothing serious
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s", #the format controls on each line looks on INFO -8 is space
)
log = logging.getLogger("deadline-bot") #creates a logger

TOKEN=os.getenv("DISCORD_TOKEN") #look up dicord token and store it in a variable TOKEN

intents=discord.Intents.default() # intents are permissions for what events discord sends your bot default is standard.

bot=commands.Bot(command_prefix="!",intents=intents) # this creates bots with intents as the permissions defined above.
#command_prefix is the prefix that will be used to call commands in the bot. For example, if you set it to "!", then you would call a command like "!ping". it's a placeholder.
LOCAL_TZ=ZoneInfo("Asia/Karachi") #this is the timezone for PAK, you can change it to your own timezone if you want.
@bot.event #decorator says handle event
async def setup_hook(): #runs once when bot starts
    check_reminders.start() #starts the background task that checks for reminders every minute
    await database.init_db() #makes connection with database
    await bot.tree.sync() #registery for all slash commands
    #sync uploads list to discord,async defines a function that uses await and await is needed because syncing involves talking to discord over the internet.

@bot.event
async def on_ready(): #on ready when bot connected to discord.
    # in on_ready
 log.info("Logged in as %s", bot.user) #INFO is used for a normal case and the %s is just seperate arguements used as a logging style.
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
    if utc_dt <= datetime.now(timezone.utc):
          await interaction.response.send_message(
            "That time is already in the past. Pick a future time.", #this checks if the user has entered a past data and rejects it automatically.
            ephemeral=True,
        )
          return
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
        ) #if no deadline reply with this and wait
        return

    embed = discord.Embed( 
    title="Your upcoming deadlines", 
    color=discord.Color.blurple(),
    #this creates an embedded title card with color blurple which means purple and blue this will show on the bar on the left
    )
    for deadline_id, title, due_at in rows[:25]:#this selects the first 25 rows because discord allows 25 fields max per embed and we display rows based on urgency so it wont matter anyways
        ts = int(datetime.fromisoformat(due_at).timestamp())
        embed.add_field(
            name=f"{deadline_id}. {title}",
            value=f"<t:{ts}:F> (<t:{ts}:R>)",
            inline=False, #stacks the field vertically else if True it would be side by side which would look messy
        ) #this addes one row with a bold heading
    embed.set_footer(text=f"{len(rows)} unfinished deadline(s)") # adds a small gray text at the bottom showing the real total

    await interaction.response.send_message(embed=embed, ephemeral=True)
    #this is how you send the embedded version and emphemeral keeps it private

@bot.tree.command(name="done", description="Mark a deadline as finished") #slash command for done.
@app_commands.rename(deadline_id="id") #REUSES id in deadlines as deadline_id in the input box for the user.
@app_commands.describe(deadline_id="The ID shown in /list") #the input box for the user
async def done(interaction: discord.Interaction, deadline_id: int):
    ok = await database.mark_done(deadline_id, interaction.user.id)
    if ok:
        await interaction.response.send_message(
            f"Nice, deadline {deadline_id} marked as done."
        )
    else:
        await interaction.response.send_message(
            "Couldn't find an unfinished deadline with that ID. Check /list.",
            ephemeral=True,
        )
#pretty self explanatory, if the deadline is found mark it as done otherwise reply with a message that it was not found.

@bot.tree.command(name="delete", description="Delete a deadline")
@app_commands.rename(deadline_id="id")
@app_commands.describe(deadline_id="The ID shown in /list")
async def delete(interaction: discord.Interaction, deadline_id: int):
    ok = await database.delete_deadline(deadline_id, interaction.user.id)
    if ok:
        await interaction.response.send_message(f"Deleted deadline {deadline_id}.")
    else:
        await interaction.response.send_message(
            "Couldn't find a deadline with that ID. Check /list.",
            ephemeral=True,
        )
#holds the same format as done, if the deadline is found delete it otherwise reply with a message that it was not found.

STAGE_COLORS={
    "24h":discord.Color.green(),
    "3h":discord.Color.orange(),
    "1h":discord.Color.red(),
}
#this is similar to FLAG_UPDATES the only difference is that it uses colors

@tasks.loop(minutes=1) #this is a decorator that runs the function below every minute.
async def check_reminders():
    now = datetime.now(timezone.utc) #TIME NOW IN UTC
    rows = await database.get_pending_deadlines()

    for deadline_id, user_id, title, due_at, r24, r3, r1 in rows:
        due = datetime.fromisoformat(due_at) #format the due date into a readable format
        left = due - now #time left for the deadline to be due

        if left <= timedelta(0):
            continue  # already overdue skip it

        if left <= timedelta(hours=1) and not r1:
            stage = "1h"
        elif left <= timedelta(hours=3) and not r3:
            stage = "3h"
        elif left <= timedelta(hours=24) and not r24:
            stage = "24h"
        else:
            continue

        ts = int(due.timestamp()) #ts represents the timestamp of the due date in seconds since epoch which is used to format the reminder message in a human-readable way.
        try:
            user = await bot.fetch_user(user_id)
            embed = discord.Embed(
            title="⏰ Deadline reminder",
            description=f"**{title}**", #the bold text under the title
            color=STAGE_COLORS[stage], #this works because stage is already set
            )
            embed.add_field(name="Due", value=f"<t:{ts}:F>", inline=False) #two fields and inline false you get the point
            embed.add_field(name="Time left", value=f"<t:{ts}:R>", inline=False)
            await user.send(embed=embed)
        except discord.Forbidden: #if user has closed DMs or blocked the bot, it will raise a discord.Forbidden exception. In that case, we catch the exception and print a message to the console indicating that we couldn't send a DM to the user.
            # in check_reminders, the Forbidden case
         log.warning("Can't DM user %s, their DMs are closed", user_id) # Warning means something is off
        except Exception as e:
           # in check_reminders, the generic exception case
            log.error("Reminder failed for deadline %s: %s", deadline_id, e) #%s for seperate arguements and ERROR represents an extreme case as something broke
            continue

        await database.mark_reminded(deadline_id, stage)
#switches flags only when reminder is sent here

@check_reminders.before_loop
async def before_check_reminders():
    await bot.wait_until_ready()
#makes sure the bot is ready before starting the loop so that we don't try to send reminders before the bot is connected to discord
@bot.tree.error #works on error handling and runs it in one place
async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
): #error means the exception which was raised here
    name = interaction.command.name if interaction.command else "unknown"
    log.error("Error in /%s: %s", name, error, exc_info=error)
    #logs error in command name and identifies error

    msg = "Something went wrong on my end. Try again in a bit."
    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
        #if the response is done send this followup message otherwise just send the message and ephmeral is true to keep things private.
    else:
        await interaction.response.send_message(msg, ephemeral=True)

bot.run(TOKEN, log_handler=None) #GO! log handler=none says that we designed our own log handler use that

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
#Now update and deleted has also been added to the bot, so you can mark deadlines as done or delete them.
#It can also check past dates and reject them, and it can also check for wrong date formats and reject them as well.
#Added a background checker as well with tasks and reminder flags 1hr,3hr and 24 hour auto DM pings