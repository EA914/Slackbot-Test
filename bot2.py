#python -m http.server 5000
#ngrok http --region=us 5000
#Update parameters in Event Handler for /slack/events and for /image
#Run python code


import os
import requests
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.signature import SignatureVerifier
from dotenv import load_dotenv
import shutil

# Load environment variables from .env file
load_dotenv()

# Get the Slack signing secret from environment variable
signing_secret = os.getenv('SLACK_SIGNING_SECRET')
if not signing_secret:
	print("Please set the 'SLACK_SIGNING_SECRET' environment variable.")
	exit(1)

# Get your app ID from the environment variable
app_id = os.getenv('SLACK_APP_ID')
if not app_id:
	print("Please set the 'SLACK_APP_ID' environment variable.")
	exit(1)

# Create a WebClient instance
client = WebClient(token=os.getenv('SLACK_API_TOKEN'))

# Create a SignatureVerifier instance
verifier = SignatureVerifier(signing_secret)

# Create a Flask app
app = Flask(__name__)

# Variable to keep track of whether the bot should respond to the next message
should_respond = False

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
			# Check if the bot should respond to the next message
			if should_respond:
				try:
					client.chat_postMessage(channel=event['channel'], text="ok!")
				except SlackApiError as e:
					print("Error sending message:", e)
				# Set should_respond to False so the bot doesn't respond to the next message
				should_respond = False
			else:
				# Set should_respond to True so the bot responds to the next message
				should_respond = True

	return '', 200

@app.before_first_request
def before_first_request():
	# Post the message from message.txt to the #testing channel
	try:
		with open("message.txt", 'r') as file:
			message = file.read()
			client.chat_postMessage(channel='#testing', text=message)
	except SlackApiError as e:
		print("Error sending message:", e)

@app.route('/image', methods=['POST'])
def random_image():
	# Check if the request is coming from the Slack command
	if request.form['token'] == os.getenv('SLACK_VERIFICATION_TOKEN'):
		try:
			# Get a random image from Lorem Picsum
			response = requests.get('https://picsum.photos/200', timeout=30)
			response.raise_for_status()	 # Raise an exception for 4xx and 5xx status codes

			# Save the image locally
			with open('image.jpg', 'wb') as out_file:
				out_file.write(response.content)

			# Upload the image to Slack
			with open('image.jpg', 'rb') as file:
				client.files_upload(
					channels='#testing',
					file=file,
					initial_comment="Random Image"
				)

		except requests.exceptions.RequestException as e:
			# Handle any request exceptions
			print("Request Error:", e)

		except Exception as e:
			# Handle any other exceptions
			print("Error:", e)

	return '', 200

if __name__ == '__main__':
	app.run(port=5000)