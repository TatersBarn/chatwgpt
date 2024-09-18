import openai
from openai import OpenAI
import os
import sys
import argparse
import re
import readline
import threading
import asyncio
import subprocess
import time
import importlib

import OobaFunctions

importlib.reload(OobaFunctions)

#script_dir = os.getcwd()
script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

config = {}

# Default Configuration (modify taterchat.conf to change these easily)
default_voutput_dir = f"{script_dir}/outputs"
default_vmodels_dir = f"{script_dir}/models"
#default_voice_model = "en_US-kristin-medium.onnx"
default_speaker = 0
default_target = "openai"
default_model_choice = "gpt-4o-mini"
default_prompt_choice = "concisepilot"
#default_voice_bool = True
default_oneout = False

prompts = OobaFunctions.prompts

def str2bool(v):
	if v.lower() in ('yes', 'true', 't', '1'):
		return True
	elif v.lower() in ('no', 'false', 'f', '0'):
		return False
	else:
		return v.lower()

# Configure api credentials from environment variable or tell user to set one up
def check_openai_api_key():
	# Check if the OPENAI_API_KEY environment variable is set and notify the user if it's missing.
	api_key = os.getenv("OPENAI_API_KEY")
	if api_key in [None, ""]:
		print("ERROR: The OPENAI_API_KEY environment variable is not set.")
		print("To set it, run the following command:\n")
		print("  export OPENAI_API_KEY='your-api-key-here'\n")
		print("Alternatively, you can add this to your shell's configuration file (e.g., .bashrc, .zshrc) for persistent use.\n")
		apiq = input("would you like to input an OpenAI API key right now? (not recommended) (Y/n)")
		if apiq in affirmatives:
			api_key = input("Please enter your OpenAI API key now: ").strip()
			# Here you can proceed to use the input API key, e.g., setting the environment variable
			print(f"API key set: {api_key}")
		else:
			print(f"continuing without API key")
			api_key = ""
		return api_key

parser = argparse.ArgumentParser(description='Chat with ChatGPT or other LLMS with various parameters')
parser.add_argument('-t', '--target', type=str, help='Target for api request choices: openai OR ooba (Default openai)')
parser.add_argument('-m', '--model', type=str, help='OpenAI model choices: gpt-4o-mini OR gpt-4o OR gpt-3.5-turbo (Default gpt-4o-mini')
parser.add_argument('message', type=str, nargs='?', default='', help='User Message to begin conversation with LLM')
parser.add_argument('-p', '--prompt', type=str, help='Prompt style choice: concisepilot, gptlike (Default concisechat)')

# One Output Mode for debugging
parser.add_argument('-o', '--oneout', type=str2bool, help='One output mode - True to break after one response')

# Voice output, defaults to false here as piper-tts config is not ready for release
#parser.add_argument('-v', '--voice', type=str2bool, help='Toggle "True" for Voice Output using Piper')

# CURRENTLY BROKEN streaming output
parser.add_argument('-s', '--stream', type=str2bool, help='[NOT YET IMPLEMENTED Output and conversationhistory are broken when Streaming is True!] Streaming True or False or t or f or 1 or 0 (Default False)', default=False)

args = parser.parse_args()

target = default_target
model_choice = default_model_choice
prompt_choice = default_prompt_choice
#voice_model = default_voice_model
speaker = default_speaker
oneout = False
#voice = True
output_dir = default_voutput_dir
models_dir = default_vmodels_dir

targets = ['openai','ooba']
models = ['gpt-4o-mini','gpt-4o','gpt-3.5-turbo', 'oobastank']
#voice_models = [
#	'en_US-kristin-medium.onnx',
#	'en_GB-semaine-medium.onnx',
#	'en_US-l2arctic-medium.onnx',
#	'en_US-lessac-medium.onnx',
#	'en_US-libritts-high.onnx',
#	'en_US-libritts_r-medium.onnx',
#	'Twilight.pth'
#]
#multivoice_models = [
#	'en_GB-semaine-medium.onnx',
#	'en_US-l2arctic-medium.onnx',
#	'en_US-libritts-high.onnx',
#	'en_US-libritts_r-medium.onnx'
#]
sysmsgs = OobaFunctions.prompts


