import pygsheets
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

# global variables for credentials and sheet name
CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE')
VOD_SHEET_NAME = os.getenv('VOD_SHEET_NAME')
BUILD_SHEET_NAME = os.getenv('BUILD_SHEET_NAME')
IDS_FILE = os.getenv('IDS_FILE')

def authorize():
    gc = pygsheets.authorize(service_file=CREDENTIALS_FILE)
    return gc

def create_vodsheet(worksheet_name):
    gc = authorize()
    sh = gc.open(VOD_SHEET_NAME)
    wks = sh.add_worksheet(title=worksheet_name, rows=100, cols=20)
    return wks

def open_vodsheet(worksheet_name):
    gc = authorize()
    sh = gc.open(VOD_SHEET_NAME)
    wks = sh.worksheet_by_title(worksheet_name)
    return wks

async def gs_add_build(build_id, discord_user_id, discord_username, build_name, role, weapon1, weapon2, heartrune, weight, gearscore, notes, gearpic):
    gc = authorize()
    sh = gc.open(BUILD_SHEET_NAME)
    wks = sh.worksheet_by_title('Builds')

    # Insert the build info into the worksheet
    wks.insert_rows(row=1, number=1, values=[build_id, str(discord_user_id), discord_username, build_name, role, weapon1, weapon2, heartrune, weight, gearscore, notes, gearpic])

def gs_edit_build(discord_user_id, build_id, field, value):
    gc = authorize()
    sh = gc.open(BUILD_SHEET_NAME)
    wks = sh.worksheet_by_title('Builds')

    # Map field variables to column headers
    field_to_column = {
        'buildname': 'BuildName',
        'role': 'BuildRole',
        'weapon1': 'BuildWeapon1',
        'weapon2': 'BuildWeapon2',
        'ability': 'BuildAbility',
        'weight': 'BuildWeight',
        'gearscore': 'BuildGearScore',
        'notes': 'UserNotes',
        'gearpic': 'BuildGearPic'
    }

    # Find the column containing the field
    column_header = field_to_column.get(field.lower())
    if not column_header:
        raise ValueError(f"Invalid field: {field}")
    cell_list = wks.find(column_header, rows=(1,1))
    if not cell_list:
        raise ValueError(f"Column header {column_header} not found")
    cell = cell_list[0]

    # Find the row containing the build
    index = None
    for i, row in enumerate(wks.get_all_values()):
        if i == 0:
            continue  # Skip header row
        if len(row) > 1 and int(row[0]) == build_id and int(row[1]) == discord_user_id:
            index = i
            break

    # Get the cell for the corresponding column and row
    if index is None:
        raise ValueError(f"Build_ID {build_id} for user {discord_user_id} not found")
    column_letter = chr(cell.col + 64) # Convert 0-based index to ASCII letter
    cell_label = f"{column_letter}{index+1}"
    cell = wks.cell(cell_label)

    # Update the specified field for the build
    # Update the specified field for the build
    if field == 'gearpic':
        formula = f'=HYPERLINK("{value}")'
        cell.formula = formula
    else:
        cell.value = value
        cell.update()

async def gs_remove_build(discord_user_id, build_id):
    gc = authorize()
    sh = gc.open(BUILD_SHEET_NAME)
    wks = sh.worksheet_by_title('Builds')

    await asyncio.sleep(0.1)
    # Find the row containing the build
    index = None
    for i, row in enumerate(wks.get_all_values()):
        if i == 0:
            continue  # Skip header row
        if len(row) > 1 and int(row[0]) == build_id and int(row[1]) == discord_user_id:
            index = i + 1
            break

    if index is None:
        raise ValueError(f"Build_ID {build_id} for user {discord_user_id} not found")

    # Delete the row
    wks.delete_rows(index, number=1)