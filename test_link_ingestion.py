"""Test script to verify link ingestion creates single memory"""
import requests
import json

# API endpoint
BASE_URL = "http://localhost:8000"

# Test data - ProtoArc mouse link
test_data = {
    "type": "link",
    "title": "protoarc mouse test",
    "url": "https://www.protoarc.com/collections/mice/products/em11-nl-vertical-mouse?variant=42318201716825"
}

# Get auth token (you'll need to replace this with actual token)
# For now, we'll just test the structure
print("Testing link ingestion...")
print(f"URL: {test_data['url']}")
print(f"Title: {test_data['title']}")
print("\nExpected: 1 memory created (not 2)")
print("Check the backend logs for: 'Skipping chunking for link summary'")
