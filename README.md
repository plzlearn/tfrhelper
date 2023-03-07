
# TFRHelper

Helper bot for TFR discord, has functionality for New World build management, vod management, event management, and more.

  

# Setup

### Environment Variables

Clone the repository and create an .env file with the following settings.

 - DISCORD_TOKEN=''
 - CREDENTIALS_FILE="utils/google-creds.json"
 - VOD_SHEET_NAME=''
 - BUILD_SHEET_NAME=''
 - IDS_FILE="utils/ids.json"
 - IMGUR_API_ID=''
 - IMGUR_API_SECRET=''
 
Fill in the missing values with the appropriate value.

### Google API Account

You'll need to create a [Google Developer Account](https://developers.google.com/) and create an API account that has access to your spreadsheets. You'll need to add this account as an editor on all of your spreadsheets. You'll also need to generate the json credentials file and place it in the path set in the .env file.

### Imgur API Account

You'll need to create an IMGUR account and get the API ID and SECRET for the Gear Image uploads to work.
 
### Builds Spreadsheet

Your builds spreadsheet will need to have the following column headers in any order

BuildID., DiscordID, DiscordName, BuildName, BuildRole, BuildWeapon1, BuildWeapon2, BuildAbility, BuildWeight, BuildGearscore, UserNotes, BuildGearPic

### Config and Threads JSON  

Create an empty threads.json, and an empty config.json file in the root directory the bot.6