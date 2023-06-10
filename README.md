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
- In your repo on github head to `settings` -> `secrets` -> `actions`
- Click `New repository secret`
- Name your secret: `ACCOUNT_ID`
- Enter the value of the account_id you fetched from `FenrisDebug.txt`

## Details

Based off of https://github.com/patrickloeber/python-github-action-template
