import os
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN", "").strip()
HF_LLM_REPO_ID = os.getenv("HF_LLM_REPO_ID", "mistralai/Mistral-7B-Instruct-v0.2").strip()

UPLOAD_DIR = "storage/uploads"
CHROMA_DIR = "storage/chroma"
