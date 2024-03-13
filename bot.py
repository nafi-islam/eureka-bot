import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone

with open('secrets.txt', 'r') as token_file:
    BOT_TOKEN = token_file.read().strip()

mod_role_id = None  # Initially, no mod role is set
allowed_channel_id = None  # Initially, allow all channels

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
bot.remove_command('help')  # Remove the default 'help' command

weeklyData = {}
monthlyData = {}
totalReferrals = {}  # Tracks the total number of referrals made by each user
referrals = {}  # Maps referrer IDs to a list of referred user IDs

# Design Consideration:
# Keeping totalReferrals even though can parse referrals to get the same information. Makes information more accessible for scaling.

"""
    Base Case: totalReferrals = {}
    In Action: totalReferrals = {"12345" : 3}
 
    * Previouss Structure * 
    Base Case: referrals = {}
    referrals = {
    "12345": "67890",  # User 12345 was referred by user 67890
    "22222": "67890"   # User 22222 was also referred by user 67890
    }
    
    * New / Current Structure *
    referrals = {
    "67890": ["12345", "22222"]  # User 67890 referred users 12345 and 22222
    }

    referrals["67890"].append("33333")

    referrals = {
    "67890": ["12345", "22222", "33333"]
    }

    Benefits:
    - Efficiency in Tracking Multiple Referrals
    - Ease of Access and Management
    - Reduced Complexity 
"""

@bot.event
async def on_ready():
    global bot_avatar_url  # Global variable to store the bot's avatar URL
    print("Bot is ready")
    bot_avatar_url = str(bot.user.avatar.url) if bot.user.avatar else None  # Store the bot's avatar URL
    channel = bot.get_channel(allowed_channel_id)
    if channel:
        await channel.send("Bot is ready")

