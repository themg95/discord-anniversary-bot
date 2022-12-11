import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from yaml import load, CLoader as Loader

intents = discord.Intents.default()
intents.members = True  # Don't forget to enable the server members intent!
client = commands.Bot(intents=intents, command_prefix="")

with open("config.yaml") as f:
    config = load(f, Loader)

sent_members = []
last_reset = datetime.now()


@client.event
async def on_ready():
    global server
    global logging_channel
    print(f"Logged in as {client.user.name}")
    server = client.get_guild(config["server_id"])
    logging_channel = client.get_channel(config["logging_channel_id"])

    check.start()


async def format_message(message, user, year):
    formats = {
        "user": user,
        "year": year
    }

    for key in formats.keys():
        message = message.replace(f"{{{key}}}", formats[key])

    return message


@tasks.loop(seconds=config["check_interval"]["seconds"],
            minutes=config["check_interval"]["minutes"],
            hours=config["check_interval"]["hours"])
async def check():
    global sent_members
    global last_reset
    current_date = datetime.today().strftime("%d/%m")
    current_year = datetime.today().year
    for member in server.members:
        if member in sent_members:
            continue
        join_date = member.joined_at.strftime("%d/%m")
        if join_date == current_date:
            year = current_year - member.joined_at.year
            if year == 0:
                continue
            sent_members.append(member)

            if config["logging_message"]:
                formatted_message = await format_message(config["logging_message"], member.mention, str(year))
                await logging_channel.send(formatted_message)
            try:
                if config["private_message"]:
                    formatted_message = await format_message(config["private_message"], member.mention, str(year))
                    await member.send(formatted_message)
            except Exception as e:
                await logging_channel.send(f"Failed to send {member.mention} a private message.\nError: {e}")
    if datetime.now() - last_reset >= timedelta(days=1):
        sent_members = []
        last_reset = datetime.now()


@check.before_loop
async def before_check():
    await client.wait_until_ready()


client.run(config["token"])
