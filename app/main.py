import argparse
import os
import sys
import json
import subprocess
from openai import OpenAI

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")


def chat_client(chat_message):
    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    chat = client.chat.completions.create(
        model="anthropic/claude-haiku-4.5",
        messages=chat_message,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "Read",
                    "description": "Read and return the contents of a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string","description": "The path to the file to read"}
                        },
                "required": ["file_path"]
                    }
                }
            },            
            {
                "type": "function",
                "function": {
                    "name": "Write",
                    "description": "Write content to a file",
                    "parameters": {
                        "type": "object",
                        "required": ["file_path", "content"],
                        "properties": {
                            "file_path": {
                            "type": "string",
                            "description": "The path of the file to write to"
                        },
                        "content": {"type": "string","description": "The content to write to the file"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Bash",
                    "description": "Execute a shell command",
                    "parameters": {
                        "type": "object",
                        "required": ["command"],
                        "properties": {
                            "command": {"type": "string","description": "The command to execute"}
                        }
                    }
                }
            }
        ]
    )

    return chat


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    # 1: original message from user prompt
    chat_messsage=[{"role": "user", "content": args.p}]

    chat=chat_client(chat_messsage)
    
    if not chat.choices or len(chat.choices) == 0:
        raise RuntimeError("no choices in response")

    # You can use print statements as follows for debugging, they'll be visible when running tests.
    #print("Logs from your program will appear here!", file=sys.stderr)

    # Uncomment the following line to pass the first stage
    #print(chat.choices[0].message.content)

    # enter the loop of using tools

    while chat.choices[0].finish_reason=='tool_calls':
        # 2. add what the LLM is request to the message
        chat_messsage.append(chat.choices[0].message)
        
        # call all the tools
        for tc in chat.choices[0].message.tool_calls or []:
            tool_call_result={}

            # this is defined under "required": ["file_path", "content"]
            func_args=json.loads(tc.function.arguments)
            
            # read tool
            if tc.function.name=="Read":
                with open (func_args['file_path'],'r') as f:
                    tool_call_result['content']=f.read()
            # write tool
            elif tc.function.name=="Write":
                with open (func_args['file_path'],'w', encoding='utf-8') as file:
                    file.write(func_args['content'])
                tool_call_result['content'] = f"Successfully wrote to {func_args['file_path']}"
            # bash tool
            elif tc.function.name=="Bash":
                try:
                    bash_result=subprocess.run([func_args['command']], 
                                           shell=True,
                                           capture_output=True,
                                           text=True,
                                           check=True)
                    tool_call_result['content'] =bash_result.stdout
                except subprocess.CalledProcessError as e:
                    tool_call_result['content'] =f"Error occurred: {e.stderr}"

            tool_call_result['role']='tool'
            tool_call_result['tool_call_id']=tc.id

            # 3. add LLM tool call results to the message
            chat_messsage.append(tool_call_result)
        
        # rerun into LLM with results from tools
        chat=chat_client(chat_messsage)

    print(chat.choices[0].message.content)
    


if __name__ == "__main__":
    main()
