import streamlit as st
from rag.config import HF_TOKEN, HF_LLM_REPO_ID, CHROMA_DIR
from rag.utils import ensure_dirs
from rag.db import init_db, create_session, log_document, log_message, log_query, get_recent_messages
from rag.ingestion import load_documents, chunk_documents
from rag.retrieval import build_vectorstore, load_vectorstore, get_hf_llm, build_qa_chain
import os
from pathlib import Path
import uuid

# Initialize
ensure_dirs()
init_db()

# Session state initialization
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    create_session(st.session_state.session_id)

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'vectorstore_exists' not in st.session_state:
    st.session_state.vectorstore_exists = False

# Streamlit UI
st.set_page_config(page_title="🤖 Universal AI Assistant", page_icon="🤖", layout="wide")

st.title("🤖 Universal AI Assistant")

# Sidebar for file upload
with st.sidebar:
    st.header("📚 Knowledge Base")
    
    # Token status
    if HF_TOKEN.strip():
        st.success("✅ Token loaded")
    else:
        st.error("❌ Token missing in .env file")
        st.info("Please set HUGGINGFACEHUB_API_TOKEN in your .env file")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Upload documents to enhance knowledge", 
        type=['pdf', 'docx', 'txt'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        if st.button("Process Documents"):
            try:
                if not HF_TOKEN:
                    st.error("Hugging Face token not found. Please set HUGGINGFACEHUB_API_TOKEN in your .env file.")
                else:
                    # Save and process files
                    all_docs = []
                    for uploaded_file in uploaded_files:
                        # Create temp file
                        import tempfile
                        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                            tmp_file.write(uploaded_file.read())
                            tmp_path = tmp_file.name
                        
                        # Load documents
                        docs = load_documents(tmp_path)
                        all_docs.extend(docs)
                        
                        # Log document
                        log_document(st.session_state.session_id, uploaded_file.name, tmp_path)
                    
                    if all_docs:
                        # Chunk documents
                        chunks = chunk_documents(all_docs, chunk_size=800, chunk_overlap=150)
                        
                        # Build vectorstore
                        persist_dir = f"{CHROMA_DIR}/{st.session_state.session_id}"
                        build_vectorstore(chunks, persist_dir=persist_dir)
                        
                        st.session_state.vectorstore_exists = True
                        st.success(f"✅ Processed {len(uploaded_files)} file(s) and created {len(chunks)} knowledge chunks!")
                    else:
                        st.error("No documents processed successfully.")
                        
            except Exception as e:
                st.error(f"Error processing documents: {str(e)}")
    
    # Status
    st.divider()
    st.subheader("📊 Status")
    persist_dir = f"{CHROMA_DIR}/{st.session_state.session_id}"
    vectorstore_exists = Path(persist_dir).exists() and any(Path(persist_dir).iterdir())
    st.session_state.vectorstore_exists = vectorstore_exists
    
    if vectorstore_exists:
        st.success("✅ Custom knowledge base ready")
    else:
        st.info("💡 Upload documents to enhance my knowledge")

# Main chat interface
if not st.session_state.vectorstore_exists:
    st.info("📚 Upload documents to enhance my knowledge, or ask general questions below.")
else:
    st.success("📖 Knowledge base loaded. I can now answer questions based on your documents.")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me anything - I'm here to help with any questions you have..."): 
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        try:
            if not HF_TOKEN:
                response = "Hugging Face token not found. Please set HUGGINGFACEHUB_API_TOKEN in your .env file."
            else:
                persist_dir = f"{CHROMA_DIR}/{st.session_state.session_id}"
                
                if Path(persist_dir).exists() and st.session_state.vectorstore_exists:
                    # Load vectorstore and get response based on documents
                    vectordb = load_vectorstore(persist_dir)
                    llm = get_hf_llm(hf_token=HF_TOKEN, repo_id=HF_LLM_REPO_ID)
                    qa = build_qa_chain(vectordb, llm)
                    
                    result = qa({"query": prompt})
                    response = result["result"]
                else:
                    # Use general LLM without document context
                    llm = get_hf_llm(hf_token=HF_TOKEN, repo_id=HF_LLM_REPO_ID)
                    response = llm.invoke(prompt)
                
                # Log messages
                log_message(st.session_state.session_id, "user", prompt)
                log_message(st.session_state.session_id, "assistant", response)
                log_query(st.session_state.session_id, prompt, response)
            
            st.markdown(response)
        except Exception as e:
            st.error(f"Error processing request: {str(e)}")
            response = f"Error: {str(e)}"
    
    # Add AI response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Display recent messages
if st.session_state.messages:
    st.sidebar.divider()
    st.sidebar.subheader("💬 Recent Conversations")
    recent_msgs = get_recent_messages(st.session_state.session_id, limit=5)
    for msg in recent_msgs:
        if len(msg) >= 3:  # Ensure msg has at least 3 elements
            role = "👤" if msg[1] == "user" else "🤖"
            st.sidebar.text(f"{role} {msg[2][:50]}...")