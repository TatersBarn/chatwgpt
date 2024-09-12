# chatwgpt
Command Line Access to LLMs compatible with OpenAI's API
Note: This project is primarily intended for me to be able to ask GPT models quick questions about linux operation, bash commands, etc.
# Considerations
This is unfinished and independently produced software written by an amateur programmer, use at your own risk.
# Installation
This script requires use of an OpenAI API key and the OpenAI Python client/library, so install it with
```bash
pip install openai
```
Read the openai-python docs for more info and details on how to set your OpenAI API Key https://github.com/openai/openai-python
# Basic use
Simply run
```bash
python3 chatwgpt.py
```
To begin a new conversation with GPT4o-mini, the default model. The default system message instructs the model to respond only to questions about linux operation, and to answer concisely to save you tokens. Conversation history is automatically retained between messages and sent back to the endpoint every round you send.

To end the operation, you can use CTRL+C to send a user interrupt, or you can simply type 'exit' or 'quit'

# other functionality
## Invoke with initial message
You can open your conversation with your first message in single quotes like this:
```bash
python3 chatwgpt.py 'How do I delete a folder and all of its contents?'
```
## Change system message
If you would rather chat about something other than linux, you can change between built-in system messages (viewable at the top of the python script) with ```-p [promptname]``` or ```--prompt [promptname]```   
As of right now there is no way to call with a custom system message. Feel free to change the system message in the chatwgpt.py file, or add your own multitude of custom prompts
## Change model
You can choose a different openAI GPT model to call with ```-m [modelname]``` or ```--model [modelname]```
## Stream responses
You can activate (currently broken) streaming with ```-s True``` or ```--stream True```
## Call a local LLM compatible with OpenAI API calls
You can call a locally available llm running on 127.0.0.1:5000 (such as Oobabooga/text-generation-webui) with ```-t ooba``` or ```--target ooba```
## send a txt file
You can simply call ```python3 chatwgpt.py textfile.txt``` to send the entire contents of a text file to the model. Input is sanitized but unfortunately sends much of your message as HTML at the moment as that is all I could figure out. 
# Conclusions and where to go next
This is a really helpful little tool of mine and I really enjoy the quick ability to ask about a command or pipeline of commands to do a job in a bash shell. I think anyone who uses linux could benefit from it, and you should totally try it if you keep forgetting how to ```chmod +x yourfile.xyz```

Next I want to make a little gui for it that displays rendered markdown, or just a web interface for in a browser. either works.
