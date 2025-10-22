"""Test relationship detection with highly similar content"""

import requests
import time
import json

API_URL = "http://localhost:8000"

print("=" * 80)
print("  Testing Relationship Detection")
print("=" * 80)
print()

# Clear existing data
print("Clearing existing data...")
response = requests.delete(f"{API_URL}/admin/clear-all")
print(f"✓ Data cleared\n")

# Test data with high similarity to trigger relationships
TEST_DATA = [
    {
        "title": "Initial Favorite Food",
        "content": "I love pizza, it's my absolute favorite food. I eat pizza at least twice a week.",
        "source": "food_diary_jan.txt"
    },
    {
        "title": "Updated Food Preference",  
        "content": "I love pizza, it's my favorite food. I have pizza almost every week.",  # Very similar to above
        "source": "food_diary_feb.txt"
    },
    {
        "title": "Exercise Habit",
        "content": "I go running every morning at 6 AM for about 30 minutes.",
        "source": "fitness_log_v1.txt"
    },
    {
        "title": "Running Routine",
        "content": "I run every morning at 6 AM, usually for 30 minutes or so.",  # Very similar
        "source": "fitness_log_v2.txt"
    },
    {
        "title": "Book Interest",
        "content": "I'm currently reading '1984' by George Orwell and finding it fascinating.",
        "source": "reading_list.txt"
    },
    {
        "title": "Same Book Mention",
        "content": "I'm reading '1984' by George Orwell right now. It's a fascinating book.",  # Very similar
        "source": "book_notes.txt"
    }
]

print("Ingesting documents with high similarity...")
print()

for i, data in enumerate(TEST_DATA, 1):
    print(f"[{i}/{len(TEST_DATA)}] {data['title']}")
    
    response = requests.post(
        f"{API_URL}/documents/ingest",
        json=data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"    ✓ Status: {result['status']}")
    else:
        print(f"    ✗ Error: {response.status_code}")
    
    time.sleep(1)  # Wait for processing

print()
print("=" * 80)
print("  Graph Statistics")
print("=" * 80)
print()

# Check stats
response = requests.get(f"{API_URL}/graph/stats")
if response.status_code == 200:
    stats = response.json()
    print(f"Total Memories: {stats['total_memories']}")
    print(f"Total Relationships: {stats['total_relationships']}")
    print()
    
    if stats['total_relationships'] > 0:
        print("✅ RELATIONSHIPS DETECTED!")
        print()
        print("Relationship Breakdown:")
        for rel_type, count in stats['relationship_types'].items():
            if count > 0:
                print(f"  - {rel_type.upper()}: {count}")
    else:
        print("⚠️  No relationships detected")
        print()
        print("This might mean:")
        print("  1. Similarity scores are still below thresholds")
        print("  2. Thresholds need to be lowered in .env:")
        print("     SIMILARITY_THRESHOLD_UPDATE=0.70")
        print("     SIMILARITY_THRESHOLD_EXTEND=0.55")

print()
print("=" * 80)
print("  Export Graph for Visualization")
print("=" * 80)
print()

# Export graph
response = requests.get(f"{API_URL}/graph/export")
if response.status_code == 200:
    graph_data = response.json()
    
    with open('knowledge_graph.json', 'w') as f:
        json.dump(graph_data, f, indent=2)
    
    print(f"✓ Graph exported to knowledge_graph.json")
    print(f"  Nodes: {len(graph_data['nodes'])}")
    print(f"  Edges: {len(graph_data['edges'])}")
    
    if graph_data['edges']:
        print()
        print("Sample Relationships:")
        for edge in graph_data['edges'][:3]:
            source = next((n for n in graph_data['nodes'] if n['id'] == edge['source']), None)
            target = next((n for n in graph_data['nodes'] if n['id'] == edge['target']), None)
            if source and target:
                print()
                print(f"  Type: {edge['type'].upper()}")
                print(f"  From: {source['label'][:60]}...")
                print(f"  To: {target['label'][:60]}...")
                print(f"  Confidence: {edge['confidence']:.2f}")

print()
print("=" * 80)
print("  Next Steps")
print("=" * 80)
print()
print("1. Run: python visualize_graph.py")
print("2. Open: graph_visualization.html in your browser")
print("3. See the relationship connections!")
print()

