from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import uuid
import os
from pathlib import Path

# Import the RAG modules
from rag.config import HF_TOKEN, HF_LLM_REPO_ID, CHROMA_DIR
from rag.utils import save_uploaded_file, ensure_dirs
from rag.db import init_db, create_session, log_document, log_message, log_query, get_recent_messages
from rag.ingestion import load_documents, chunk_documents
from rag.retrieval import build_vectorstore, load_vectorstore, get_hf_llm, build_qa_chain

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for all origins
app.secret_key = os.environ.get('SECRET_KEY', 'fallback_secret_key')
ensure_dirs()
init_db()

# Initialize session
@app.before_request
def initialize_session():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        create_session(session['session_id'])

@app.route('/')
def index():
    session_id = session['session_id']
    persist_dir = f"{CHROMA_DIR}/{session_id}"
    vectorstore_exists = Path(persist_dir).exists() and any(Path(persist_dir).iterdir())
    
    return render_template('index.html', 
                          vectorstore_exists=vectorstore_exists,
                          hf_token_status=bool(HF_TOKEN.strip()))

@app.route('/process_documents', methods=['POST'])
def process_documents():
    try:
        if not HF_TOKEN:
            return jsonify({'error': 'Hugging Face token not found. Please set HUGGINGFACEHUB_API_TOKEN in your .env file.'}), 400
        
        if 'files' not in request.files:
            return jsonify({'error': 'No files uploaded'}), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400
        
        session_id = session['session_id']
        persist_dir = f"{CHROMA_DIR}/{session_id}"
        
        all_docs = []
        for file in files:
            if file and file.filename != '':
                # Validate file extension with more robust checking
                filename_lower = file.filename.lower().strip()
                if not (filename_lower.endswith('.pdf') or filename_lower.endswith('.docx')):
                    return jsonify({'error': f'File {file.filename} is not supported. Only PDF and DOCX files are allowed.'}), 400
                
                path = save_uploaded_file(file, session_id)
                log_document(session_id, file.filename, path)
                
                # Debug: print the path to see what was saved
                print(f"Processing file path: {path}")
                print(f"File path ends with .pdf: {str(path).lower().endswith('.pdf')}")
                print(f"File path ends with .docx: {str(path).lower().endswith('.docx')}")
                
                # Try to load documents and catch specific errors
                try:
                    docs = load_documents(path)
                    all_docs.extend(docs)
                except ValueError as ve:
                    print(f"Error loading document {path}: {str(ve)}")
                    print(f"File path exists: {Path(path).exists()}")
                    if "Only PDF and DOCX are supported" in str(ve):
                        return jsonify({'error': f'File {file.filename} could not be processed. The file extension might be incorrect or the file may be corrupted. Please verify it is a valid PDF or DOCX file.'}), 400
                    else:
                        raise ve
        
        if not all_docs:
            return jsonify({'error': 'No valid documents processed'}), 400
        
        chunks = chunk_documents(all_docs, chunk_size=800, chunk_overlap=150)
        build_vectorstore(chunks, persist_dir=persist_dir)
        
        return jsonify({
            'success': True,
            'message': f'Processed {len(files)} file(s) and created {len(chunks)} knowledge chunks.',
            'chunk_count': len(chunks)
        })
    except Exception as e:
        print(f"Error processing documents: {str(e)}")
        return jsonify({'error': f'Error processing documents: {str(e)}'}), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        if not HF_TOKEN:
            return jsonify({'error': 'Hugging Face token not found. Please set HUGGINGFACEHUB_API_TOKEN in your .env file.'}), 400
        
        session_id = session['session_id']
        persist_dir = f"{CHROMA_DIR}/{session_id}"
        
        if not Path(persist_dir).exists():
            return jsonify({'error': 'Vector store not found. Please upload and process documents first.'}), 400
        
        try:
            vectordb = load_vectorstore(persist_dir)
        except Exception as e:
            return jsonify({'error': f'Error loading vector store: {str(e)}'}), 500
        
        try:
            llm = get_hf_llm(hf_token=HF_TOKEN, repo_id=HF_LLM_REPO_ID)
            qa = build_qa_chain(vectordb, llm)
            
            result = qa({"query": user_message})
            answer = result["result"]
            
            # Log messages
            log_message(session_id, "user", user_message)
            log_message(session_id, "assistant", answer)
            log_query(session_id, user_message, answer)
            
            return jsonify({
                'response': answer,
                'message': user_message
            })
        except Exception as e:
            print(f"Error in chat processing: {str(e)}")
            return jsonify({'error': f'Error processing request: {str(e)}'}), 500
    except Exception as e:
        print(f"Unexpected error in chat: {str(e)}")
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/status')
def status():
    try:
        session_id = session['session_id']
        persist_dir = f"{CHROMA_DIR}/{session_id}"
        vectorstore_exists = Path(persist_dir).exists() and any(Path(persist_dir).iterdir())
        
        return jsonify({
            'vectorstore_exists': vectorstore_exists,
            'session_id': session_id
        })
    except Exception as e:
        print(f"Error in status check: {str(e)}")
        return jsonify({
            'vectorstore_exists': False,
            'session_id': None,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000, threaded=True)