# Slackbot
A program to test slash commands in Slack using various APIs

## Requirements in requirements.txt

1. Clone repo
2. Install ngrok: https://ngrok.com/
3. `python -m http.server 5000`
4. `ngrok http --region=us 5000`
5. Grab Forwarding URL
6. `python bot.py`
7. Update parameters in Slack Event Handler (https://api.slack.com/apps/APPID/event-subscriptions), add /slack/events after ngrok URL:
![Events](https://i.imgur.com/tvZ9MUJ.png)
8. Navigate to Slash Commands and add a slash command for each command mentioned in the bot:
   * /image
   * /awesome
   * /joke
   * /country
   * /random
   * /emoji
   * /chatgpt
   * /animal
   
![Slash Commands](https://i.imgur.com/4QoWD4L.png)

9. Edit each slash command and input ngrok Forwarding URL in Request URL field, with the command appended at the end. For example, /image:
    * https://NGROKURL/image
    * https://NGROKURL/chatgpt
  
10. Run slackbot again `python bot.py`


## Commands
* `/image`
### Generates a random image from Lorep Picsum
![Random Image](https://i.imgur.com/1qHmgoR.png)


* `/awesome`
### Outputs "YOUR_NAME is awesome!"
![Awesome](https://i.imgur.com/NqX7j6S.png)


* `/joke`

### Pulls a random dad joke via API

![Joke](https://i.imgur.com/XRgTmhQ.png)


* `/country`
### Shows the flag of a country with parameter XX where XX is the 2-digit country code
`/country us`

![US](https://i.imgur.com/w9oYC81.png)

`/country zb`

![ZW](https://i.imgur.com/vONHhvU.png)

`/country --help` - Show a list of allowed parameters

![Help](https://i.imgur.com/yR62UhV.png)


* `/random`

### Generates a random word of random length, unless length flag is specified

`/random`

![Random](https://i.imgur.com/RFev8lZ.png)

`/random --5` and `/random --7`

![Random 57](https://i.imgur.com/bakCxJW.png)


* `/chatgpt`

### Invokes chat GPT with whatever command you type after /chatgpt

`/chatgpt COMMAND`

![ChatGPT](https://i.imgur.com/BBmgwd8.png)



* `/emoji --random`

### Pulls a random emoji

![Emoji](https://i.imgur.com/VAw5rOU.png)


* `/animal`

### Pulls information about any animal

`/animal lion` - Shows the common name of that animal

![Animal](https://i.imgur.com/VYTXXoP.png)

`/animal lion --taxonomy` - Shows the taxonomy of that animal

![Animal](https://i.imgur.com/6GJNb1F.png)

`/animal lion --characteristics` - Shows various characteristics of that animal

![Animal](https://i.imgur.com/CskmL5n.png)

`/animal lion --locations` - Shows the location of that animal

![Animal](https://i.imgur.com/FYeI1fD.png)


* 
## APIs Used:
* [Slack API](https://api.slack.com/legacy/enabling-bot-users)
* [Random Word Generator](https://random-word-api.herokuapp.com/word)
* [Lorep Picsum](https://picsum.photos/)
* [Dad Jokes](https://icanhazdadjoke.com/)
* [Open Emoji API](https://emoji-api.com/)
* [OpenAI API](https://platform.openai.com/docs/api-reference)
* [FlagCDN](https://flagcdn.com/)
* [Animals API](https://api-ninjas.com/api/animals)

## .env variables
* [SLACK_API_TOKEN](https://api.slack.com/authentication/token-types)
* [SLACK_SIGNING_SECRET](https://api.slack.com/authentication/token-types)
* [SLACK_USER_ID](https://api.slack.com/authentication/token-types)
* [SLACK_APP_ID](https://api.slack.com/authentication/token-types)
* [SLACK_VERIFICATION_TOKEN](https://api.slack.com/authentication/token-types)
* [CHATGPT_API_KEY](https://platform.openai.com/api-keys)
* [OPEN_EMOJI_API_KEY](https://emoji-api.com/)
* [ANIMAL_API_KEY](https://api-ninjas.com/api/animals)