with open(f"{script_dir}/taterchat.conf", 'r') as f:
	for line in f:
		line = line.strip()
		if line.startswith('#') or not line:  # Ignore comment lines and empty lines
			continue
		key, value = line.split('=', 1)
		value = value.strip()  # Remove any whitespace around the value

		if key == 'target':
			if value in targets:
				target = value
			else:
				print(f"Warning: invalid target in config '{value}'. Using default: {default_target}")

		elif key == 'model_choice' and args.model not in models:
			if value in models:
				model_choice = value
			else:
				print(f"Warning: Invalid model in config '{value}'. Using default: {default_model_choice}.")

		elif key == 'prompt':
			if value in sysmsgs.keys():
				prompt_choice = value
			else:
				print(f"Warning: Invalid prompt in config '{value}'. Using default: {default_prompt_choice}.")

#		elif key == 'voice_model':
#			if value in voice_models:
#				voice_model = value
#			else:
#				print(f"Warning: Invalid voice_model in config '{value}'. Using default: {default_voice_model}.")

		elif key == 'speaker':
			if not (isinstance(int(value), int) and int(value) > -5):
				print(f"Warning: Invalid speaker '{value}'. Using default: {default_speaker}.")
				speaker = default_speaker
			else:
				speaker = int(value)

		elif key == 'oneout':
			oneout = str2bool(value)

#		elif key == 'voice':
#			voice =str2bool(value)


# Define color codes
class Colors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	ERROR = '\033[91m'
	ENDC = '\033[0m'  # Reset to default color
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

# Create an Event object to signal when to stop the loading animation
loading_event = threading.Event()

# list of acceptable affirmatives for api input question
affirmatives = ["y", "yes", "ye", "yeah", "yeppers"]

client = OpenAI(api_key=check_openai_api_key, base_url=openai.base_url)

def resolveTarget():
	global target
	global aliasorkey
	global model_choice
	global client
	global prompt_choice

	if target == "openai":
		aliasorkey = check_openai_api_key()
		apibaseurl = openai.base_url
		model_choice = "gpt-4o-mini"
		prompt_choice = "concisepilot"
	if target == "ooba":
		aliasorkey = "..."
		apibaseurl = "http://127.0.0.1:5000/v1/"
		model_choice = "oobastank"
		prompt_choice = "oobafree"

	client = OpenAI(api_key=aliasorkey, base_url=apibaseurl)

resolveTarget()



def configure_readline():
	# Enable readline history and multi-line editing
	readline.parse_and_bind("set enable-keypad on")
	readline.parse_and_bind("set editing-mode emacs")
	readline.parse_and_bind("set horizontal-scroll-mode off")

def read_file(file_path):
	"""Read the entire content of the given file."""
	try:
		with open(file_path, 'r') as file:
			return file.read()
	except Exception as e:
		print(f"Error reading file {file_path}: {str(e)}")
		return None

def show_help():
	print("""
	Available Commands:
	- exit/quit: Exit the application
	- help/?: Show this help message
	- You can also type messages to send to the assistant
	- Code blocks can be enclosed in ``` or ~~~ to retain formatting
	""")

def show_loading():
	"""Displays a loading animation while waiting for a response."""
	loading_symbols = ['.', '..', '...']
	idx = 0
	while not loading_event.is_set():
		print(f"\rWaiting for response{loading_symbols[idx % len(loading_symbols)]}", end='')
		idx += 1
		time.sleep(0.5)
	# Clear the line when the loading animation stops
	print("\r" + " " * 40, end="")

