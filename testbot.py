#python -m http.server 5000
#ngrok http --region=us 5000
#Update parameters in Event Handler
#Run python code

import os
import requests
import threading
import openai
import random
import unicodedata
import re
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.signature import SignatureVerifier
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the Slack signing secret from the environment variable
signing_secret = os.getenv('SLACK_SIGNING_SECRET')
if not signing_secret:
	print("Please set the 'SLACK_SIGNING_SECRET' environment variable.")
	exit(1)

# Get the app ID from the environment variable
app_id = os.getenv('SLACK_APP_ID')
if not app_id:
	print("Please set the 'SLACK_APP_ID' environment variable.")
	exit(1)

# Create a WebClient instance
client = WebClient(token=os.getenv('SLACK_API_TOKEN'))

# Create a SignatureVerifier instance
verifier = SignatureVerifier(signing_secret)

# Set OpenAI API key
openai.api_key = os.getenv('CHATGPT_API_KEY')

# Post the message from message.txt to the #testing channel
try:
	with open("message.txt", 'r') as file:
		message = file.read()
		client.chat_postMessage(channel='#testing', text=message)
except SlackApiError as e:
	print("Error sending message:", e)

# Create a Flask app
app = Flask(__name__)

def generate_and_upload_image(channel_id):
	try:
		# Get a random image from Lorem Picsum
		response = requests.get('https://picsum.photos/200', timeout=5)
		response.raise_for_status()

		# Save the image locally
		with open('image.jpg', 'wb') as out_file:
			out_file.write(response.content)

		# Upload the image to Slack using client.files_upload_v2()
		with open('image.jpg', 'rb') as file:
			response = client.files_upload_v2(
				channel=channel_id,
				file=file,
				initial_comment="Random Image"
			)

	except requests.exceptions.RequestException as e:
		print("Request Error:", e)


@app.route('/slack/events', methods=['POST'])
def slack_events():
	global should_respond
	data = request.json

	# Handle URL verification challenge
	if data.get('type') == 'url_verification':
		return jsonify({'challenge': data.get('challenge')}), 200

	# Verify the request by checking the signature
	if not verifier.is_valid_request(request.get_data(), request.headers):
		return '', 400

	# Handle the event
	event = data.get('event')
	if event and event.get('type') == 'message' and event.get('subtype') is None:
		# Check if the message is not from the bot itself
		if event.get('bot_id') != app_id:
			# Check if the message is not a reply to a slash command
			if event.get('text') and not event.get('text').startswith('/'):
				# Set should_respond to True so the bot responds to the next message
				should_respond = True

	return '', 200

@app.route('/image', methods=['POST'])
def random_image():
	# Get the channel ID from the request
	channel_id = request.form['channel_id']

	# Check if the request is coming from the Slack command
	if request.form['token'] == os.getenv('SLACK_VERIFICATION_TOKEN'):
		try:
			# Immediate response to Slack command
			threading.Thread(target=generate_and_upload_image, args=(channel_id,)).start()

			return jsonify({
				"response_type": "in_channel",
				"text": "Please wait: image is generating"
			}), 200

		except Exception as e:
			print("Error starting background task:", e)

	return '', 200


@app.route('/awesome', methods=['POST'])
def awesome_command():
	try:
		# Get user info from Slack
		user_id = request.form['user_id']
		response = client.users_info(user=user_id)
		user_name = response.data['user']['profile']['display_name']

		# Get the channel ID from the request
		channel_id = request.form['channel_id']

		# Respond with the message
		client.chat_postMessage(channel=channel_id, text=f"{user_name} is awesome!")

	except SlackApiError as e:
		print("Error sending message:", e)

	return '', 200

# Update the dad_joke() function to handle DMs
@app.route('/joke', methods=['POST'])
def dad_joke():
	try:
		# Get the channel ID from the request
		channel_id = request.form['channel_id']

		# Check if the channel is a DM
		if channel_id.startswith('D'):
			# Get a random dad joke from icanhazdadjoke.com
			response = requests.get('https://icanhazdadjoke.com/', headers={'Accept': 'application/json'})
			response.raise_for_status()

			# Extract the joke from the response
			joke = response.json()['joke']

			# Get the user ID from the request
			user_id = request.form['user_id']

			# Send the joke as a direct message to the user
			client.chat_postMessage(channel=user_id, text=joke)
		else:
			# Get a random dad joke from icanhazdadjoke.com
			response = requests.get('https://icanhazdadjoke.com/', headers={'Accept': 'application/json'})
			response.raise_for_status()

			# Extract the joke from the response
			joke = response.json()['joke']

			# Post the joke as a message in the channel
			client.chat_postMessage(channel=channel_id, text=joke)

	except requests.exceptions.RequestException as e:
		print("Request Error:", e)

	return '', 200

