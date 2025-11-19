'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { Loader2, Maximize2, ZoomIn, ZoomOut, RefreshCw } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { exportGraph } from '@/lib/api'
import { truncateText, getRelationshipColor } from '@/lib/utils'
import dynamic from 'next/dynamic'
import { useToast } from '@/hooks/use-toast'

// Dynamically import ForceGraph2D to avoid SSR issues
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false })

interface GraphNode {
    id: string
    name: string
    content: string
    created_at: string
    entities?: Record<string, string[]>
    color?: string
    val?: number
    x?: number
    y?: number
}

interface GraphLink {
    source: string | GraphNode
    target: string | GraphNode
    type: string
    confidence: number
}

interface GraphData {
    nodes: GraphNode[]
    links: GraphLink[]
}

interface MemoryGraphProps {
    height?: number
    onNodeClick?: (node: GraphNode) => void
    className?: string
}

export function MemoryGraph({ height = 600, onNodeClick, className }: MemoryGraphProps) {
    const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] })
    const [loading, setLoading] = useState(true)
    const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null)
    const fgRef = useRef<any>()
    const { toast } = useToast()

    const fetchGraphData = useCallback(async () => {
        setLoading(true)
        try {
            const data = await exportGraph()

            const nodes: GraphNode[] = data.nodes?.map((node: any) => ({
                id: node.id,
                name: truncateText(node.label || node.content || 'Memory', 40),
                content: node.full_content || node.content || '',
                created_at: node.created_at,
                entities: node.entities,
                color: '#3b82f6', // Default blue
                val: 5
            })) || []

            const links: GraphLink[] = data.edges?.map((edge: any) => ({
                source: edge.from || edge.source,
                target: edge.to || edge.target,
                type: edge.type || 'similar',
                confidence: edge.confidence || 0.5
            })) || []

            setGraphData({ nodes, links })
        } catch (error) {
            console.error("Failed to fetch graph:", error)
            toast({
                title: "Error loading graph",
                description: "Could not load memory graph data.",
                variant: "destructive"
            })
        } finally {
            setLoading(false)
        }
    }, [toast])

    useEffect(() => {
        fetchGraphData()
    }, [fetchGraphData])

    const handleNodeClick = useCallback((node: GraphNode) => {
        // Center view on node
        if (fgRef.current) {
            fgRef.current.centerAt(node.x, node.y, 1000)
            fgRef.current.zoom(2, 1000)
        }

        if (onNodeClick) {
            onNodeClick(node)
        }
    }, [onNodeClick])

    return (
        <Card className={`glass-card overflow-hidden relative ${className}`}>
            {loading ? (
                <div className="flex items-center justify-center" style={{ height }}>
                    <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
                </div>
            ) : graphData.nodes.length === 0 ? (
                <div className="flex flex-col items-center justify-center text-gray-400 space-y-4" style={{ height }}>
                    <p>No memories found.</p>
                    <Button variant="outline" onClick={fetchGraphData}>
                        <RefreshCw className="w-4 h-4 mr-2" /> Refresh
                    </Button>
                </div>
            ) : (
                <div className="relative">
                    <div className="absolute top-4 right-4 z-10 flex gap-2">
                        <Button size="icon" variant="secondary" className="bg-black/50 hover:bg-black/70" onClick={() => fgRef.current?.zoomToFit(400)}>
                            <Maximize2 className="w-4 h-4" />
                        </Button>
                        <Button size="icon" variant="secondary" className="bg-black/50 hover:bg-black/70" onClick={fetchGraphData}>
                            <RefreshCw className="w-4 h-4" />
                        </Button>
                    </div>

                    <ForceGraph2D
                        ref={fgRef}
                        width={undefined} // Auto-width
                        height={height}
                        graphData={graphData}
                        nodeLabel="name"
                        nodeColor={node => (node as GraphNode).id === hoveredNode?.id ? '#fbbf24' : ((node as GraphNode).color || '#3b82f6')}
                        nodeRelSize={6}
                        linkColor={link => getRelationshipColor((link as GraphLink).type)}
                        linkWidth={link => (link as GraphLink).confidence * 2}
                        linkDirectionalParticles={2}
                        linkDirectionalParticleWidth={2}
                        onNodeClick={handleNodeClick as any}
                        onNodeHover={(node: any) => setHoveredNode(node || null)}
                        backgroundColor="#020617" // Dark background matching theme
                        nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
                            const isHovered = hoveredNode?.id === node.id
                            const label = node.name
                            const fontSize = 12 / globalScale

                            // Glow effect
                            if (isHovered) {
                                ctx.shadowBlur = 15
                                ctx.shadowColor = '#fbbf24'
                            } else {
                                ctx.shadowBlur = 0
                            }

                            // Draw node
                            ctx.beginPath()
                            ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI, false)
                            ctx.fillStyle = isHovered ? '#fbbf24' : '#3b82f6'
                            ctx.fill()

                            // Reset shadow
                            ctx.shadowBlur = 0

                            // Draw label
                            if (globalScale >= 1.5 || isHovered) {
                                ctx.font = `${fontSize}px Sans-Serif`
                                ctx.textAlign = 'center'
                                ctx.textBaseline = 'middle'
                                ctx.fillStyle = 'rgba(255, 255, 255, 0.8)'
                                ctx.fillText(label, node.x, node.y + 8)
                            }
                        }}
                        nodePointerAreaPaint={(node: any, color: string, ctx: CanvasRenderingContext2D) => {
                            ctx.fillStyle = color
                            ctx.beginPath()
                            ctx.arc(node.x, node.y, 8, 0, 2 * Math.PI, false) // Slightly larger radius for easier clicking
                            ctx.fill()
                        }}
                    />
                </div>
            )}
        </Card>
    )
}
