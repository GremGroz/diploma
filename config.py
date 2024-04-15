from dotenv import load_dotenv
import os
import google.generativeai as genai

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

generation_config=genai.types.GenerationConfig(
                    max_output_tokens=10240,
                    temperature=0.1,
                    top_p=1,
                    top_k=1
                )
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')