@app.route('/country', methods=['POST'])
def country_command():
	# Get the command text from the request
	command_text = request.form['text'].strip()

	# Fetch the JSON data with country names and codes
	try:
		response = requests.get('https://flagcdn.com/en/codes.json')
		response.raise_for_status()
		countries = response.json()
	except requests.exceptions.RequestException as e:
		return jsonify({'response_type': 'ephemeral', 'text': f'Error: {e}'})

	# Check if the command is requesting help
	if command_text == '--help':
		# Show a list of allowed country codes
		allowed_codes = '\n'.join([f'{code}: {name}' for code, name in countries.items()])
		return jsonify({
			'response_type': 'ephemeral',
			'text': f'Allowed country codes:\n{allowed_codes}'
		})

	# Check if the command includes a valid country code
	if command_text in countries:
		country_name = countries[command_text]
		flag_url = f'https://flagcdn.com/96x72/{command_text.lower()}.png'

		# Respond with the flag image and country name
		return jsonify({
			'response_type': 'in_channel',
			'text': f'Flag of {country_name}:',
			'attachments': [{'image_url': flag_url}]
		})
	else:
		# If the country code is not valid, show an error message
		return jsonify({
			'response_type': 'ephemeral',
			'text': 'Invalid country code. Type "/country --help" for a list of allowed country codes.'
		})

@app.route('/random', methods=['POST'])
def random_word_command():
	# Get the command text from the request
	command_text = request.form['text'].strip()

	# Extract the length parameter from the command text
	try:
		length = int(command_text.split('--')[1])
	except IndexError:
		length = None
	except ValueError:
		return jsonify({
			'response_type': 'ephemeral',
			'text': 'Invalid length parameter. Please use "--<number>" to specify the length.'
		})

	# Fetch a random word with the specified length
	try:
		word = get_random_word(length)
		# Capitalize the first letter of the word
		word = word.capitalize()
		return jsonify({
			'response_type': 'in_channel',
			'text': f'{word}'
		})
	except requests.exceptions.RequestException as e:
		return jsonify({
			'response_type': 'ephemeral',
			'text': f'Error fetching random word: {e}'
		})

def get_random_word(length=None):
	url = 'https://random-word-api.herokuapp.com/word'
	params = {'length': length} if length else {}
	response = requests.get(url, params=params)
	response.raise_for_status()
	return response.json()[0]
	
def interact_with_chatgpt(message):
	completion = openai.ChatCompletion.create(
		model='gpt-3.5-turbo',
		messages=[
			{'role': 'user', 'content': message}
		],
		max_tokens=50,
		temperature=0.7
	)

	return completion.choices[0].message['content']

@app.route('/chatgpt', methods=['POST'])
def chat_gpt():
	# Get the text from the request
	text = request.form.get('text')
	
	try:
		# Use the OpenAI API to generate a completion
		response = openai.ChatCompletion.create(
			model='gpt-3.5-turbo',	# Use the correct model name
			messages=[
				{'role': 'system', 'content': 'You are a helpful assistant.'},
				{'role': 'user', 'content': text}
			],
			max_tokens=50,
			temperature=0.7
		)
		
		# Get the completion text from the response
		completion_text = response.choices[0].message.content
		
		# Respond with the completion text
		return jsonify({
			'response_type': 'in_channel',
			'text': completion_text
		})
	
	except openai.error.InvalidRequestError as e:
		# Handle OpenAI API errors
		error_message = str(e)
		print("OpenAI API Error:", error_message)
		return jsonify({
			'response_type': 'ephemeral',
			'text': f"Error processing request: {error_message}"
		})

@app.route('/emoji', methods=['POST'])

