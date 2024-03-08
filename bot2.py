#python -m http.server 5000
#ngrok http --region=us 5000
#Update parameters in Event Handler
#Run python code

import os
import requests
import threading
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.signature import SignatureVerifier
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the Slack signing secret from environment variable
signing_secret = os.getenv('SLACK_SIGNING_SECRET')
if not signing_secret:
	print("Please set the 'SLACK_SIGNING_SECRET' environment variable.")
	exit(1)

# Get app ID from the environment variable
app_id = os.getenv('SLACK_APP_ID')
if not app_id:
	print("Please set the 'SLACK_APP_ID' environment variable.")
	exit(1)

# Create a WebClient instance
client = WebClient(token=os.getenv('SLACK_API_TOKEN'))

# Create a SignatureVerifier instance
verifier = SignatureVerifier(signing_secret)

# Post the message from message.txt to the #testing channel
try:
	with open("message.txt", 'r') as file:
		message = file.read()
		client.chat_postMessage(channel='#testing', text=message)
except SlackApiError as e:
	print("Error sending message:", e)

# Create a Flask app
app = Flask(__name__)

# Variable to keep track of whether the bot should respond to the next message
should_respond = False

def generate_and_upload_image():
	try:
		# Get a random image from Lorem Picsum
		response = requests.get('https://picsum.photos/200', timeout=5)
		response.raise_for_status()			  # Raise an exception for 4xx and 5xx status codes

		# Save the image locally
		with open('image.jpg', 'wb') as out_file:
			out_file.write(response.content)

		# Upload the image to Slack using client.files_upload_v2()
		with open('image.jpg', 'rb') as file:
			response = client.files_upload_v2(
				channel='C06N8BVF0LW',	 # Channel ID for #testing
				file=file,
				initial_comment="Random Image"
			)

	except requests.exceptions.RequestException as e:
		# Handle any request exceptions
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
	# Check if the request is coming from the Slack command
	if request.form['token'] == os.getenv('SLACK_VERIFICATION_TOKEN'):
		try:
			# Immediate response to Slack command
			threading.Thread(target=generate_and_upload_image).start()

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

		# Respond with the message
		client.chat_postMessage(channel='#testing', text=f"{user_name} is awesome!")

	except SlackApiError as e:
		print("Error sending message:", e)

	return '', 200

@app.route('/joke', methods=['POST'])
def dad_joke():
	try:
		# Get a random dad joke from icanhazdadjoke.com
		response = requests.get('https://icanhazdadjoke.com/', headers={'Accept': 'application/json'})
		response.raise_for_status()	 # Raise an exception for 4xx and 5xx status codes

		# Extract the joke from the response
		joke = response.json()['joke']

		# Post the joke as a message in the channel
		client.chat_postMessage(channel='#testing', text=joke)

	except requests.exceptions.RequestException as e:
		# Handle any request exceptions
		print("Request Error:", e)

	return '', 200

if __name__ == '__main__':
	app.run(port=5000)
