
import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

start = time.perf_counter()

print("Connecting to Gemini...")

stream = client.models.generate_content_stream(
    model="gemini-flash-latest",
    contents="Explain Newton's first law in two sentences."
)

first_chunk = True

for chunk in stream:
    if chunk.text:
        if first_chunk:
            print(
                "\nFirst response delay:",
                round(time.perf_counter() - start, 2),
                "seconds\n"
            )
            first_chunk = False

        print(chunk.text, end="", flush=True)

print("\n\nSpeed test complete.")