# Need the * arg so that the command can take in a string for "default" case
@bot.command(name="set-channel")
async def set_channel(ctx, *, channel_name=None):
    # Check if the user has the set-mod role or administrator permissions
    if not (ctx.author.guild_permissions.administrator or (mod_role_id and any(role.id == mod_role_id for role in ctx.author.roles))):
        embed = discord.Embed(
            title="Permission Denied",
            description=f"{ctx.author.mention}, you do not have permission to use the set channel command.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    global allowed_channel_id
    embed = discord.Embed()

    if channel_name == 'default':
        allowed_channel_id = None
        embed.description = "The bot is now set to respond in all channels."
        embed.color = discord.Color.green()
    elif channel_name:
        # Try to find the channel by name or mention
        channel = discord.utils.get(ctx.guild.channels, name=channel_name.strip('#'))
        if channel and isinstance(channel, discord.TextChannel):
            allowed_channel_id = channel.id
            embed.description = f"The bot is now set to respond in the #{channel.name} channel."
            embed.color = discord.Color.green()
        else:
            embed.description = "Channel not found. Please make sure you've entered the correct channel name."
            embed.color = discord.Color.red()
    else:
        embed.description = "Please provide a channel name or 'default' to set the bot's active channel."
        embed.color = discord.Color.red()

    await ctx.send(embed=embed)

# Only need if admin has access to set_channel command but mod has access too, so do the check in the command itself
# Error handler for set_channel command
@set_channel.error
async def set_channel_error(ctx, error):
    if not is_allowed_channel(ctx):
        return  # Ignore if the error response is not in the allowed channel
    
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="Permission Denied",
            description=f"{ctx.author.mention}, you do not have permission to use the set_channel command.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

def is_allowed_channel(ctx):
    # Function to check if the bot is allowed to operate in the channel
    return allowed_channel_id is None or ctx.channel.id == allowed_channel_id

# Function to calculate account age
def calculate_age(author):
    past = author.created_at
    present = datetime.now(timezone.utc)
    ageDelta = present - past
    dayAge = ageDelta.days
    return dayAge

@bot.command()
async def age(ctx):
    if not is_allowed_channel(ctx):
        return  # Ignore if the command is not in the allowed channel

    dayAge = calculate_age(ctx.author)
    embed = discord.Embed(title="Account Age", 
                          description=f"Your account is {dayAge} days old.", 
                          color=discord.Color.blue())  # Blue color
    embed.set_thumbnail(url=bot_avatar_url)  # Set the bot's avatar as the thumbnail
    await ctx.send(embed=embed)


@bot.command(name="referred-by")
async def referredBy(ctx, referred: discord.User):
    if not is_allowed_channel(ctx):
        return  # Ignore if the command is not in the allowed channel

    referrer_id = str(referred.id)
    referred_id = str(ctx.author.id)
    dayAge = calculate_age(ctx.author)

    # Embed for error messages
    embed = discord.Embed()
    embed.color = discord.Color.red()  # Default color for error messages

    if dayAge <= 120:
        embed.description = f"{ctx.author.mention}, sorry, your account is not old enough for a referral. You can check your account age with `!age`."
        await ctx.send(embed=embed)
        return

    # Prevent self-referral
    if referrer_id == referred_id:
        embed.description = f"{ctx.author.mention}, you cannot refer yourself!"
        await ctx.send(embed=embed)
        return

    # Check if the referred user has already been referred by someone else
    if any(referred_id in referred_list for referred_list in referrals.values()):
        embed.description = f"{ctx.author.mention}, you have already been referred to the server!"
        await ctx.send(embed=embed)
        return

    # Check for swapping referrals, referred
    if referred_id in referrals and referrer_id in referrals[referred_id]:
        embed.description = f"{ctx.author.mention}, you cannot be referred by someone who you have referred!"
        await ctx.send(embed=embed)
        return

    # Check for circular referral, referrer
    if referrer_id in referrals and referred_id in referrals[referrer_id]:
        embed.description = f"{ctx.author.mention}, you cannot refer this user because they have already referred you!"
        await ctx.send(embed=embed)
        return
    
    # Swap checks LATER and Circular checks NOW. Similar functionality but during different times

    # Add or update the referral
    if referrer_id not in referrals:
        referrals[referrer_id] = [referred_id]
    elif referred_id not in referrals[referrer_id]:
        referrals[referrer_id].append(referred_id)
    else:
        embed.description = f"{ctx.author.mention}, this user has already referred you!"
        await ctx.send(embed=embed)
        return

    # Update weekly, monthly, and total referral data
    weeklyData[referrer_id] = weeklyData.get(referrer_id, 0) + 1
    monthlyData[referrer_id] = monthlyData.get(referrer_id, 0) + 1
    totalReferrals[referrer_id] = totalReferrals.get(referrer_id, 0) + 1

    referrerMention = referred.mention
    referredMention = ctx.author.mention
    # Sending confirmation with embed
    embed = discord.Embed(title="Referral Confirmation", 
                        description=f'{referredMention} has been referred by {referrerMention}.', 
                        color=0x2ecc71)  # Green color for successful referral
    embed.set_thumbnail(url=str(ctx.author.avatar.url) if ctx.author.avatar else None)  # Set the user's avatar as the thumbnail
    await ctx.send(embed=embed)

@bot.command()
async def stats(ctx):
    if not is_allowed_channel(ctx):
        return  # Ignore if the command is not in the allowed channel
    
    referrer_id = str(ctx.author.id)
    weekly_count = weeklyData.get(referrer_id, 0)
    monthly_count = monthlyData.get(referrer_id, 0)

    embed = discord.Embed(title="Your Referral Stats", color=0x1abc9c)  # Teal color
    embed.add_field(name="Weekly Referrals", value=f"{weekly_count}", inline=False)
    embed.add_field(name="Monthly Referrals", value=f"{monthly_count}", inline=False)
    embed.set_thumbnail(url=str(ctx.author.avatar.url) if ctx.author.avatar else None)  # Set the user's avatar as the thumbnail
    await ctx.send(embed=embed)

@bot.command(name="set-mod")
async def set_mod(ctx, role: discord.Role):
    global mod_role_id  # Declare mod_role_id as global at the beginning of the function

    # Check if the user has administrator permissions or the set mod role
    if not (ctx.author.guild_permissions.administrator or (mod_role_id and any(role.id == mod_role_id for role in ctx.author.roles))):
        embed = discord.Embed(
            title="Permission Denied",
            description=f"{ctx.author.mention}, you do not have permission to use the set mod command.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    mod_role_id = role.id
    embed = discord.Embed(
        title="Mod Role Updated",
        description=f"The mod role has been set to: {role.name}",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# Only need if admin has access to set_channel command but mod has access too, so do the check in the command itself ?
# Error handler for set_mod command
@set_mod.error
async def set_mod_error(ctx, error):
    if not is_allowed_channel(ctx):
        return  # Ignore if the error response is not in the allowed channel
    
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="Permission Denied",
            description=f"{ctx.author.mention}, you do not have permission to use the set mod command.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

@bot.command()
async def leaderboard(ctx):
    embed = discord.Embed(title="Referral Leaderboard", color=0xf1c40f)  # Gold color
    # Weekly Leaderboard
    embed.add_field(name="Top 3 Weekly Referrals", 
                    value=get_leaderboard_text(weeklyData, ctx.guild), 
                    inline=False)
    # Monthly Leaderboard
    embed.add_field(name="Top 3 Monthly Referrals", 
                    value=get_leaderboard_text(monthlyData, ctx.guild), 
                    inline=False)
    embed.set_thumbnail(url=bot_avatar_url)  # Set the bot's avatar as the thumbnail
    await ctx.send(embed=embed)

def get_leaderboard_text(data, guild):
    top = sorted(data.items(), key=lambda x: x[1], reverse=True)[:3]
    text = "\n".join(f"{idx + 1}. {guild.get_member(int(user_id)).mention} Referrals: {count}" 
                     for idx, (user_id, count) in enumerate(top))
    return text or "No referrals yet."

@bot.command()
async def help(ctx):
    if not is_allowed_channel(ctx):
        return  # Ignore if the command is not in the allowed channel
    
    # Create an embed for the help message
    embed = discord.Embed(
        title="Get Started Guide!",
        description="The goal of this bot is to manage user referrals in the server. Here's how to use it:",
        color=0x00ff00  # Green color
    )
    embed.set_thumbnail(url=bot_avatar_url)  # Set the bot's avatar as the thumbnail

    # Add fields for each command
    embed.add_field(
        name="Public Commands",
        value="`!age` - Shows the age of your Discord account in days.",
        inline=False
    )
    embed.add_field(
        name="",
        value="`!referred-by @username` - Record that you were referred by another user.",
        inline=False
    )
    embed.add_field(
        name="",
        value="`!stats` - Displays the number of users you've referred this week and month.",
        inline=False
    )
    embed.add_field(
        name="Mod Commands",
        value="`!leaderboard` - Displays the Top 3 referrers this week and month.",
        inline=False
    )
    embed.add_field(
        name="",
        value="`!set-mod <role-name>` - Bot allows users with this role to access mod commands.",
        inline=False
    )
    embed.add_field(
        name="",
        value="`!set-channel #<channel-name> or <default>` - Bot will only recognize commands in a specific channel. Default allows all channels to be used.",
        inline=False
    )

    # Send the embed in a DM
    try:
        await ctx.author.send(embed=embed)
        if ctx.channel.type != discord.ChannelType.private:
            await ctx.send(f"{ctx.author.mention}, I've sent you a DM with the help information.")
    except discord.Forbidden:
        await ctx.send(f"Sorry {ctx.author.mention}, I can't send you a DM. Please check your DM settings.", embed=embed)

bot.run(BOT_TOKEN)
