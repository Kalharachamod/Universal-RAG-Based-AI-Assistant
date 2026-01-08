from langchain_community.vectorstores import Chroma
from pathlib import Path
import os

def get_embeddings():
    # Try to use HuggingFaceEmbeddings first, fallback to Inference API if sentence-transformers not available
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    except (ImportError, Exception) as e:
        # Fallback to HuggingFace Inference API embeddings (requires HF token)
        try:
            from langchain_huggingface import HuggingFaceInferenceEmbeddings
            hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN", "")
            if hf_token:
                return HuggingFaceInferenceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    huggingfacehub_api_token=hf_token
                )
            else:
                raise ImportError(
                    "sentence-transformers not available and no HUGGINGFACEHUB_API_TOKEN found. "
                    "Either install sentence-transformers or set HUGGINGFACEHUB_API_TOKEN."
                )
        except ImportError:
            raise ImportError(
                "Could not import sentence_transformers. Please install it with: pip install sentence-transformers"
            )

def build_vectorstore(chunks, persist_dir: str):
    Path(persist_dir).mkdir(parents=True, exist_ok=True)
    embeddings = get_embeddings()
    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir
    )
    vectordb.persist()
    return vectordb

def load_vectorstore(persist_dir: str):
    embeddings = get_embeddings()
    return Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings
    )

from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain.schema import HumanMessage, SystemMessage
from rag.prompts import SYSTEM_PROMPT

def get_hf_llm(hf_token: str, repo_id: str):
    if not hf_token:
        raise ValueError("Missing HUGGINGFACEHUB_API_TOKEN.")

    # Build a conversational endpoint then wrap it as a chat model
    endpoint_llm = HuggingFaceEndpoint(
        repo_id=repo_id,
        huggingfacehub_api_token=hf_token,
        task="conversational",
        temperature=0.1,
        max_new_tokens=400,
    )
    return ChatHuggingFace(llm=endpoint_llm)

def build_qa_chain(vectordb, llm):
    retriever = vectordb.as_retriever(search_kwargs={"k": 4})

    # Custom QA chain that formats as conversation for Mistral
    class ConversationalQA:
        def __init__(self, llm, retriever):
            self.llm = llm
            self.retriever = retriever
        
        def __call__(self, inputs):
            query = inputs.get("query", inputs.get("question", ""))
            
            # Retrieve relevant documents
            docs = self.retriever.get_relevant_documents(query)
            
            # Format context from documents
            context_text = "\n\n".join([
                f"[Document {i+1}]: {doc.page_content[:400]}..."
                for i, doc in enumerate(docs[:4])
            ])
            
            # Format as conversation for Mistral (conversational task)
            # Mistral expects messages in conversational format
            prompt_content = f"""Based on the following context from medical guidelines:

{context_text}

Question: {query}

Please provide an answer based only on the context provided. If the answer is not in the context, say 'Not found in the uploaded documents.'"""
            
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=prompt_content)
            ]
            
            # Invoke the LLM with conversational format
            try:
                response = self.llm.invoke(messages)
                answer = response.content if hasattr(response, 'content') else str(response)
            except Exception as e:
                # Fallback: try as string prompt
                prompt_text = f"""{SYSTEM_PROMPT}

Context from documents:
{context_text}

Question: {query}

Answer:"""
                response = self.llm.invoke(prompt_text)
                answer = response.content if hasattr(response, 'content') else str(response)
            
            return {
                "result": answer,
                "source_documents": docs
            }
    
    return ConversationalQA(llm, retriever)
