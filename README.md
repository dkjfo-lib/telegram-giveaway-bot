# GIVEAWAY BOT

Telegram bot for managing personalized telegram giveaways.


## Installation

Prepare virtual environment and install all requirements.

```
python -m venv venv
.\venv\Scripts\activate
pip install -r .\requirements.txt
```

Create .env file with the following parameters
```
BOT_TOKEN
LOCAL
WEBHOOK_URL
IP
PORT
CHAT_ID
```

## Commands 

[/g_create   Creates new giveaways.](https://github.com/dkjfo-lib/Tg_GiveawayBot#g_create)

[/g_edit     Changes parameters of a given giveaway.](https://github.com/dkjfo-lib/Tg_GiveawayBot#g_edit)

[/g_subs     Displays subscribed users of a given giveaway.](https://github.com/dkjfo-lib/Tg_GiveawayBot#g_subs)

[/g_post     Creates post about a given giveaway.](https://github.com/dkjfo-lib/Tg_GiveawayBot#g_post)

[/g_finish   Declares winners of a given giveaway.](https://github.com/dkjfo-lib/Tg_GiveawayBot#g_finish)

Only creator of the giveaway can call edit, subs, post and finish commands.

## Commands Description:

### /g_create 
Creates new giveaways.

Arguments:

    - Number of winners
    - Giveaway name
    - Giveaway Description
    - Photo attachment (Optional)

Example:

`/g_create 10''Annal Community Giveaway #11''This time ten lucky subscribers will win a poro plush!`
    

### /g_edit 
Changes parameters of a given giveaway. 

Arguments:

    - Giveaway Id (Is sent to you when new giveaway is created)
    - Number of winners
    - Giveaway name
    - Giveaway Description
    - Photo attachment (Optional) 

Example:

`/g_edit 5a27b099-2d88-4fc4-ac0e-71d7a660a9f9''11''Annal Community Giveaway #11''This time ten lucky subscribers will eleven a poro plush!`

### /g_subs 
Displays subscribed users of a given giveaway. 

Arguments:

    - Giveaway Id (Is sent to you when new giveaway is created)

Example:

`/g_subs 5a27b099-2d88-4fc4-ac0e-71d7a660a9f9`

### /g_post 
Creates post about a given giveaway.

Arguments:

    - Giveaway Id (Is sent to you when new giveaway is created)

Example:

`/g_post 5a27b099-2d88-4fc4-ac0e-71d7a660a9f9`
    
### /g_finish 
Declares winners of a given giveaway.

Arguments:

    - Giveaway Id (Is sent to you when new giveaway is created)

Example:

`/g_finish 5a27b099-2d88-4fc4-ac0e-71d7a660a9f9`

### /restart 
Restarts bot. Works only in LOCAL=True mode