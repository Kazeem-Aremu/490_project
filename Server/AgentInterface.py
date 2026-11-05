"""
Ms. Leslie purchased the team seats but didn't load any credit into our API account.
What i will do is set this up using Open AI api to get over these issues and set it up later.
This solution should be relativly easy to correct when we are able too.

"""
from openai import OpenAI
import json
from dotenv import load_dotenv
import os

class Teacher:
    def __init__(self, AssignmentID = None, StudentID = None):
        load_dotenv()
        ##This will describe the set up for the api key
        self.CLIENT = OpenAI(api_key=os.environ.get("OPEN_AI_KEY"))
        self.MODEL = "gpt-5-mini"
        self.SYSTEM_PROMPT = """
            for now we are testing. Just make Sure that we are able to read your input and output
        """

        self.TOOL_SCHEME = []
        self.TOOLS = {}
        self.messages = [{"role":"system", "content":self.SYSTEM_PROMPT}]

    def runAgent(self):
       while True:
           response = self.getResponse()
           message = self.stripMessage(response)
           self.messages.append(message)

           if not message.tool_calls:
               return message.content

           for tool_call in message.toolCalls:
                result = self.runTool(tool_call)
                self._toolOutput(result, tool_call)

    def runTool(self, tool_call):
        pass
    def _toolOutput(self, result, tool_call):
        return self.messages.append({
            "role":"tool",
            "tool_call_id":tool_call,
            "content":result
        })
    
    def getResponse(self):
        return self.CLIENT.chat.completions.create(
            model = self.MODEL,
            messages = self.messages,
            tools = self.TOOL_SCHEME
        )

    def stripMessage(self, response):
        message = response.choices[0].message
        self.messages.append(message)
        return message

    def addMessage(self, role, content):
        self.messages.append({"role":role, "content":content})
        return self.runAgent()

## this will simply be an example fo the logic to get this running on the client side. At the end when the user closes the program it needs to save this chat.

def main():
    teacher = Teacher()
    response = teacher.getResponse()
    message = teacher.stripMessage(response)

    print(f"Teacher: {message.content}")
    while True:
        userInput = input("You: ")
        if userInput.strip().lower() in ("exit", "quit"):
            break

        reply = teacher.addMessage("user", userInput)
        print(f"Teacher: {reply}")
    



if __name__ == "__main__":
    main()