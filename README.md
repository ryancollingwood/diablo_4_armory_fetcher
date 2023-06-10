# diablo_4_armory_fetcher

Use the unofficial Diablo 4 Armory https://d4armory.io/ to snapshot your characters data, combined with Github actions to fetch and store the data on a schedule

Using this you can track your characters until/if Blizzard create an official API.

## Setup

### Find Your Account ID∏

To find your account id:
- Open Diablo IV install directory
- Open `FenrisDebug.txt`
- Search for 'account_id'

### Register your characters on d4armory.io
- Head to https://d4armory.io/
- Search for your account using the account_id you fetched from `FenrisDebug.txt`
- Confirm you can see your characters, there may be some latency

### Setup your Clone of this Repo
- Clone this repo

#### Setup Repo Secrets
- In your repo on github head to `settings` -> `secrets` -> `actions`
- Click `New repository secret`
- Name your secret: `ACCOUNT_ID`
- Enter the value of the account_id you fetched from `FenrisDebug.txt`

#### Setup Repo Write Permissions
- In your repo on github head to `settings` -> `actions`
- Under `Workflow permissions` select `Read and write permissions`
- Click `save`

## Details

- Based off of https://github.com/patrickloeber/python-github-action-template for using Github actions to run on a scheduled
- By default the script is run every twelve hours as specified in `.github/workflows/actions.yml`. I'd caution against running this too often as it would put a load on the kind folks at d4armory.io

## TODO

- Add a script (bash probably) to get all revisions of the character data commited to the repo