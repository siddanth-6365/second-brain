'use client'

import { useState, useEffect, useCallback } from 'react'
import { Network, Loader2, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { exportGraph } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { formatRelativeTime, getRelationshipColor, truncateText } from '@/lib/utils'
import dynamic from 'next/dynamic'

// Dynamically import ForceGraph2D to avoid SSR issues
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false })

interface GraphNode {
  id: string
  name: string
  content: string
  created_at: string
  entities?: Record<string, string[]>
  color?: string
}

interface GraphLink {
  source: string
  target: string
  type: string
  confidence: number
  reason?: string
}

interface GraphData {
  nodes: GraphNode[]
  links: GraphLink[]
}

export default function GraphPage() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] })
  const [loading, setLoading] = useState(true)
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [relationshipFilter, setRelationshipFilter] = useState('all')
  const [dialogOpen, setDialogOpen] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    fetchGraphData()
  }, [])

  const fetchGraphData = async () => {
    setLoading(true)
    try {
      const data = await exportGraph()
      
      // Transform data for force graph
      const nodes: GraphNode[] = data.nodes?.map((node: any) => {
        // Use full_content from backend (or fallback to label or empty string)
        const content = node.full_content || node.content || node.label || ''
        const words = content.split(/\s+/).filter((w: string) => w.length > 3)
        const mainWord = words.length > 0 ? words[0] : 'Memory'
        
        return {
          id: node.id,
          name: mainWord,
          content: content, // Full content for dialog
          created_at: node.created_at || new Date().toISOString(),
          entities: node.entities || {},
          color: getNodeColor(node)
        }
      }) || []

      const links: GraphLink[] = data.edges?.map((edge: any) => ({
        source: edge.from || edge.source,
        target: edge.to || edge.target,
        type: edge.type || 'similar',
        confidence: edge.confidence || edge.weight || 0.5,
        reason: edge.reason || ''
      })) || []

      setGraphData({ nodes, links })
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load graph data',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const getNodeColor = (node: any): string => {
    // Color nodes based on age
    const createdAt = new Date(node.created_at || Date.now())
    const ageInDays = (Date.now() - createdAt.getTime()) / (1000 * 60 * 60 * 24)
    
    if (ageInDays < 7) return '#22c55e' // Green for recent
    if (ageInDays < 30) return '#3b82f6' // Blue for medium
    return '#6b7280' // Gray for old
  }

  const getLinkColor = (link: GraphLink): string => {
    return getRelationshipColor(link.type)
  }

  const filteredLinks = relationshipFilter === 'all' 
    ? graphData.links 
    : graphData.links.filter(link => link.type === relationshipFilter)

  const handleNodeClick = useCallback((node: any) => {
    setSelectedNode(node)
    setDialogOpen(true)
  }, [])

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <Network className="w-8 h-8 text-purple-400" />
          <h1 className="text-4xl font-bold text-white">Knowledge Graph</h1>
        </div>
        <p className="text-gray-400">
          Interactive visualization of your memory relationships and entity connections
        </p>
      </div>

      {/* Stats and Controls */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Stats */}
        <Card className="glass-card-hover bg-blue-500/10 border-blue-400/30">
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-white">{graphData.nodes.length}</div>
            <p className="text-xs text-blue-300/70">Memories</p>
          </CardContent>
        </Card>

        <Card className="glass-card-hover bg-purple-500/10 border-purple-400/30">
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-white">{graphData.links.length}</div>
            <p className="text-xs text-purple-300/70">Relationships</p>
          </CardContent>
        </Card>

        {/* Relationship Filter */}
        <Card className="glass-card md:col-span-2">
          <CardContent className="pt-4">
            <div className="space-y-2">
              <label className="text-xs text-gray-400">Filter by Relationship</label>
              <Select value={relationshipFilter} onValueChange={setRelationshipFilter}>
                <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-gray-700 border-gray-600">
                  <SelectItem value="all">All Types ({graphData.links.length})</SelectItem>
                  <SelectItem value="updates">UPDATES ({graphData.links.filter(l => l.type === 'updates').length})</SelectItem>
                  <SelectItem value="extends">EXTENDS ({graphData.links.filter(l => l.type === 'extends').length})</SelectItem>
                  <SelectItem value="derives">DERIVES ({graphData.links.filter(l => l.type === 'derives').length})</SelectItem>
                  <SelectItem value="similar">SIMILAR ({graphData.links.filter(l => l.type === 'similar').length})</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Legend */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-white text-sm">Legend</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Node Colors */}
            <div className="space-y-2">
              <p className="text-xs font-semibold text-gray-400 uppercase">Node Age</p>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  <span className="text-xs text-gray-300">Recent (&lt; 7 days)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                  <span className="text-xs text-gray-300">Medium (&lt; 30 days)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-gray-500"></div>
                  <span className="text-xs text-gray-300">Old (&gt; 30 days)</span>
                </div>
              </div>
            </div>

            {/* Relationship Types */}
            <div className="space-y-2">
              <p className="text-xs font-semibold text-gray-400 uppercase">Relationships</p>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-1" style={{ backgroundColor: getRelationshipColor('updates') }}></div>
                  <span className="text-xs text-gray-300">UPDATES</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-1" style={{ backgroundColor: getRelationshipColor('extends') }}></div>
                  <span className="text-xs text-gray-300">EXTENDS</span>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <p className="text-xs font-semibold text-gray-400 uppercase">&nbsp;</p>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-1" style={{ backgroundColor: getRelationshipColor('derives') }}></div>
                  <span className="text-xs text-gray-300">DERIVES (NER)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-1" style={{ backgroundColor: getRelationshipColor('similar') }}></div>
                  <span className="text-xs text-gray-300">SIMILAR</span>
                </div>
              </div>
            </div>

            {/* Controls */}
            <div className="space-y-2">
              <p className="text-xs font-semibold text-gray-400 uppercase">Controls</p>
              <div className="space-y-1 text-xs text-gray-300">
                <p>• Click node to view details</p>
                <p>• Drag to pan</p>
                <p>• Scroll to zoom</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Graph Visualization */}
      <Card className="glass-card">
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-[600px]">
              <Loader2 className="w-8 h-8 animate-spin text-purple-400" />
            </div>
          ) : graphData.nodes.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-[600px] space-y-4">
              <Network className="w-16 h-16 text-gray-600" />
              <p className="text-gray-400">No memories yet. Add some memories to see your knowledge graph!</p>
              <Button onClick={() => window.location.href = '/ingest'}>
                Add Memory
              </Button>
            </div>
          ) : (
            <div className="h-[600px] w-full bg-gray-900 rounded-lg overflow-hidden">
              <ForceGraph2D
                graphData={{ 
                  nodes: graphData.nodes, 
                  links: filteredLinks 
                }}
                nodeLabel="name"
                nodeColor={(node: any) => node.color}
                nodeRelSize={6}
                linkColor={(link: any) => getLinkColor(link as GraphLink)}
                linkWidth={(link: any) => (link as GraphLink).confidence * 3}
                linkDirectionalParticles={2}
                linkDirectionalParticleWidth={2}
                onNodeClick={handleNodeClick}
                backgroundColor="#111827"
                nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
                  const nodeRadius = 8
                  
                  // Draw outer glow
                  ctx.beginPath()
                  ctx.arc(node.x, node.y, nodeRadius + 2, 0, 2 * Math.PI, false)
                  ctx.fillStyle = node.color + '40'
                  ctx.fill()
                  
                  // Draw node circle
                  ctx.beginPath()
                  ctx.arc(node.x, node.y, nodeRadius, 0, 2 * Math.PI, false)
                  ctx.fillStyle = node.color
                  ctx.fill()
                  
                  // Draw border
                  ctx.strokeStyle = '#ffffff'
                  ctx.lineWidth = 1.5
                  ctx.stroke()
                }}
              />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Node Detail Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="glass-card border-white/20 text-white max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-2xl">Memory Details</DialogTitle>
            <DialogDescription className="text-white/60">
              {selectedNode && formatRelativeTime(selectedNode.created_at)}
            </DialogDescription>
          </DialogHeader>
          {selectedNode && (
            <div className="space-y-6">
              {/* Memory ID */}
              <div className="space-y-2">
                <p className="text-xs text-white/50">ID: {selectedNode.id}</p>
              </div>

              {/* Content */}
              <div className="space-y-2">
                <p className="text-sm font-semibold text-white/80">Content</p>
                <div className="bg-white/5 border border-white/10 rounded-lg p-4">
                  <p className="text-white/90 leading-relaxed">
                    {selectedNode.content || 'No content available'}
                  </p>
                </div>
              </div>

              {/* Entities */}
              {selectedNode.entities && Object.values(selectedNode.entities).flat().length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-white/80">Extracted Entities</p>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(selectedNode.entities).map(([type, entities]) =>
                      entities.map(entity => (
                        <Badge 
                          key={`${type}-${entity}`} 
                          className="bg-blue-500/30 text-blue-300 border-blue-400/50"
                        >
                          {entity}
                        </Badge>
                      ))
                    )}
                  </div>
                </div>
              )}

              {/* Related Memories */}
              {graphData.links.filter(link => 
                link.source === selectedNode.id || 
                link.target === selectedNode.id ||
                (typeof link.source === 'object' && (link.source as any).id === selectedNode.id) ||
                (typeof link.target === 'object' && (link.target as any).id === selectedNode.id)
              ).length > 0 && (
                <div className="space-y-3">
                  <p className="text-sm font-semibold text-white/80">Related Memories</p>
                  <div className="space-y-3">
                    {graphData.links
                      .filter(link => 
                        link.source === selectedNode.id || 
                        link.target === selectedNode.id ||
                        (typeof link.source === 'object' && (link.source as any).id === selectedNode.id) ||
                        (typeof link.target === 'object' && (link.target as any).id === selectedNode.id)
                      )
                      .map((link, idx) => {
                        // Handle both string and object references
                        const sourceId = typeof link.source === 'object' ? (link.source as any).id : link.source
                        const targetId = typeof link.target === 'object' ? (link.target as any).id : link.target
                        const relatedNodeId = sourceId === selectedNode.id ? targetId : sourceId
                        const relatedNode = graphData.nodes.find(n => n.id === relatedNodeId)
                        
                        return (
                          <div key={idx} className="bg-white/5 border border-white/10 rounded-lg p-3 space-y-2">
                            <div className="flex items-center gap-2">
                              <Badge 
                                className="flex-shrink-0"
                                style={{ 
                                  backgroundColor: getLinkColor(link) + '30',
                                  borderColor: getLinkColor(link),
                                  color: getLinkColor(link)
                                }}
                              >
                                {link.type.toUpperCase()}
                              </Badge>
                              <span className="text-xs text-white/50">
                                Confidence: {link.confidence.toFixed(2)}
                              </span>
                            </div>
                            {relatedNode && relatedNode.content && (
                              <p className="text-sm text-white/80">
                                {truncateText(relatedNode.content, 150)}
                              </p>
                            )}
                            {relatedNode && !relatedNode.content && (
                              <p className="text-sm text-white/50 italic">
                                No content available
                              </p>
                            )}
                          </div>
                        )
                      })}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2 pt-4 border-t border-white/10">
                <Button
                  variant="outline"
                  onClick={() => {
                    const searchQuery = selectedNode.content ? selectedNode.content.slice(0, 50) : selectedNode.id
                    window.location.href = `/search?q=${encodeURIComponent(searchQuery)}`
                  }}
                  className="border-white/20 text-white hover:bg-white/10"
                  disabled={!selectedNode.content && !selectedNode.id}
                >
                  Find Similar
                </Button>
                <Button
                  onClick={() => setDialogOpen(false)}
                  className="bg-blue-600 hover:bg-blue-700 ml-auto"
                >
                  Close
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
