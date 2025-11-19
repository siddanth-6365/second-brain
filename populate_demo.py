import asyncio
import httpx
import sys

BASE_URL = "http://localhost:8000"

DEMO_DATA = [
    # Cluster 1: Coffee (Interconnected by "coffee", "espresso", "milk")
    {
        "title": "Espresso",
        "content": "Espresso is a concentrated coffee beverage brewed by forcing hot water under high pressure through finely-ground coffee beans. It is the base for many other coffee drinks.",
        "type": "note"
    },
    {
        "title": "Latte",
        "content": "A latte is a coffee drink made with espresso and steamed milk. The term comes from the Italian caffellatte, which means 'coffee and milk'.",
        "type": "note"
    },
    {
        "title": "Cappuccino",
        "content": "Cappuccino is an espresso-based coffee drink that originated in Italy. It is traditionally prepared with steamed milk foam (microfoam).",
        "type": "note"
    },
    
    # Cluster 2: Programming (Interconnected by "programming", "language", "code")
    {
        "title": "Python",
        "content": "Python is a high-level, general-purpose programming language. Its design philosophy emphasizes code readability with the use of significant indentation.",
        "type": "note"
    },
    {
        "title": "Rust",
        "content": "Rust is a multi-paradigm, general-purpose programming language. Rust emphasizes performance, type safety, and concurrency.",
        "type": "note"
    },
    {
        "title": "TypeScript",
        "content": "TypeScript is a free and open-source high-level programming language developed by Microsoft that adds static typing with optional type annotations to JavaScript.",
        "type": "note"
    },

    # Cluster 3: Tech Products (Interconnected with Programming and each other)
    {
        "title": "MacBook Pro",
        "content": "The MacBook Pro is a line of Mac laptops made by Apple Inc. It is popular among software developers for writing Python, Rust, and TypeScript code.",
        "type": "note"
    },
    {
        "title": "VS Code",
        "content": "Visual Studio Code, also commonly referred to as VS Code, is a source-code editor made by Microsoft. It supports Python, Rust, and TypeScript via extensions.",
        "type": "note"
    }
]

async def ingest_note(client, note):
    print(f"Ingesting {note['title']}...")
    payload = {
        "type": "note",
        "title": note["title"],
        "content": note["content"]
    }
    headers = {"Authorization": "Bearer test-token"}
    try:
        response = await client.post(f"{BASE_URL}/documents/ingest", json=payload, headers=headers, timeout=30.0)
        if response.status_code != 200:
            print(f"Failed to ingest {note['title']}: {response.text}")
            return
        data = response.json()
        print(f"Successfully ingested {note['title']}")
    except Exception as e:
        print(f"Error ingesting {note['title']}: {e}")

async def main():
    print("Populating database with demo data...")
    async with httpx.AsyncClient() as client:
        for item in DEMO_DATA:
            await ingest_note(client, item)
            # Small delay to ensure order/processing
            await asyncio.sleep(0.5)
    
    print("\nDone! You can now check the graph visualization.")

if __name__ == "__main__":
    asyncio.run(main())
