"""Ingest sample data via API"""

import requests
import json
import time

API_URL = "http://localhost:8000"

# Sample data  
SAMPLE_DATA = [
    {
        "title": "Food Preferences - Initial",
        "content": "I love Italian food, especially pasta carbonara and tiramisu for dessert. I usually eat out at Italian restaurants twice a month.",
        "source": "personal_journal.txt"
    },
    {
        "title": "Food Preferences - Updated",
        "content": "I've switched to a mostly plant-based diet. I now prefer Mediterranean cuisine with lots of vegetables, hummus, and falafel instead of pasta.",
        "source": "health_goals.txt"
    },
    {
        "title": "Exercise Routine",
        "content": "I go to the gym three times a week, focusing on cardio and strength training. My goal is to run a 5K by the end of the year.",
        "source": "fitness_tracker.txt"
    },
    {
        "title": "Hobbies and Interests",
        "content": "I enjoy reading science fiction novels, particularly works by Isaac Asimov and Philip K. Dick. I also like playing chess online and hiking on weekends.",
        "source": "personal_notes.txt"
    },
    {
        "title": "Reading List",
        "content": "Currently reading 'The Foundation' series by Asimov. I've finished 'Do Androids Dream of Electric Sheep?' and loved it. Next on my list is 'Dune' by Frank Herbert.",
        "source": "books.txt"
    },
    {
        "title": "Weekend Activities",
        "content": "Last weekend I went hiking in the mountains and took some amazing photos. I love being in nature and disconnecting from technology for a few hours.",
        "source": "weekend_diary.txt"
    },
    {
        "title": "Learning Goals",
        "content": "I'm learning Spanish through Duolingo and practicing for 30 minutes daily. I also want to learn to play the guitar this year.",
        "source": "goals_2024.txt"
    },
    {
        "title": "Travel Plans",
        "content": "Planning a trip to Japan next spring. I want to visit Tokyo, Kyoto, and experience the cherry blossom season. Also interested in trying authentic ramen and sushi.",
        "source": "travel_plans.txt"
    },
    {
        "title": "Morning Routine",
        "content": "I wake up at 6 AM, meditate for 10 minutes, then have a healthy breakfast with green tea. This routine has helped me feel more energized throughout the day.",
        "source": "daily_habits.txt"
    }
]

print("=" * 80)
print("  Ingesting Sample Data via API")
print("=" * 80)
print()

for i, data in enumerate(SAMPLE_DATA, 1):
    print(f"[{i}/{len(SAMPLE_DATA)}] Ingesting: {data['title']}")
    
    response = requests.post(
        f"{API_URL}/documents/ingest",
        json=data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"    ✓ Created {len(result['memory_ids'])} memory/memories")
    else:
        print(f"    ✗ Error: {response.status_code} - {response.text}")
    
    time.sleep(0.5)  # Small delay between requests

print(f"\n✅ Successfully ingested {len(SAMPLE_DATA)} documents")

# Check graph stats
print("\n" + "=" * 80)
print("  Graph Statistics")
print("=" * 80)
print()

response = requests.get(f"{API_URL}/graph/stats")
if response.status_code == 200:
    stats = response.json()
    print(f"Total Memories: {stats['total_memories']}")
    print(f"Total Relationships: {stats['total_relationships']}")
    print(f"\nRelationship Breakdown:")
    for rel_type, count in stats['relationship_types'].items():
        if count > 0:
            print(f"  - {rel_type.upper()}: {count}")
    
    if stats['total_relationships'] == 0:
        print("  (No relationships detected yet)")
else:
    print(f"Error getting stats: {response.status_code}")

print("\n✨ Done! Check http://localhost:8000/docs to explore the API")

