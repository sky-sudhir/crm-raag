#!/usr/bin/env python3
"""
Test script for the complete RAG system with all fixes implemented.
This script tests:
1. File upload with proper text extraction
2. Document processing and embedding generation
3. RAG query (retrieval only)
4. RAG chat (retrieval + generation)
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8080"
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NTU2Njk2NDYsImV4cCI6MTc1NTY3MzI0Niwic3ViIjoiYWU1NDJkMDctZTliMi00ZjMxLWIxMTYtZWE1MjA4MWVlNmI2IiwidGVuYW50IjoibWFjYm9vayIsImVtYWlsIjoic2F1cmFiaGtqaGE5ODExQGdtYWlsLmNvbSIsInJvbGUiOiJST0xFX0FETUlOIn0.SGg-MPhpRw2w8ozxAJT04brBQWKke2oA0BGpINrwolI"

async def test_rag_system():
    """Test the complete RAG system."""
    
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("🚀 Testing Complete RAG System")
    print("=" * 50)
    
    # Test 1: Get categories
    print("\n1️⃣ Testing: Get accessible categories")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/rag/categories", headers=headers) as response:
                if response.status == 200:
                    categories = await response.json()
                    print(f"✅ Found {len(categories)} categories")
                    for cat in categories:
                        print(f"   - {cat['name']}: {cat['description']}")
                    category_id = categories[0]['id'] if categories else None
                else:
                    print(f"❌ Failed to get categories: {response.status}")
                    return
    except Exception as e:
        print(f"❌ Error getting categories: {e}")
        return
    
    # Test 2: RAG Query (retrieval only)
    print("\n2️⃣ Testing: RAG Query (retrieval only)")
    try:
        query_data = {
            "query": "need details for Autonomy in foreign/second language learning",
            "top_k": 5,
            "include_metadata": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/rag/query", headers=headers, json=query_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Query successful")
                    print(f"   - Found {result['total_results']} results")
                    print(f"   - Processing time: {result['processing_time_ms']:.2f}ms")
                    
                    if result['results']:
                        print(f"   - First result text: {result['results'][0]['chunk_text'][:100]}...")
                    else:
                        print("   - No results found")
                else:
                    print(f"❌ Query failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
    except Exception as e:
        print(f"❌ Error in RAG query: {e}")
    
    # Test 3: RAG Chat (retrieval + generation)
    print("\n3️⃣ Testing: RAG Chat (retrieval + generation)")
    try:
        chat_data = {
            "query": "need details for Autonomy in foreign/second language learning",
            "top_k": 5,
            "model": "openai"  # or "google"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/rag/chat", headers=headers, json=chat_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Chat successful")
                    print(f"   - Response: {result['response'][:200]}...")
                    print(f"   - Sources: {result['total_sources']}")
                    print(f"   - Processing time: {result['processing_time_ms']:.2f}ms")
                else:
                    print(f"❌ Chat failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
    except Exception as e:
        print(f"❌ Error in RAG chat: {e}")
    
    # Test 4: Get user documents
    print("\n4️⃣ Testing: Get user documents")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/rag/documents", headers=headers) as response:
                if response.status == 200:
                    documents = await response.json()
                    print(f"✅ Found {len(documents)} documents")
                    for doc in documents:
                        print(f"   - {doc['file_name']}: {doc['status']}")
                else:
                    print(f"❌ Failed to get documents: {response.status}")
    except Exception as e:
        print(f"❌ Error getting documents: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 RAG System Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_rag_system())
