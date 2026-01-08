# Universal-RAG-Based-AI-Assistant

This is a Retrieval-Augmented Generation (RAG) AI assistant that enables document-based question answering using LangChain, Hugging Face LLMs, and ChromaDB. Implemented semantic search, context-grounded responses, a Streamlit interface, and SQLite-based session management.

## Features

- 🤖 Universal AI assistant for general knowledge queries
- 📚 Document upload capability (PDF, DOCX, TXT)
- 💬 Interactive chat interface with contextual responses
- 🔗 Seamless integration with Hugging Face LLMs
- 🗄️ Vector database storage for efficient information retrieval

## Tech Stack

- **Frontend**: Streamlit
- **Frameworks & Libraries**: LangChain, sentence-transformers, Hugging Face, ChromaDB, SQLite
- **Document Processing**: PyPDF, Docx2txt, Sentence Transformers
- **AI Models**: Hugging Face Transformers

## Installation

1) Clone the repository:
   ```bash
   git clone https://github.com/Kalharachamod/Universal-RAG-Based-AI-Assistant.git
   cd Universal-RAG-Based-AI-Assistant
   ```

2) Create venv and install requirements:
   ```bash
   pip install -r requirements.txt
   ```

3) Create .env (optional) or enter token in Streamlit sidebar:
   ```
   HUGGINGFACEHUB_API_TOKEN=your_token_here
   ```

4) Start the application:
   ```bash
   streamlit run app.py
   ```

## Usage

- Upload documents to enhance the assistant's knowledge
- Ask questions related to your documents or general questions
- The assistant will provide contextual answers based on your documents or general knowledge

## License

This project is licensed under the MIT License.