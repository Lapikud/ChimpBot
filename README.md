# ChimpBot
Synchronizes Mailchimp with the latest email addresses gathered from Google Sheets.

# Installation
Create a new project at https://console.developers.google.com/<br>
Enable Google Sheets API for the project and generate a new API key under Google Sheets<br>

Rename ```docker-compose.yml.example``` to ```docker-compose.yml```<br>
Fill in ```docker-compose.yml```

`SPREADSHEET_ID` - Can be found from the url of the document:
`https://docs.google.com/spreadsheets/d/<SPREADSHEET ID>`

`SPREADSHEET_RANGE_NAME` - Format: `<SHEET NAME>`!`<START COLUMN>`:`<END COLUMN>`<br>

`MAILCHIMP_API_KEY` - Mailchimp API key

`MAILCHIMP_LIST_ID` - Mailchimp mailing list IDs (Multiple list IDs are supported with a comma delimiter). If no list IDs are specified, then all available lists will be printed out instead of running the bot. (`docker-compose up --build` can be used to display the lists)

Build docker container ```docker-compose build```<br>
Run docker container ```docker-compose up```