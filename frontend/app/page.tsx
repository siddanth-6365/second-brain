'use client'

import { useState, useEffect } from 'react'
import { Brain, Search, MessageSquare, Network, ArrowRight, Eye } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useRouter } from 'next/navigation'
import { getGraphStats, exportGraph } from '@/lib/api'
import dynamic from 'next/dynamic'

// Dynamically import ForceGraph2D to avoid SSR issues
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false })

export default function Home() {
  const router = useRouter()
  const [stats, setStats] = useState<any>(null)
  const [chatQuery, setChatQuery] = useState('')
  const [graphData, setGraphData] = useState<any>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const statsData = await getGraphStats()
        setStats(statsData)
        
        const graphExport = await exportGraph()
        if (graphExport.nodes && graphExport.nodes.length > 0) {
          setGraphData({
            nodes: graphExport.nodes.slice(0, 10), // Show first 10 nodes
            edges: graphExport.edges.filter((e: any) => {
              const sourceInNodes = graphExport.nodes.slice(0, 10).some((n: any) => n.id === e.source)
              const targetInNodes = graphExport.nodes.slice(0, 10).some((n: any) => n.id === e.target)
              return sourceInNodes && targetInNodes
            })
          })
        }
      } catch (error) {
        console.error('Failed to fetch data:', error)
      }
    }
    fetchData()
  }, [])

  const handleChatSearch = () => {
    if (chatQuery.trim()) {
      router.push(`/chat?q=${encodeURIComponent(chatQuery)}`)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleChatSearch()
    }
  }

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <div className="text-center space-y-6 py-12">
        <div className="flex justify-center">
          <div className="relative">
            <div className="absolute inset-0 bg-blue-500 blur-3xl opacity-20 rounded-full"></div>
            <Brain className="w-24 h-24 text-blue-400 relative z-10" />
          </div>
        </div>
        <h1 className="text-6xl font-bold text-white">
          Second Brain
        </h1>
        <p className="text-xl text-gray-300 max-w-2xl mx-auto">
          Transform messy inputs into intelligent, connected memories with advanced NER-based relationship detection and hot/cold memory tiering
        </p>
        <div className="flex gap-4 justify-center">
          <Button onClick={() => router.push('/ingest')} size="lg" className="bg-blue-600 hover:bg-blue-700">
            <Brain className="mr-2 h-5 w-5" />
            Add Memory
          </Button>
          <Button onClick={() => router.push('/search')} size="lg" variant="outline">
            <Search className="mr-2 h-5 w-5" />
            Search
          </Button>
        </div>
      </div>

      {/* Big Chat Search Bar */}
      <div className="py-12 px-4">
        <div className="max-w-3xl mx-auto space-y-6">
          <div className="text-center space-y-4">
            <h2 className="text-3xl font-bold text-white">
              Chat with Your Memories
            </h2>
            <p className="text-lg text-white/70">
              Ask anything about your knowledge base. Powered by RAG and Groq LLM.
            </p>
          </div>

          {/* Search Bar */}
          <div className="glass-card-hover p-2 flex items-center gap-2">
            <div className="flex-1 flex items-center gap-3 px-4">
              <MessageSquare className="w-6 h-6 text-blue-400 flex-shrink-0" />
              <Input
                type="text"
                placeholder="Ask me anything about your memories..."
                value={chatQuery}
                onChange={(e) => setChatQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                className="bg-transparent border-0 text-white placeholder-white/50 focus:outline-none focus:ring-0 text-lg"
              />
            </div>
            <Button
              onClick={handleChatSearch}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg flex items-center gap-2 flex-shrink-0"
            >
              <Search className="w-5 h-5" />
              <span className="hidden sm:inline">Ask</span>
            </Button>
          </div>

          {/* Quick Actions Below */}
          <div className="grid md:grid-cols-2 gap-4 pt-8">
            <Card className="glass-card-hover cursor-pointer group"
                  onClick={() => router.push('/graph')}>
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2 group-hover:text-blue-400 transition-colors">
                  <Network className="w-5 h-5" />
                  Explore Graph
                </CardTitle>
                <CardDescription>Visualize your knowledge network</CardDescription>
              </CardHeader>
            </Card>

            <Card className="glass-card-hover cursor-pointer group"
                  onClick={() => router.push('/search')}>
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2 group-hover:text-green-400 transition-colors">
                  <Search className="w-5 h-5" />
                  Search Memories
                </CardTitle>
                <CardDescription>Find specific information</CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </div>

      {/* Mini Graph Visualization */}
      {graphData && graphData.nodes.length > 0 && (
        <div className="space-y-4">
          <div className="text-center space-y-2">
            <h2 className="text-3xl font-bold text-white">Your Knowledge Network</h2>
            <p className="text-white/70">Visual representation of your memory connections</p>
          </div>
          <Card className="glass-card overflow-hidden">
            <CardContent className="p-0">
              <div className="h-[500px] w-full bg-gray-900 rounded-lg overflow-hidden">
                <ForceGraph2D
                  graphData={{
                    nodes: graphData.nodes.map((n: any) => ({
                      id: n.id,
                      name: n.label || n.full_content?.substring(0, 30) || 'Memory',
                      color: '#06b6d4'
                    })),
                    links: graphData.edges.map((e: any) => ({
                      source: e.source,
                      target: e.target,
                      type: e.type
                    }))
                  }}
                  nodeLabel="name"
                  nodeColor={(node: any) => node.color}
                  nodeRelSize={6}
                  linkColor={() => '#4f46e5'}
                  linkWidth={1.5}
                  backgroundColor="#111827"
                  nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
                    const nodeRadius = 6
                    
                    // Draw outer glow
                    ctx.beginPath()
                    ctx.arc(node.x, node.y, nodeRadius + 2, 0, 2 * Math.PI, false)
                    ctx.fillStyle = '#06b6d4' + '40'
                    ctx.fill()
                    
                    // Draw node circle
                    ctx.beginPath()
                    ctx.arc(node.x, node.y, nodeRadius, 0, 2 * Math.PI, false)
                    ctx.fillStyle = '#06b6d4'
                    ctx.fill()
                    
                    // Draw border
                    ctx.strokeStyle = '#ffffff'
                    ctx.lineWidth = 1
                    ctx.stroke()
                  }}
                />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Stats Section - Now Below Chat and Graph */}
      {stats && (
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Eye className="w-5 h-5" />
              Knowledge Graph Stats
            </CardTitle>
            <CardDescription>Your intelligent memory system at a glance</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-400">{stats.total_memories || 0}</div>
                <div className="text-sm text-white/60">Total Memories</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-400">{stats.total_relationships || 0}</div>
                <div className="text-sm text-white/60">Relationships</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-400">
                  {stats.relationship_types?.derives || 0}
                </div>
                <div className="text-sm text-white/60">DERIVES (NER)</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-yellow-400">
                  {stats.relationship_types?.updates || 0}
                </div>
                <div className="text-sm text-white/60">UPDATES</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