def chat_with_gpt4(prompt, history=[]):
#	global voice_model
#	global voice_models
#	global multivoice_models
	global model_choice
	# Add the user's input to the history
	history.append({"role": "user", "content": prompt})

	# Start the loading animation in a separate thread
	loading_event.clear()
	loading_thread = threading.Thread(target=show_loading)
	loading_thread.daemon = True  # Allows the thread to be killed when the main program exits
	loading_thread.start()

	try:
		# Send the conversation history to GPT-4 and get a response
		response = client.chat.completions.create(
			model=model_choice,
			messages=history,
		)

		assistant_reply = ""

		# Extract the assistant's reply
		assistant_reply = response.choices[0].message.content

		readable_reply = sanitize_input(assistant_reply).replace('*','')

		history.append({"role": "assistant", "content": assistant_reply})
	finally:
		# Ensure the loading animation is stopped
		loading_event.set()
		loading_thread.join()  # Wait for the loading thread to finish



#	Voice Output with PiperTTS - requires directories models and outputs alongside chatwgpt, not implemented in public release
#		with open(f"{output_dir}/tmp.txt", "w") as f:
#			f.write(readable_reply)

#		if voice_model in multivoice_models:
#			command = ["bash", "-c", f"cat {output_dir}/tmp.txt | piper -m {models_dir}/{voice_model} -s {speaker} -f {output_dir}/tmp.wav"
#		]
#		else:
#			command = ["bash", "-c", f"cat {output_dir}/tmp.txt | piper -m {models_dir}/{voice_model} -f {output_dir}/tmp.wav"
#		]

#		if voice_model in multivoice_models:
#			print(f"\r{voice_model} in multivoice")
#		else:
#			print(f"\r{voice_model} not in multivoice")

#		command = ["bash", "-c", f"cat {output_dir}/tmp.txt | piper -m {models_dir}/{voice_model} -s {speaker} -f {output_dir}/tmp.wav"
#		]
#		print(f"\rGenerating Audio Samples")
#		subprocess.run(command)

	return assistant_reply, history

def multi_line_input(end_delimiters=["```","'''", "~~~"]):
	
	# Captures input and handles multi-line blocks with delimiters. Sends immediately outside blocks.
	
	# Parameters:
	# - prompt: The prompt to display to the user.
	# - end_delimiters: List of delimiters to start/stop multi-line blocks.
	
	# Returns:
	# - A string containing the entire input, with multi-line blocks correctly included.
	
	user_input = []  # Store the whole input (both regular and block input)
	inside_block = False  # Track whether we are inside a code block

	#print(prompt, end="", flush=True)

	while True:
		# Capture each line of input
		line = input()

		# Check if the line contains any end delimiters
		if any(line.strip() == delimiter for delimiter in end_delimiters):
			if inside_block:
				# We are closing the block, include the line and stop block mode
				user_input.append(line)
				inside_block = False
				continue  # Continue and allow to process the input after this
			else:
				# We are opening a block, include the line and enter block mode
				user_input.append(line)
				inside_block = True
				continue  # Keep collecting input inside the block

		if inside_block:
			# While inside the block, continue collecting lines
			user_input.append(line)
		else:
			# Outside the block, if the line is empty or "enter" is pressed, send input
			if line.strip() == "":
				break  # Exit on empty line and return input
			else:
				user_input.append(line)
				break  # Exit on regular input and send message

	return "\n".join(user_input)  # Join all lines into a single string



def sanitize_input(user_input):
	# Escape quotes and remove other problematic characters
	sanitized = re.sub(r'[^\x20-\x7E]+', '', user_input)
	
	# Preserve code blocks with whitespace
	def preserve_code_blocks(match):
		code_content = match.group(1)
		# Convert spaces in code block to HTML non-breaking spaces
		code_content = code_content.replace(' ', '&nbsp;').replace('\n', '<br>')
		return f'<code>{code_content}</code>'

	sanitized = re.sub(r'```(.*?)```', preserve_code_blocks, sanitized, flags=re.DOTALL)
	sanitized = re.sub(r'~~~(.*?)~~~', preserve_code_blocks, sanitized, flags=re.DOTALL)

	return sanitized

def printDebug():
	global target
	global model_choice
	global prompt_choice
#	global voice
#	global voice_model
	global speaker
	global oneout
	global script_dir
	global model_dir
	global output_dir
	teststr = "testprint"

	# Debug
	print(f"Target = {target}")
	print(f"Model = {model_choice}")
	print(f"System Message = {prompt_choice}")
