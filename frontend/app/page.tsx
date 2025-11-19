'use client'

import { useState } from 'react'
import { MemoryGraph } from '@/components/memory-graph'
import { MemoryDetailDialog } from '@/components/memory-detail-dialog'
import { Button } from '@/components/ui/button'
import { Plus, Network, MessageSquare, Search } from 'lucide-react'
import { ProtectedRoute } from '@/components/protected-route'
import Link from 'next/link'

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<'graph' | 'chat'>('graph')
  const [selectedNode, setSelectedNode] = useState<any>(null)
  const [detailsOpen, setDetailsOpen] = useState(false)

  const handleNodeClick = (node: any) => {
    setSelectedNode(node)
    setDetailsOpen(true)
  }

  return (
    <ProtectedRoute>
      <div className="space-y-8 pb-10">
        {/* Hero Section */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div className="space-y-1">
            <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400 text-glow">
              Second Brain
            </h1>
            <p className="text-gray-400">Your personal memory expanded by AI</p>
          </div>
          <div className="flex gap-3">
            <Link href="/ingest">
              <Button className="bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-500/20">
                <Plus className="w-4 h-4 mr-2" /> Add Memory
              </Button>
            </Link>
            <Link href="/chat">
              <Button variant="secondary" className="bg-purple-500/10 text-purple-300 hover:bg-purple-500/20 border border-purple-500/20">
                <MessageSquare className="w-4 h-4 mr-2" /> Chat
              </Button>
            </Link>
            <Link href="/search">
              <Button variant="outline" className="border-white/10 hover:bg-white/5 text-white">
                <Search className="w-4 h-4 mr-2" /> Search
              </Button>
            </Link>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 gap-6">

          {/* Full Width: Graph */}
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                <Network className="w-5 h-5 text-blue-400" /> Knowledge Graph
              </h2>
              <Link href="/graph" className="text-sm text-blue-400 hover:text-blue-300">
                View Full Screen &rarr;
              </Link>
            </div>
            <MemoryGraph height={600} className="w-full" onNodeClick={handleNodeClick} />
          </div>
        </div>

        <MemoryDetailDialog
          node={selectedNode}
          open={detailsOpen}
          onOpenChange={setDetailsOpen}
        />
      </div>
    </ProtectedRoute>
  )
}
