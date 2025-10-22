"""Test script to demonstrate the Second Brain system"""

import asyncio
import json
from backend.services import (
    get_ingestion_service,
    get_search_service,
    get_graph_store
)
from backend.models import SearchQuery


# Sample data mirroring real-world knowledge management (like Supermemory)
SAMPLE_DATA = [
    # UPDATES: Role/job changes
    {
        "title": "Current Role",
        "content": "I work as a Software Engineer at TechCorp, focusing on backend development with Python and FastAPI.",
        "source": "career_notes.txt"
    },
    {
        "title": "Role Update",
        "content": "I now work as a Senior Engineering Manager at TechCorp, leading a team of 8 engineers across backend and frontend.",
        "source": "career_update.txt"
    },
    
    # EXTENDS: Work responsibilities with additional detail
    {
        "title": "Work Projects",
        "content": "I'm currently working on building a scalable API platform for our microservices architecture.",
        "source": "work_log.txt"
    },
    {
        "title": "Project Details",
        "content": "The API platform uses FastAPI with PostgreSQL database, Redis for caching, and Docker for containerization. We're aiming for 99.9% uptime.",
        "source": "technical_specs.txt"
    },
    
    # UPDATES: Learning progress
    {
        "title": "Learning AI",
        "content": "I'm learning about AI and machine learning fundamentals through online courses. Just started with basic neural networks.",
        "source": "learning_journal.txt"
    },
    {
        "title": "AI Progress Update",
        "content": "I've now completed 3 AI courses and built my first machine learning model using TensorFlow. Currently working on a computer vision project.",
        "source": "learning_progress.txt"
    },
    
    # EXTENDS: Hobbies with additional context
    {
        "title": "Hobbies",
        "content": "I enjoy photography, especially landscape and street photography. I shoot with a Canon EOS R5.",
        "source": "personal_interests.txt"
    },
    {
        "title": "Photography Techniques",
        "content": "For landscape photography, I focus on golden hour lighting and use a tripod for long exposures. I also shoot in RAW for better post-processing control.",
        "source": "photography_tips.txt"
    },
    
    # DERIVES: Health and fitness connections
    {
        "title": "Fitness Goals",
        "content": "My fitness goal is to run a marathon by the end of the year. Currently running 20 miles per week.",
        "source": "fitness_goals.txt"
    },
    {
        "title": "Diet Plan",
        "content": "I follow a high-protein, balanced diet with lots of vegetables. I eat 5 small meals a day to maintain energy for training.",
        "source": "nutrition_plan.txt"
    },
    {
        "title": "Sleep Schedule",
        "content": "I maintain a strict sleep schedule of 8 hours per night, going to bed at 10 PM and waking at 6 AM for my morning run.",
        "source": "daily_routine.txt"
    },
    
    # SIMILAR: Related reading interests
    {
        "title": "Reading List - Tech",
        "content": "Currently reading 'Designing Data-Intensive Applications' by Martin Kleppmann. Great insights on distributed systems and databases.",
        "source": "reading_tech.txt"
    },
    {
        "title": "Reading List - Business",
        "content": "Also reading 'The Lean Startup' by Eric Ries to better understand product development and startup methodologies.",
        "source": "reading_business.txt"
    },
    
    # DERIVES: Travel and culture connections
    {
        "title": "Travel Plans",
        "content": "Planning a 2-week trip to Japan in spring to see cherry blossoms in Tokyo and Kyoto.",
        "source": "travel_japan.txt"
    },
    {
        "title": "Japanese Language",
        "content": "Started learning Japanese basics on Duolingo. Can introduce myself and order food in Japanese now.",
        "source": "language_learning.txt"
    },
    {
        "title": "Japanese Culture",
        "content": "Fascinated by Japanese tea ceremonies and traditional architecture. Planning to visit temples and attend a tea ceremony during my trip.",
        "source": "cultural_interests.txt"
    }
]


def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def print_section(text: str):
    """Print a formatted section"""
    print("\n" + "-" * 80)
    print(f"  {text}")
    print("-" * 80 + "\n")


