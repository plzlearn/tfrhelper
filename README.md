# tfrhelper
Helper bot for TFR discord, has functionality for New World build management, vod management, event management, and more.

# Setup
Clone the repository, create a .env file with the following settings

DISCORD_TOKEN=''
CREDENTIALS_FILE="utils/google-creds.json"
VOD_SHEET_NAME=''
BUILD_SHEET_NAME=''
IDS_FILE="utils/ids.json"
IMGUR_API_ID=''
IMGUR_API_SECRET=''

Fill in the missing values with the appropriate value.

You'll need to create a google api account that has access to your spreadsheets, and add the account as an editor. You'll also need to generate the json creds file and put it in the path set in the .env file.

You'll also need to create an IMGUR account and get the API ID and SECRET for the Gear Image uploads to work.

Your builds spreadsheet will need to have the following column headers in any order

BuildID.	DiscordID	DiscordName	BuildName	BuildRole	BuildWeapon1	BuildWeapon2	BuildAbility	BuildWeight	BuildGearscore	UserNotes	BuildGearPic

Create an empty threads.json, and an empty config.json file in the root directory the bot.