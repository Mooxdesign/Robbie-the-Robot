import os
from openai import OpenAI

client = OpenAI()

completion = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {
      "role": "system",
      "content": "You are Robbie the Robot, a robot who is being built by Heidi and Heidi's daddy. Your responses should be kind and helpful, and suitable for a second-grade student."
    },
    {
      "role": "user",
      "content": "Who are you?"
    }
  ],
  temperature=0,
  max_tokens=32,
  top_p=1,
  frequency_penalty=0,
  presence_penalty=0
)

message = completion.choices[0].message.content
print(message)
os.system('espeak "'+message+'"')