async def main():
    """Run the test demonstration"""
    
    print_header("Second Brain - System Demonstration")
    print("This demo shows how documents are transformed into an intelligent knowledge graph")
    print("with automatic relationship detection (Updates, Extends, Derives).\n")
    
    # Get services
    ingestion_service = get_ingestion_service()
    search_service = get_search_service()
    graph_store = get_graph_store()
    
    # Step 1: Ingest documents
    print_section("STEP 1: INGESTING DOCUMENTS")
    print("Processing documents into memories with embeddings...\n")
    
    documents = []
    for idx, data in enumerate(SAMPLE_DATA):
        print(f"[{idx + 1}/{len(SAMPLE_DATA)}] Ingesting: {data['title']}")
        doc = await ingestion_service.ingest_text(
            text=data["content"],
            title=data["title"],
            source=data["source"]
        )
        documents.append(doc)
        print(f"    ✓ Created {len(doc.memory_ids)} memory/memories")
    
    print(f"\n✅ Successfully ingested {len(documents)} documents")
    
    # Step 2: Show graph statistics
    print_section("STEP 2: KNOWLEDGE GRAPH STATISTICS")
    stats = graph_store.get_graph_stats()
    print(f"Total Memories: {stats['total_memories']}")
    print(f"Total Relationships: {stats['total_relationships']}")
    print(f"\nRelationship Breakdown:")
    for rel_type, count in stats['relationship_types'].items():
        if count > 0:
            print(f"  - {rel_type.upper()}: {count}")
    
    # Step 3: Demonstrate relationship detection
    print_section("STEP 3: RELATIONSHIP DETECTION")
    
    # Find memories about career/role evolution
    all_memories = graph_store.get_all_memories()
    role_memories = [m for m in all_memories if "work" in m.content.lower() or "role" in m.content.lower() or "engineer" in m.content.lower()]
    
    if len(role_memories) >= 2:
        print("Found memories about career/role (showing evolution):")
        for memory in role_memories[:2]:
            print(f"\n  Memory ID: {memory.id}")
            print(f"  Content: {memory.content[:80]}...")
            print(f"  Is Latest: {memory.is_latest}")
            print(f"  Created: {memory.created_at}")
            
            # Show relationships
            if memory.relationships:
                print(f"  Relationships:")
                for rel in memory.relationships:
                    print(f"    → {rel.relationship_type.value.upper()} (confidence: {rel.confidence:.2f})")
                    print(f"      Reason: {rel.reason}")
    
    # Step 4: Semantic search demonstration
    print_section("STEP 4: SEMANTIC SEARCH DEMONSTRATION")
    
    search_queries = [
        "What is my current role?",
        "What am I learning about AI?",
        "What are my hobbies?",
        "What are my fitness goals?"
    ]
    
    for query_text in search_queries:
        print(f"\nQuery: '{query_text}'")
        print("-" * 60)
        
        query = SearchQuery(query=query_text, limit=3, only_latest=True)
        results = await search_service.search(query)
        
        for i, result in enumerate(results, 1):
            print(f"\n  Result {i} (score: {result.score:.3f}):")
            print(f"  Content: {result.memory.content}")
            print(f"  Source: {result.memory.metadata.get('source', 'unknown')}")
            print(f"  Explanation: {result.explanation}")
            if result.related_memories:
                print(f"  Related memories: {len(result.related_memories)}")
    
    # Step 5: Show how information evolved
    print_section("STEP 5: INFORMATION EVOLUTION")
    
    timeline = await search_service.get_memory_timeline("career role")
    if timeline:
        print("Timeline of how career information evolved:")
        for i, memory in enumerate(timeline, 1):
            print(f"\n  {i}. [{memory.created_at.strftime('%Y-%m-%d %H:%M:%S')}]")
            print(f"     {memory.content[:100]}...")
            print(f"     Latest: {memory.is_latest} | Active: {memory.is_active}")
    
    # Step 6: Export graph
    print_section("STEP 6: KNOWLEDGE GRAPH EXPORT")
    
    graph_data = graph_store.export_graph()
    
    print(f"Graph contains:")
    print(f"  - {len(graph_data['nodes'])} nodes (memories)")
    print(f"  - {len(graph_data['edges'])} edges (relationships)")
    
    # Save to file
    output_file = "knowledge_graph.json"
    with open(output_file, 'w') as f:
        json.dump(graph_data, f, indent=2)
    print(f"\n✅ Full graph exported to: {output_file}")
    
    # Show sample edges
    if graph_data['edges']:
        print("\nSample Relationships:")
        for edge in graph_data['edges'][:5]:
            source_node = next((n for n in graph_data['nodes'] if n['id'] == edge['source']), None)
            target_node = next((n for n in graph_data['nodes'] if n['id'] == edge['target']), None)
            
            if source_node and target_node:
                print(f"\n  '{source_node['label'][:50]}...'")
                print(f"    --[{edge['type'].upper()}]--> ")
                print(f"  '{target_node['label'][:50]}...'")
                print(f"    Confidence: {edge['confidence']:.2f}")
                if edge.get('reason'):
                    print(f"    Reason: {edge['reason']}")
    
    # Summary
    print_section("SUMMARY")
    print("✅ System successfully demonstrated:")
    print("  1. ✓ Document ingestion and chunking")
    print("  2. ✓ Embedding generation")
    print("  3. ✓ Automatic relationship detection (UPDATES, EXTENDS, SIMILAR)")
    print("  4. ✓ Semantic search with relevance ranking")
    print("  5. ✓ Information evolution tracking (is_latest)")
    print("  6. ✓ Knowledge graph with connected memories")
    print("\n🧠 Your Second Brain is ready!")
    print("\nNext steps:")
    print("  - Start the API server: uvicorn backend.main:app --reload")
    print("  - Access API docs: http://localhost:8000/docs")
    print("  - View graph visualization: http://localhost:8000/graph/export")


if __name__ == "__main__":
    asyncio.run(main())


