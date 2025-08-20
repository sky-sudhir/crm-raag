#!/usr/bin/env python3
"""
Simple test to upload a new document and verify text extraction works.
"""

import asyncio
import aiohttp
import json

# Configuration
BASE_URL = "http://localhost:8080"
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NTU2Njk2NDYsImV4cCI6MTc1NTY3MzI0Niwic3ViIjoiYWU1NDJkMDctZTliMi00ZjMxLWIxMTYtZWE1MjA4MWVlNmI2IiwidGVuYW50IjoibWFjYm9vayIsImVtYWlsIjoic2F1cmFiaGtqaGE5ODExQGdtYWlsLmNvbSIsInJvbGUiOiJST0xFX0FETUlOIn0.SGg-MPhpRw2w8ozxAJT04brBQWKke2oA0BGpINrwolI"

async def test_upload():
    """Test uploading a new document."""
    
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}"
    }
    
    print("🚀 Testing Document Upload with Fixed Text Extraction")
    print("=" * 60)
    
    # First, get categories
    print("\n1️⃣ Getting categories...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/rag/categories", headers=headers) as response:
                if response.status == 200:
                    categories = await response.json()
                    category_id = categories[0]['id'] if categories else None
                    print(f"✅ Using category: {categories[0]['name']}")
                else:
                    print(f"❌ Failed to get categories: {response.status}")
                    return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Create a simple text file for testing
    test_content = """
    This is a test document about Autonomy in foreign/second language learning.
    
    Autonomy in language learning refers to the learner's ability to take charge of their own learning process.
    It involves making decisions about what to learn, how to learn it, and when to learn it.
    
    Key aspects of autonomy include:
    1. Self-direction in learning
    2. Motivation and goal-setting
    3. Self-assessment and reflection
    4. Independent learning strategies
    
    Research shows that autonomous learners are more successful in acquiring foreign languages.
    """
    
    # Create a simple text file
    with open("test_document.txt", "w") as f:
        f.write(test_content)
    
    print("\n2️⃣ Uploading test document...")
    try:
        data = aiohttp.FormData()
        data.add_field('file', 
                      open('test_document.txt', 'rb'),
                      filename='test_document.txt',
                      content_type='text/plain')
        data.add_field('category_id', category_id)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/rag/upload", headers=headers, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Upload successful: {result['message']}")
                    document_id = result['id']
                else:
                    print(f"❌ Upload failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return
    except Exception as e:
        print(f"❌ Error uploading: {e}")
        return
    
    # Wait a bit for processing
    print("\n3️⃣ Waiting for document processing...")
    await asyncio.sleep(5)
    
    # Check document status
    print("\n4️⃣ Checking document status...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/rag/documents/{document_id}/status", headers=headers) as response:
                if response.status == 200:
                    status = await response.json()
                    print(f"✅ Document status: {status['status']}")
                else:
                    print(f"❌ Failed to get status: {response.status}")
    except Exception as e:
        print(f"❌ Error checking status: {e}")
    
    # Test the chat with the new document
    print("\n5️⃣ Testing chat with new document...")
    try:
        chat_data = {
            "query": "What is autonomy in language learning?",
            "top_k": 5,
            "model": "google"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/rag/chat", headers=headers, json=chat_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Chat successful!")
                    print(f"   Response: {result['response'][:200]}...")
                    print(f"   Sources: {result['total_sources']}")
                else:
                    print(f"❌ Chat failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
    except Exception as e:
        print(f"❌ Error in chat: {e}")
    
    # Clean up
    import os
    if os.path.exists("test_document.txt"):
        os.remove("test_document.txt")
    
    print("\n" + "=" * 60)
    print("🎉 Upload Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_upload())
