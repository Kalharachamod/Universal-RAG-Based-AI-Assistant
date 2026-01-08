#!/usr/bin/env python3
"""
Debug script to test file upload and processing functionality
"""
import os
import sys
from pathlib import Path

# Add the rag module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from rag.utils import save_uploaded_file, ensure_dirs
from rag.ingestion import load_documents

def simulate_file_processing():
    print("=== File Processing Diagnostic ===")
    
    # Create a mock file object to simulate what Flask receives
    class MockFile:
        def __init__(self, name, content=b'test pdf content'):
            self.filename = name
            self.content = content
        
        def getbuffer(self):
            return self.content
            
        def read(self):
            return self.content

    # Test various problematic filenames
    test_files = [
        "OMC Report Sample - Cardio.pdf",
        "simple.pdf",
        "file with spaces.pdf",
        "file_with_underscores.pdf",
        "file-with-dashes.pdf"
    ]
    
    # Create a session ID for testing
    import uuid
    session_id = str(uuid.uuid4())
    
    print(f"Testing with session ID: {session_id}")
    print()
    
    for filename in test_files:
        print(f"Testing file: {filename}")
        mock_file = MockFile(filename)
        
        try:
            # Step 1: Save the file
            print(f"  1. Saving file...")
            path = save_uploaded_file(mock_file, session_id)
            print(f"     Saved to: {path}")
            print(f"     Path type: {type(path)}")
            print(f"     Path string: '{str(path)}'")
            print(f"     Ends with .pdf: {str(path).lower().endswith('.pdf')}")
            print(f"     Ends with .docx: {str(path).lower().endswith('.docx')}")
            
            # Step 2: Check if file exists
            path_exists = Path(path).exists()
            print(f"     File exists: {path_exists}")
            
            if path_exists:
                # Step 3: Try to load the document
                print(f"  2. Loading document...")
                docs = load_documents(path)
                print(f"     Successfully loaded {len(docs)} documents")
            else:
                print(f"     ERROR: File does not exist at the saved path")
                
        except Exception as e:
            print(f"     ERROR: {str(e)}")
        
        print()

if __name__ == "__main__":
    ensure_dirs()
    simulate_file_processing()