import os
from langchain_anthropic import ChatAnthropic

def load_env_manually(dotenv_path):
    if os.path.exists(dotenv_path):
        with open(dotenv_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value.strip('"')

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
print(os.path.dirname(__file__))
print(dotenv_path)
load_env_manually(dotenv_path)

anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

print(f"ANTHROPIC_API_KEY: {anthropic_api_key}")

if anthropic_api_key:
    try:
        chat = ChatAnthropic(api_key=anthropic_api_key, model="claude-3-opus-20240229")
        response = chat.invoke("Hello, Claude!")
        print("Claude response:")
        print(response.content)
    except Exception as e:
        print(f"An error occurred: {e}")
else:
    print("ANTHROPIC_API_KEY not found.")
