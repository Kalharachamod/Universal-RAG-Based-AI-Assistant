from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

def load_documents(file_path: str):
    lower = file_path.lower()
    if lower.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif lower.endswith(".docx"):
        loader = Docx2txtLoader(file_path)
    else:
        raise ValueError("Only PDF and DOCX are supported.")
    return loader.load()

def chunk_documents(docs, chunk_size: int = 800, chunk_overlap: int = 150):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return splitter.split_documents(docs)
