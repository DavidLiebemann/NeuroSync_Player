from dotenv import load_dotenv
import os


def load_openai_api_key():
    load_dotenv()
    return os.getenv('OPENAI_API_KEY')
