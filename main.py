from fastapi import FastAPI, UploadFile, File
import openai
import os
import aiofiles
from dotenv import load_dotenv
import logging
import uvicorn

# Load environment variables
load_dotenv()
openai_api_key = os.environ.get("OPENAI_API_KEY")

# Constants
TEMP_FILE_PREFIX = "temp_"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000

# Initialize FastAPI app and OpenAI client
app = FastAPI()
client = openai.OpenAI(api_key=openai_api_key)

# Configure logging
logging.basicConfig(level=logging.INFO)


async def convert_speech_to_text(file_path: str) -> str:
    """
    Convert speech to text using OpenAI's Whisper.
    """
    try:
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                response_format="text",
                language="en"
            )
        return transcript
    except Exception as e:
        logging.error(f"Error in convert_speech_to_text: {e}")
        return ""


async def analyze_text(text: str) -> str:
    """
    Analyze the text using OpenAI's GPT-3.5 API and categorize it.
    """
    prompt = ("Please analyze the following text and categorize it into one of the following "
              "categories: 'harassment', 'abuse', 'theft', 'fraud', 'lie', or 'safe'. "
              f"The text is: '{text}'. Respond with only one word from the categories. "
              "If no illegal content is detected, respond with 'safe'.")

    try:
        response = client.completions.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=5
        )
        category = response.choices[0].text.strip()
        return category
    except Exception as e:
        logging.error(f"Error in analyze_text: {e}")
        return "Error"


@app.post("/analyze-voice/")
async def analyze_voice(file: UploadFile = File(...)) -> dict:
    """
    Endpoint to analyze voice file for specific categories.
    """
    temp_file_path = TEMP_FILE_PREFIX + file.filename

    try:
        async with aiofiles.open(temp_file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)

        text = await convert_speech_to_text(temp_file_path)
        category = await analyze_text(text)

        os.remove(temp_file_path)
        return {"category": category}
    except Exception as e:
        logging.error(f"Error in analyze_voice: {e}")
        return {"category": "Error"}


if __name__ == "__main__":
    uvicorn.run(app, host=DEFAULT_HOST, port=DEFAULT_PORT)