def handle_emoji_command():
	api_key = os.getenv('OPEN_EMOJI_API_KEY')

	text = request.form.get('text', '')

	# Check for the --random flag
	if '--random' in text:
		# Fetch a random emoji
		try:
			response = requests.get(f'https://emoji-api.com/emojis?access_key={api_key}')
			response.raise_for_status()
			emojis = response.json()
			random_emoji = random.choice(emojis)
			return jsonify({
				'response_type': 'in_channel',
				'text': f'{random_emoji["character"]} - {random_emoji["unicodeName"]}'
			})
		except requests.exceptions.RequestException as e:
			return jsonify({'response_type': 'ephemeral', 'text': f'Error: {e}'})

	# Check if the text is an emoji character
	if len(text) == 1 and unicodedata.category(text) == 'So':
		emoji_code = ord(text)
		# Fetch the emoji description
		try:
			response = requests.get(f'https://emoji-api.com/emojis?search={emoji_code}&access_key={api_key}')
			response.raise_for_status()
			emoji_data = response.json()
			if emoji_data:
				return jsonify({
					'response_type': 'in_channel',
					'text': f'{emoji_data[0]["character"]} - {emoji_data[0]["unicodeName"]}: {emoji_data[0]["slug"]}'
				})
			else:
				return jsonify({
					'response_type': 'ephemeral',
					'text': 'Emoji not found.'
				})
		except requests.exceptions.RequestException as e:
			return jsonify({'response_type': 'ephemeral', 'text': f'Error: {e}'})

	return jsonify({
		'response_type': 'ephemeral',
		'text': 'Please provide a valid flag (--random or --<emoji>)'
	})

@app.route('/animal', methods=['POST'])
def animal_command():
	# Get the command text from the request
	command_text = request.form.get('text', '')

	# Extract the animal name and flag (if provided)
	parts = command_text.split()
	if len(parts) < 1:
		return jsonify({
			'response_type': 'ephemeral',
			'text': 'Please provide an animal name.'
		})

	animal_name = parts[0]
	flag = parts[1] if len(parts) > 1 and parts[1].startswith('--') else '--common_name'

	# Fetch the animal data from the API
	api_url = f'https://api.api-ninjas.com/v1/animals?name={animal_name}'
	api_key = os.getenv('ANIMAL_API_KEY')

	try:
		response = requests.get(api_url, headers={'X-Api-Key': api_key})
		response.raise_for_status()
		animal_data = response.json()[0]
	except requests.exceptions.RequestException as e:
		return jsonify({
			'response_type': 'ephemeral',
			'text': f'Error fetching animal data: {e}'
		})

	# Extract the value based on the flag
	if flag == '--common_name':
		value = animal_data['characteristics']['common_name']
	elif flag == '--taxonomy':
		value = '\n'.join([f"{k.capitalize().replace('_', ' ')}: {v}" for k, v in animal_data['taxonomy'].items()])
	elif flag == '--locations':
		value = ', '.join(animal_data['locations'])
	elif flag == '--characteristics':
		value = '\n'.join([f'{re.sub(r"_+", " ", k).title()}: {re.sub(r", $", "", v) if v.endswith(",") else v}' if k != 'top_speed' else f'{re.sub(r"_+", " ", k).title()}: {v.upper()}' for k, v in animal_data['characteristics'].items()])
	else:
		return jsonify({
			'response_type': 'ephemeral',
			'text': 'Invalid flag. Available flags: --common_name, --taxonomy, --locations, --characteristics'
		})

	# Format the value for Color
	if 'color' in animal_data['characteristics']:
		colors = animal_data['characteristics']['color']
		formatted_color = re.sub(r'(?<!^)(?=[A-Z])', '/', colors)
		value = value.replace(f'Color: {colors}', f'Color: {formatted_color}')

	# Format the response
	if flag == '--common_name':
		response_text = f'Common Name: {value}'
	elif flag == '--taxonomy':
		response_text = f'Taxonomy: \n\n{value}'
	elif flag == '--characteristics':
		response_text = f'Characteristics: \n\n{value}'
	else:
		response_text = f'{flag[2:]}: {value}'

	return jsonify({
		'response_type': 'in_channel',
		'text': response_text
	})



if __name__ == '__main__':
	app.run(port=5000)
