from langchain_anthropic import ChatAnthropic

from langchain_core.messages import AIMessage, HumanMessage

import json
from dotenv import load_dotenv

"""claude-3-7-sonnet-20250219
claude-3-5-sonnet-20241022
claude-3-5-haiku-20241022
claude-3-5-sonnet-20240620"""

load_dotenv()

model = ChatAnthropic(model='claude-3-5-haiku-20241022')

if __name__ == "__main__":
    messages = [
        {
            "role": "user",
            "content": "What is the capital of France?"
        },
    ]
    response = model.invoke(input=messages)
    print(response.content)
    messages.append(AIMessage(content=response.content))
    messages.append(HumanMessage(content="What is there to do in that city?"))
    response = model.invoke(input=messages)
    print(response.content)
