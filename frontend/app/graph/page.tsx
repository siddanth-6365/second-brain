'use client'

import { useState } from 'react'
import { MemoryGraph } from '@/components/memory-graph'
import { MemoryDetailDialog } from '@/components/memory-detail-dialog'
import { ProtectedRoute } from '@/components/protected-route'
import { Button } from '@/components/ui/button'
import { ArrowLeft } from 'lucide-react'
import Link from 'next/link'

export default function GraphPage() {
  const [selectedNode, setSelectedNode] = useState<any>(null)
  const [detailsOpen, setDetailsOpen] = useState(false)

  const handleNodeClick = (node: any) => {
    setSelectedNode(node)
    setDetailsOpen(true)
  }

  return (
    <ProtectedRoute>
      <div className="h-[calc(100vh-4rem)] flex flex-col gap-4">
        <div className="flex items-center gap-4">
          <Link href="/">
            <Button variant="ghost" size="icon" className="text-white hover:bg-white/10">
              <ArrowLeft className="w-5 h-5" />
            </Button>
          </Link>
          <h1 className="text-2xl font-bold text-white">Full Knowledge Graph</h1>
        </div>
        <div className="flex-1 min-h-0">
          <MemoryGraph height={800} className="h-full" onNodeClick={handleNodeClick} />
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
