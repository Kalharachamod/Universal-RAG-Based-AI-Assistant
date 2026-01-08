Medical Guideline RAG Chat Bot (Internship-Level)

Tech:
- Streamlit UI
- LangChain
- Hugging Face Embeddings (sentence-transformers)
- Hugging Face LLM (Inference API)
- Chroma (vector DB)
- SQLite (sessions, chat history, logs)

Run:
1) Create venv and install requirements:
   pip install -r requirements.txt

2) Create .env (optional) or enter token in Streamlit sidebar:
   HUGGINGFACEHUB_API_TOKEN=...

3) Start:
   streamlit run app.py
