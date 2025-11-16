'use client'

import { useState, useEffect } from 'react'
import { BarChart3, TrendingUp, Database, Zap } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { getGraphStats } from '@/lib/api'
import { getRelationshipColor } from '@/lib/utils'
import { ProtectedRoute } from '@/components/protected-route'

interface GraphStats {
  total_memories: number
  total_relationships: number
  relationship_types: {
    updates: number
    extends: number
    derives: number
    similar: number
  }
}

export default function DashboardPage() {
  const [stats, setStats] = useState<GraphStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getGraphStats()
        setStats(data)
      } catch (error) {
        console.error('Failed to fetch stats:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
    const interval = setInterval(fetchStats, 5000) // Refresh every 5 seconds
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-gray-400">Loading dashboard...</p>
      </div>
    )
  }

  if (!stats && loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-gray-400">Loading dashboard...</p>
      </div>
    )
  }

  // Show dashboard even if stats is empty (0 values)
  const displayStats = stats || {
    total_memories: 0,
    total_relationships: 0,
    relationship_types: {
      updates: 0,
      extends: 0,
      derives: 0,
      similar: 0
    }
  }

  const totalRelationships = displayStats.total_relationships
  const relationshipTypes = displayStats.relationship_types

  // Calculate percentages
  const derivesPercent = totalRelationships > 0 ? (relationshipTypes.derives / totalRelationships) * 100 : 0
  const updatesPercent = totalRelationships > 0 ? (relationshipTypes.updates / totalRelationships) * 100 : 0
  const extendsPercent = totalRelationships > 0 ? (relationshipTypes.extends / totalRelationships) * 100 : 0
  const similarPercent = totalRelationships > 0 ? (relationshipTypes.similar / totalRelationships) * 100 : 0

  return (
    <ProtectedRoute>
      <div className="space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <BarChart3 className="w-8 h-8 text-cyan-400" />
          <h1 className="text-4xl font-bold text-white">Analytics Dashboard</h1>
        </div>
        <p className="text-gray-400">
          Monitor your knowledge graph and memory tiering performance
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Memories */}
        <Card className="glass-card-hover bg-blue-500/10 border-blue-400/30">
          <CardHeader className="pb-3">
            <CardTitle className="text-blue-300 text-sm font-medium">Total Memories</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-white">{displayStats.total_memories}</div>
            <p className="text-xs text-blue-300/70 mt-1">Knowledge base size</p>
          </CardContent>
        </Card>

        {/* Total Relationships */}
        <Card className="glass-card-hover bg-purple-500/10 border-purple-400/30">
          <CardHeader className="pb-3">
            <CardTitle className="text-purple-300 text-sm font-medium">Relationships</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-white">{displayStats.total_relationships}</div>
            <p className="text-xs text-purple-300/70 mt-1">Connected memories</p>
          </CardContent>
        </Card>

        {/* DERIVES (NER) */}
        <Card className="glass-card-hover bg-green-500/10 border-green-400/30">
          <CardHeader className="pb-3">
            <CardTitle className="text-green-300 text-sm font-medium">DERIVES (NER)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-white">{relationshipTypes.derives}</div>
            <p className="text-xs text-green-300/70 mt-1">Entity-based relationships</p>
          </CardContent>
        </Card>

        {/* Avg Connections */}
        <Card className="glass-card-hover bg-yellow-500/10 border-yellow-400/30">
          <CardHeader className="pb-3">
            <CardTitle className="text-yellow-300 text-sm font-medium">Avg Connections</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-white">
              {displayStats.total_memories > 0 ? (displayStats.total_relationships / displayStats.total_memories).toFixed(1) : '0'}
            </div>
            <p className="text-xs text-yellow-300/70 mt-1">Per memory</p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analytics */}
      <Tabs defaultValue="relationships" className="space-y-4">
        <TabsList className="bg-gray-800 border-gray-700">
          <TabsTrigger value="relationships" className="data-[state=active]:bg-blue-600">
            Relationships
          </TabsTrigger>
          <TabsTrigger value="types" className="data-[state=active]:bg-blue-600">
            Type Distribution
          </TabsTrigger>
          <TabsTrigger value="performance" className="data-[state=active]:bg-blue-600">
            Performance
          </TabsTrigger>
        </TabsList>

        {/* Relationships Tab */}
        <TabsContent value="relationships">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white">Relationship Breakdown</CardTitle>
              <CardDescription>Distribution of relationship types in your knowledge graph</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* UPDATES */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: getRelationshipColor('updates') }}
                    />
                    <span className="text-white font-medium">UPDATES</span>
                  </div>
                  <span className="text-blue-400 font-semibold">{relationshipTypes.updates}</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all"
                    style={{ width: `${updatesPercent}%` }}
                  />
                </div>
                <p className="text-xs text-gray-400">{updatesPercent.toFixed(1)}% of relationships</p>
              </div>

              {/* EXTENDS */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: getRelationshipColor('extends') }}
                    />
                    <span className="text-white font-medium">EXTENDS</span>
                  </div>
                  <span className="text-purple-400 font-semibold">{relationshipTypes.extends}</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-purple-500 h-2 rounded-full transition-all"
                    style={{ width: `${extendsPercent}%` }}
                  />
                </div>
                <p className="text-xs text-gray-400">{extendsPercent.toFixed(1)}% of relationships</p>
              </div>

              {/* DERIVES */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: getRelationshipColor('derives') }}
                    />
                    <span className="text-white font-medium">DERIVES (NER-Based)</span>
                  </div>
                  <span className="text-green-400 font-semibold">{relationshipTypes.derives}</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-green-500 h-2 rounded-full transition-all"
                    style={{ width: `${derivesPercent}%` }}
                  />
                </div>
                <p className="text-xs text-gray-400">{derivesPercent.toFixed(1)}% of relationships</p>
              </div>

              {/* SIMILAR */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: getRelationshipColor('similar') }}
                    />
                    <span className="text-white font-medium">SIMILAR</span>
                  </div>
                  <span className="text-yellow-400 font-semibold">{relationshipTypes.similar}</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-yellow-500 h-2 rounded-full transition-all"
                    style={{ width: `${similarPercent}%` }}
                  />
                </div>
                <p className="text-xs text-gray-400">{similarPercent.toFixed(1)}% of relationships</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Type Distribution Tab */}
        <TabsContent value="types">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white">Relationship Types</CardTitle>
              <CardDescription>Quick reference for relationship meanings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* UPDATES */}
                <div className="p-4 bg-gray-700/50 rounded-lg border border-blue-600/30">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge className="bg-blue-600">UPDATES</Badge>
                  </div>
                  <p className="text-sm text-gray-300">
                    Memory updates or revises information from another memory. Indicates newer information supersedes older.
                  </p>
                </div>

                {/* EXTENDS */}
                <div className="p-4 bg-gray-700/50 rounded-lg border border-purple-600/30">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge className="bg-purple-600">EXTENDS</Badge>
                  </div>
                  <p className="text-sm text-gray-300">
                    Memory builds upon or adds to information from another memory. Complementary information.
                  </p>
                </div>

                {/* DERIVES */}
                <div className="p-4 bg-gray-700/50 rounded-lg border border-green-600/30">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge className="bg-green-600">DERIVES</Badge>
                  </div>
                  <p className="text-sm text-gray-300">
                    NER-based relationship. Memories share entities (people, organizations, locations). Automatically detected.
                  </p>
                </div>

                {/* SIMILAR */}
                <div className="p-4 bg-gray-700/50 rounded-lg border border-yellow-600/30">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge className="bg-yellow-600">SIMILAR</Badge>
                  </div>
                  <p className="text-sm text-gray-300">
                    Memories have similar semantic meaning or content. Semantically related but not explicitly connected.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Memory Tiering */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Zap className="w-5 h-5 text-yellow-400" />
                  Memory Tiering
                </CardTitle>
                <CardDescription>Hot/Cold tier optimization</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <p className="text-sm text-gray-300">
                    <span className="font-semibold">Hot Tier:</span> Recent & frequently accessed memories
                  </p>
                  <p className="text-xs text-gray-400">Search latency: &lt; 400ms</p>
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-gray-300">
                    <span className="font-semibold">Cold Tier:</span> Archived & infrequently accessed
                  </p>
                  <p className="text-xs text-gray-400">Optimized for storage</p>
                </div>
                <div className="pt-2 border-t border-gray-700">
                  <p className="text-xs text-gray-400">
                    Memories promoted to hot tier after 5+ accesses or within 30 days of creation
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Entity Extraction */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Database className="w-5 h-5 text-cyan-400" />
                  Entity Extraction
                </CardTitle>
                <CardDescription>NER-based entity detection</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <p className="text-sm text-gray-300">
                    <span className="font-semibold">Persons:</span> People names
                  </p>
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-gray-300">
                    <span className="font-semibold">Organizations:</span> Companies, institutions
                  </p>
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-gray-300">
                    <span className="font-semibold">Locations:</span> Cities, countries, regions
                  </p>
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-gray-300">
                    <span className="font-semibold">Contacts:</span> Emails, phones, URLs
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Time Decay */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-green-400" />
                  Time Decay Scoring
                </CardTitle>
                <CardDescription>Exponential decay formula</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <p className="text-sm text-gray-300 font-mono">
                    score × exp(-age_days / 90)
                  </p>
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-gray-300">
                    <span className="font-semibold">Half-life:</span> 90 days
                  </p>
                  <p className="text-xs text-gray-400">Score reduced to 50% after 90 days</p>
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-gray-300">
                    <span className="font-semibold">Recent memories:</span> Ranked higher
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Search Features */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle className="text-white">Search Features</CardTitle>
                <CardDescription>Advanced search capabilities</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <p className="text-sm text-gray-300">
                    <span className="font-semibold">Semantic Search:</span> Embedding-based matching
                  </p>
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-gray-300">
                    <span className="font-semibold">Entity Filtering:</span> Search by extracted entities
                  </p>
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-gray-300">
                    <span className="font-semibold">Relationship Filtering:</span> By relationship type
                  </p>
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-gray-300">
                    <span className="font-semibold">Time-aware Ranking:</span> Recent first
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
      </div>
    </ProtectedRoute>
  )
}
