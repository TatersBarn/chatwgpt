# chatwgpt
Command Line Access to LLMs compatible with OpenAI's API
Note: This project is primarily intended for me to be able to ask GPT models quick questions about linux operation, bash commands, etc. But you can easily just use it to chat with OpenAI models. (Use of the OpenAI API is not free, and having a ChatGPT Premium subscription does not count. The API is charged pay-as-you-go by token use. For many it costs less than ChatGPT Premium

# Considerations
-This is unfinished and independently produced software written by an amateur programmer, use at your own risk.
-This solution currently only interacts with the chat completions endpoint.
-This solution has been updated to the v1 sdk, but i very well may forget to update it further.

# Installation
This script requires use of an OpenAI API key and the OpenAI Python client/library, so install it with
```bash
pip install openai
```
Make sure you have an OpenAI API key environment variable set, you can set for this one shell session with:
```
export OPENAI_API_KEY=[your_key_here]
```
Before calling the script.

### RECOMMENDED
You can add that export line into your .bashrc or .zshrc or whatever shell initialization file to have a persistent use key on the machine.
For more information go and read the openai-python docs for more info and details on how to set your OpenAI API Key https://github.com/openai/openai-python
# Basic use
Simply run
```bash
python3 chatwgpt.py
```
To begin a new conversation with GPT4o-mini, the default model. The default system message instructs the model to respond only to questions about linux operation, and to answer concisely to save you tokens. Conversation history is automatically retained between messages and sent back to the endpoint every round you send.

To end the operation, you can use CTRL+C to send a user interrupt, or you can simply type 'exit' or 'quit'

# Other functionality
## Easy settings changes during runtime
Upon execution settings are taken from taterchat.conf, these settings never get overwritten so you can always reuse the defaults here if you like but if you want you can also use the slash commands:
```
/m or /model   will give you model choices from oobabooga or openai
/t or /target   will allow you to change the target api
/p or /prompt    will allow you to choose from built in prompts or custom ones you add to oobafunctions.py
```
## use these command line arguments for other functionality
### Invoke with initial message
You can open your conversation with your first message in single quotes like this:
```bash
python3 chatwgpt.py 'How do I delete a folder and all of its contents?'
```
### Change system message
If you would rather chat about something other than linux, you can change between built-in system messages (viewable at the top of the python script) with ```-p [promptname]``` or ```--prompt [promptname]```   
As of right now there is no way to call with a custom system message. Feel free to change the system message in the chatwgpt.py file, or add your own multitude of custom prompts
### Change model
You can choose a different openAI GPT model to call with ```-m [modelname]``` or ```--model [modelname]```
### Stream responses (currently broken)
You can activate (currently broken) streaming with ```-s True``` or ```--stream True```
### Call a local LLM compatible with OpenAI API calls
You can call a locally available llm running on 127.0.0.1:5000 (such as Oobabooga/text-generation-webui) with ```-t ooba``` or ```--target ooba```
### send a txt file
You can simply call ```python3 chatwgpt.py textfile.txt``` to send the entire contents of a text file to the model. Input is sanitized but unfortunately sends much of your message as HTML at the moment as that is all I could figure out. 
### See the help message
Call ```python3 chatwgpt.py -h``` or ```python3 chatwgpt.py --help``` to view various usage information
### Single use API key
When called without any arguments and no OPENAI_API_KEY environment variable, you will be given the opportunity to input the API key directly into the terminal for this session only. This is not recommended and was only included for testing

## Make calling easier with an alias
If you like having your concise linux copilot and want it to be even easier to use, open your .bashrc or .zshrc file and add the following line
```
alias chatwgpt='python3 /home/tatersbarn/chatgpt.py'
```

# Conclusions and where to go next
This is a really helpful little tool of mine and I really enjoy the quick ability to ask about a command or pipeline of commands to do a job in a bash shell. I think anyone who uses linux could benefit from it, and you should totally try it if you keep forgetting how to ```chmod +x yourfile.xyz```

Next I want to make a little gui for it that displays rendered markdown, or just a web interface for in a browser. either works.
