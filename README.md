# Eureka Bot 🏆

## Inspiration

A good friend of mine recently began streaming on Twitch this past year. His growth model was supported by giveaways. One problem we discussed was that the same people were entering his giveaways and he wasn't reaching the growth he wanted. This bot tackles that challenge by gamifying inviting friends to his Discord server, ultimately bringing in more engagement.

**Note: This project is still in development.**

## What It Does

Eureka is designed to manage user referrals within a server, rewarding members for bringing in new members to the community. The suite of commands are explained in the table below. Some of the core functionalities include referral tracking and validation, data management, and admin setup. 

# Bot Commands

Below is a list of commands supported by the bot, along with a brief description of what each command does:

| Command                            | Description                                                                                   |
| ---------------------------------- | --------------------------------------------------------------------------------------------- |
| !age                               | Outputs the age if your Discord account. Minimum age is 3 months to use the referral command. |
| !referred-by \`\`\`@username\`\`\` | Records the referral of User A by User B and updates overall statistics.                      |
| !stats                             | Outputs the number of users who have stated your referral this week and month.                |
| !leaderboard                       | Outputs the top 3 referrers for this current week and month. Can be moderator only.           |
| !set-mod <role-name>               | Sets a specific role as the "moderator" granting access to following commands.                |
| !set-channel #channel-name         | Sets a channel to use for bot commands, restricting spam in channels.                         |
| !set-channel default               | Resets the particular channel command and allows commands to be used in any channel.          |
| !help                              | Sends a DM to the user explaining how to use the bot.                                         |


## Development Thought Process

The bot is powered by the [Discord.py](https://discordpy.readthedocs.io/en/stable/). There is no major need for a frontend interface, so I opted to use Python for this project over [Discord.js](https://discord.js.org/).

In my initial development of the bot, I strived for efficiency and accessibility by using dictionaries to store all processed information. I eventually realized a pivotal issue -- that I was storing data in memory and could cause a couple of issues.  Also, I knew there would be a couple ways to finesse the system, so I carefully plotted anti-abuse mechanisms. Lastly, UX is always important. The bot outputs clear messages through embeds.

## What's next?

- Migrate to [TinyDB]()
- Refactor the code so commands are [ephemeral](https://discordpy.readthedocs.io/en/latest/interactions/api.html).
- Organize code base into smaller chunks instead of a massive file.
