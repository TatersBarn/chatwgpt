import openai
from openai import OpenAI
import os
import sys
import argparse
import re
import readline
import threading
import time
import curses

prompts = {
	"concisepilot": "You are a quick problem solving assistant for navigating and operating in linux. Give short, concise responses that help the user with any questions or problems they ask about when using linux.",
	"gptlike": "You are an ai chatbot and general purpose assistant being used by a creative and inquisitive person who likes to explore the potentials of their computer use. Please listen to the users requests and go over it thoughtfully, creating an ouline of the request or its challenges on a whiteboard in my your mind, ensuring you consider all angles, potentials, and alternatives when making your response. In your response, first address the problem or question by offering a solution or answer that is direct and concise, before going into more detail about how that first answer works, and then offering at least one alternative. Finally, give the user some considerations for the future-proofing of any solutions provided, including security and stability concerns for questions about programming or linux config. Then continue the conversation with the user, helping them to build their solutions and ideas by asking questions of your own and offering various suggestions that can keep the user building and growing."
}

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
			print(f"Exiting...")
			sys.exit(1)  # Exit the program as the API key is required
		return api_key

parser = argparse.ArgumentParser(description='Chat with ChatGPT or other LLMS with various parameters')
parser.add_argument('-t', '--target', type=str, help='Target for api request choices: openai OR ooba (Default openai)', default='openai')
parser.add_argument('-m', '--model', type=str, help='OpenAI model choices: gpt-4o-mini OR gpt-4o OR gpt-3.5-turbo (Default gpt-4o-mini', default='gpt-4o-mini')
parser.add_argument('message', type=str, nargs='?', default='', help='User Message to begin conversation with LLM')
parser.add_argument('-p', '--prompt', type=str, help='Prompt style choice: concisepilot, gptlike (Default concisepilot)', default='concisepilot')
parser.add_argument('-s', '--stream', type=str2bool, help='[NOT YET IMPLEMENTED Output and conversationhistory are broken when Streaming is True!] Streaming True or False or t or f or 1 or 0 (Default False)', default=False)

args = parser.parse_args()

if args.target not in ['openai','ooba']:
	print(f"ERROR: no interface named {args.target}")
	sys.exit(1)
elif args.target == 'ooba':
	aliasorkey = "..."
	apibaseurl = "http://127.0.0.1:5000/v1/"
	modelChoice = "oobastank"
elif args.target == 'openai':
	aliasorkey = check_openai_api_key()
	apibaseurl = openai.base_url

if args.model not in ['gpt-4o-mini','gpt-4o','gpt-3.5-turbo']:
	print(f"ERROR: no model named {args.model}")
	sys.exit(1)
else:
	modelChoice = args.model

if args.prompt not in ['concisepilot','gptlike']:
	print(f"ERROR: no built in prompt named {args.prompt}")
	sys.exit(1)
else:
	promptChoice = args.prompt

if args.stream not in [True, False]:
	print(f"ERROR: STREAM must be True or False (or t,f,1,0)  not {args.stream}")
	sys.exit(1)
else:
	streaming = args.stream

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

client = OpenAI(api_key=aliasorkey,base_url=apibaseurl)

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
			model=modelChoice,
			messages=history,
			stream=streaming,
		)

		assistant_reply = ""

		if streaming:
			for chunk in response:
				if chunk.choices[0].delta.content is not None:
					print(chunk.choices[0].delta.content, end = " ")
					assistant_reply += chunk.choices[0].delta.content
		else:
			# Extract the assistant's reply
			assistant_reply = response.choices[0].message.content
			history.append({"role": "assistant", "content": assistant_reply})
	finally:
		# Ensure the loading animation is stopped
		loading_event.set()
		loading_thread.join()  # Wait for the loading thread to finish

	return assistant_reply, history

def multi_line_input(end_delimiters=["```", "~~~"]):
	
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


def main():
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
	history.append({"role": "system", "content": prompts[promptChoice]})

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
			elif msg2gpt.lower() in ["help", "?"]:
				show_help()
				continue

			# Pass to the model
			reply, history = chat_with_gpt4(msg2gpt, history)
			if streaming is not True:
				print(f"\n{Colors.ERROR}{modelChoice}:{Colors.ENDC}\n {reply}\n")
			else:
				print(f"\n")
		
		except KeyboardInterrupt:
			print("\nInterrupted by user.")
			break
		except Exception as e:
			print(f"\nAn error occurred:\n {e}")

if __name__ == "__main__":
	main()
