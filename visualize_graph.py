"""Script to generate graph visualization"""

import json
from backend.utils.visualizer import visualize_graph

# Load the graph data
try:
    with open('knowledge_graph.json', 'r') as f:
        graph_data = json.load(f)
    
    # Create visualization
    visualize_graph(graph_data, 'graph_visualization.html')
    
    print("\n🎨 Visualization created!")
    print("   Open 'graph_visualization.html' in your browser")
    
except FileNotFoundError:
    print("❌ Error: knowledge_graph.json not found")
    print("   Please run 'python backend/test_system.py' first to generate the graph")
except Exception as e:
    print(f"❌ Error: {e}")