#	print(f"Voice = {voice}")
#	print(f"Voice Model = {voice_model}")
	print(f"Speaker = {speaker}")
	print(f"Oneout = {oneout}")
	print(f"script_dir = {script_dir}")
	print(f"models_dir = {models_dir}")
	print(f"output_dir = {output_dir}")

def main():
	printDebug()
	global target
	global prompts
	global prompt_choice
	global model_choice
	# Configure readline for better terminal handling
	configure_readline()

	# Initialize and assign first_message
	first_message = ''

	# Check if there are any arguments
	if args.message:
		first_message = sanitize_input(args.message)  # First user-provided argument

	# Initialize conversation history
	history = []

	# Add system message to history
	history.append({"role": "system", "content": prompts[prompt_choice]})

	# Begin taking input from args or user and loop
	while True:
		try:
			# Check if first_message was passed via command line args
			if first_message == "":
				print(f"{Colors.OKBLUE}You:{Colors.ENDC}")
				msg2gpt = sanitize_input(multi_line_input())
			else:
				# Check if the message is a filename
				if os.path.isfile(first_message):
					# It's a file, read the contents
					file_content = read_file(first_message)
					if file_content is not None:
						# Process the file content
						msg2gpt = sanitize_input(file_content)
					else:
						# Skip processing if file can't be read
						msg2gpt = ""
				else:
					# It's a regular string message
					msg2gpt = sanitize_input(first_message)
				# Reset after the first message
				first_message = ""

			if msg2gpt.lower() in ["exit", "quit"]:
				break

			elif msg2gpt.lower() in ['/t', '/target']:
				for index, tg in enumerate(targets):
					print(f"{index}: {tg}")
				target_choice = input("Which target? (index):")
				if int(target_choice) in [0,1]:
					target = targets[int(target_choice)]
					print(f"Target successfully changed")
					resolveTarget()
					printDebug()
					continue
				else:
					printDebug()
					print("ERROR: invalid input continuing with")
					continue

#			elif msg2gpt.lower() in ["/v", "/voice"]:
#				OobaFunctions.setMultiVoiceModel()
#				continue

			elif msg2gpt.lower() in ["/p","/sysmsg"]:
				pq = OobaFunctions.setSystemMessage()
				if pq in sysmsgs.keys():
					prompt_choice = pq
					history = []
					history.append({"role": "system", "content": prompts[prompt_choice]})
				else:
					print(f"something went wrong before return to main")
				printDebug()
				print(f"Starting new conversation with above parameters")
				continue

			elif msg2gpt.lower() in ["/m", "/model"]:
				mq = OobaFunctions.loadModel(target)
				
				if mq is not None:  # Check if the result is a model name
					model_choice = mq
					print(f"Model selected: {model_choice}")
				elif mq is None:  # Handle case where loadModel returns None
					print("Failed to load model.")
				else:
					print("Unexpected result from loadModel.")
				
				printDebug()  # Ensure this function is defined and used as needed
				print("Conversation continuing with above parameters")
				continue

			elif msg2gpt.lower() in ["/k", "/keep"]:
				OobaFunctions.setSaveFiles(teststr)
				continue

			elif msg2gpt.lower() in ["help", "?"]:
				show_help()
				continue

			# Pass to the model
			reply, history = chat_with_gpt4(msg2gpt, history)
			print(f"\n{Colors.ERROR}{model_choice}:{Colors.ENDC}\n {reply}\n")

			# Play that wav file if voice = True
#			if voice:
#				with open(os.devnull, 'w') as devnull:
#					vresult = subprocess.Popen(['aplay', f"{output_dir}/tmp.wav"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#					voutput, verrors = vresult.communicate()
#			if oneout:
#				break
		
		except KeyboardInterrupt:
			print("\nInterrupted by user.")
			break
		except Exception as e:
			print(f"\nAn error occurred:\n {e}")

if __name__ == "__main__":
	main()
