"""Graph visualization utilities"""

import json
from typing import Optional


def visualize_graph(graph_data: dict, output_file: str = "graph_visualization.html"):
    """
    Create an interactive HTML visualization of the knowledge graph.
    
    Args:
        graph_data: Graph data from graph_store.export_graph()
        output_file: Output HTML file path
    """
    
    # HTML template with vis.js for graph visualization
    html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Second Brain - Knowledge Graph</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style type="text/css">
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: #f5f5f5;
        }}
        
        #header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        #header h1 {{
            margin: 0;
            font-size: 28px;
        }}
        
        #header p {{
            margin: 5px 0 0 0;
            opacity: 0.9;
        }}
        
        #stats {{
            background: white;
            margin: 20px;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        #stats h2 {{
            margin-top: 0;
            color: #333;
        }}
        
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        
        .stat-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }}
        
        .stat-card .label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .stat-card .value {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin-top: 5px;
        }}
        
        #mynetwork {{
            width: calc(100% - 40px);
            height: 600px;
            margin: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        #legend {{
            background: white;
            margin: 0 20px 20px 20px;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        #legend h3 {{
            margin-top: 0;
            color: #333;
        }}
        
        .legend-item {{
            display: inline-block;
            margin-right: 20px;
            margin-bottom: 10px;
        }}
        
        .legend-color {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border-radius: 3px;
            vertical-align: middle;
            margin-right: 5px;
        }}
        
        #info {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            max-width: 300px;
            display: none;
        }}
        
        #info.show {{
            display: block;
        }}
        
        #info h4 {{
            margin: 0 0 10px 0;
            color: #667eea;
        }}
        
        #info p {{
            margin: 5px 0;
            font-size: 14px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div id="header">
        <h1>🧠 Second Brain - Knowledge Graph</h1>
        <p>Interactive visualization of your intelligent memory system</p>
    </div>
    
    <div id="stats">
        <h2>Graph Statistics</h2>
        <div class="stat-grid">
            <div class="stat-card">
                <div class="label">Total Memories</div>
                <div class="value">{total_memories}</div>
            </div>
            <div class="stat-card">
                <div class="label">Total Relationships</div>
                <div class="value">{total_relationships}</div>
            </div>
            <div class="stat-card">
                <div class="label">Updates</div>
                <div class="value">{updates_count}</div>
            </div>
            <div class="stat-card">
                <div class="label">Extends</div>
                <div class="value">{extends_count}</div>
            </div>
            <div class="stat-card">
                <div class="label">Similar</div>
                <div class="value">{similar_count}</div>
            </div>
            <div class="stat-card">
                <div class="label">Derives</div>
                <div class="value">{derives_count}</div>
            </div>
        </div>
    </div>
    
    <div id="mynetwork"></div>
    
    <div id="legend">
        <h3>Legend</h3>
        <div class="legend-item">
            <span class="legend-color" style="background: #4CAF50;"></span>
            <span>Latest Memory</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #9E9E9E;"></span>
            <span>Outdated Memory</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #FF9800; width: 40px; height: 3px;"></span>
            <span>Updates</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #2196F3; width: 40px; height: 3px;"></span>
            <span>Extends</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #9C27B0; width: 40px; height: 3px;"></span>
            <span>Similar</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #E91E63; width: 40px; height: 3px;"></span>
            <span>Derives</span>
        </div>
    </div>
    
    <div id="info">
        <h4>Memory Details</h4>
        <div id="info-content"></div>
    </div>

    <script type="text/javascript">
        // Graph data
        var graphData = {graph_json};
        
        // Create nodes for vis.js
        var nodes = graphData.nodes.map(function(node) {{
            var color = node.is_latest ? '#4CAF50' : '#9E9E9E';
            return {{
                id: node.id,
                label: node.label.substring(0, 30) + '...',
                title: node.full_content,
                color: {{
                    background: color,
                    border: node.is_latest ? '#388E3C' : '#757575',
                    highlight: {{
                        background: '#667eea',
                        border: '#5568d3'
                    }}
                }},
                font: {{
                    color: 'white',
                    size: 14
                }},
                shape: 'box',
                margin: 10,
                data: node
            }};
        }});
        
        // Create edges for vis.js
        var edges = graphData.edges.map(function(edge) {{
            var colorMap = {{
                'updates': '#FF9800',
                'extends': '#2196F3',
                'similar': '#9C27B0',
                'derives': '#E91E63'
            }};
            
            var color = colorMap[edge.type] || '#999';
            
            return {{
                from: edge.source,
                to: edge.target,
                arrows: 'to',
                color: {{
                    color: color,
                    highlight: '#667eea'
                }},
                label: edge.type.toUpperCase(),
                font: {{
                    size: 10,
                    align: 'middle',
                    color: '#666'
                }},
                width: 2,
                smooth: {{
                    type: 'curvedCW',
                    roundness: 0.2
                }},
                data: edge
            }};
        }});
        
        // Create a network
        var container = document.getElementById('mynetwork');
        var data = {{
            nodes: new vis.DataSet(nodes),
            edges: new vis.DataSet(edges)
        }};
        
        var options = {{
            physics: {{
                enabled: true,
                barnesHut: {{
                    gravitationalConstant: -2000,
                    springConstant: 0.001,
                    springLength: 200
                }},
                stabilization: {{
                    iterations: 150
                }}
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 100
            }},
            layout: {{
                improvedLayout: true,
                hierarchical: false
            }}
        }};
        
        var network = new vis.Network(container, data, options);
        
        // Click event
        network.on("click", function(params) {{
            if (params.nodes.length > 0) {{
                var nodeId = params.nodes[0];
                var node = nodes.find(n => n.id === nodeId);
                
                if (node) {{
                    var infoDiv = document.getElementById('info');
                    var infoContent = document.getElementById('info-content');
                    
                    infoContent.innerHTML = 
                        '<p><strong>Content:</strong><br>' + node.data.full_content + '</p>' +
                        '<p><strong>Created:</strong> ' + node.data.created_at + '</p>' +
                        '<p><strong>Latest:</strong> ' + (node.data.is_latest ? 'Yes' : 'No') + '</p>';
                    
                    infoDiv.classList.add('show');
                }}
            }} else {{
                document.getElementById('info').classList.remove('show');
            }}
        }});
        
        console.log('Graph loaded with', nodes.length, 'nodes and', edges.length, 'edges');
    </script>
</body>
</html>
"""
    
    # Get stats
    stats = graph_data.get('stats', {})
    relationship_types = stats.get('relationship_types', {})
    
    # Fill in template
    html_content = html_template.format(
        graph_json=json.dumps(graph_data),
        total_memories=stats.get('total_memories', 0),
        total_relationships=stats.get('total_relationships', 0),
        updates_count=relationship_types.get('updates', 0),
        extends_count=relationship_types.get('extends', 0),
        similar_count=relationship_types.get('similar', 0),
        derives_count=relationship_types.get('derives', 0)
    )
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Graph visualization saved to: {output_file}")
    print(f"   Open it in your browser to explore the knowledge graph!")


def create_visualization_from_graph_store():
    """Create visualization directly from graph store"""
    from backend.services.graph_store import get_graph_store
    
    graph_store = get_graph_store()
    graph_data = graph_store.export_graph()
    visualize_graph(graph_data)

