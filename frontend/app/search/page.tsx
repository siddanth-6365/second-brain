'use client'

import { useState, useEffect } from 'react'
import { Search as SearchIcon, Loader2, Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { searchMemories } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { formatRelativeTime, getEntityColor, getRelationshipColor, truncateText } from '@/lib/utils'

interface SearchResult {
  id: string
  content: string
  score: number
  created_at: string
  entities?: Record<string, string[]>
  relationships?: Array<{
    type: string
    confidence: number
  }>
}

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [relationshipFilter, setRelationshipFilter] = useState('all')
  const [semanticWeight, setSemanticWeight] = useState('0.7')
  const { toast } = useToast()

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!query.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter a search query',
        variant: 'destructive',
      })
      return
    }

    setLoading(true)
    try {
      const data = await searchMemories(query, 20, false, [], parseFloat(semanticWeight))
      setResults(data || [])
      
      if (!data || data.length === 0) {
        toast({
          title: 'No results',
          description: 'Try a different search query',
        })
      }
    } catch (error) {
      toast({
        title: 'Search failed',
        description: error instanceof Error ? error.message : 'Failed to search memories',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const filteredResults = results.filter(result => {
    if (relationshipFilter === 'all') return true
    return result.relationships?.some(rel => rel.type === relationshipFilter)
  })

  const exportResults = () => {
    const csv = [
      ['ID', 'Content', 'Score', 'Created', 'Entities', 'Relationships'].join(','),
      ...filteredResults.map(r => [
        r.id,
        `"${r.content.replace(/"/g, '""')}"`,
        r.score.toFixed(4),
        r.created_at,
        Object.values(r.entities || {}).flat().join(';'),
        r.relationships?.map(rel => `${rel.type}(${rel.confidence.toFixed(2)})`).join(';') || ''
      ].join(','))
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `search-results-${Date.now()}.csv`
    a.click()
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <SearchIcon className="w-8 h-8 text-green-400" />
          <h1 className="text-4xl font-bold text-white">Search Memories</h1>
        </div>
        <p className="text-gray-400">
          Search across all your memories with semantic understanding and time-aware ranking
        </p>
      </div>

      {/* Search Form */}
      <Card className="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <CardTitle className="text-white">Search</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="flex gap-2">
              <Input
                placeholder="Search your memories..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="bg-gray-700 border-gray-600 text-white placeholder-gray-400 flex-1"
              />
              <Button
                type="submit"
                disabled={loading}
                className="bg-green-600 hover:bg-green-700"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <SearchIcon className="h-4 w-4" />
                )}
              </Button>
            </div>

            {/* Filters */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <label className="text-sm text-gray-300">Relationship Type</label>
                <Select value={relationshipFilter} onValueChange={setRelationshipFilter}>
                  <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-700 border-gray-600">
                    <SelectItem value="all">All Types</SelectItem>
                    <SelectItem value="updates">UPDATES</SelectItem>
                    <SelectItem value="extends">EXTENDS</SelectItem>
                    <SelectItem value="derives">DERIVES (NER)</SelectItem>
                    <SelectItem value="similar">SIMILAR</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm text-gray-300">Semantic Weight</label>
                <Select value={semanticWeight} onValueChange={setSemanticWeight}>
                  <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-700 border-gray-600">
                    <SelectItem value="0.5">50% Semantic</SelectItem>
                    <SelectItem value="0.7">70% Semantic</SelectItem>
                    <SelectItem value="0.9">90% Semantic</SelectItem>
                    <SelectItem value="1.0">100% Semantic</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {filteredResults.length > 0 && (
                <div className="flex items-end">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={exportResults}
                    className="w-full border-gray-600 text-gray-300 hover:bg-gray-700"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Export CSV
                  </Button>
                </div>
              )}
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Results */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-white">
            Results {filteredResults.length > 0 && `(${filteredResults.length})`}
          </h2>
        </div>

        {loading ? (
          <Card className="bg-gray-800/50 border-gray-700">
            <CardContent className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-400" />
            </CardContent>
          </Card>
        ) : filteredResults.length === 0 ? (
          <Card className="bg-gray-800/50 border-gray-700">
            <CardContent className="py-12 text-center">
              <p className="text-gray-400">
                {results.length === 0 ? 'No results yet. Try searching!' : 'No results match your filters.'}
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {filteredResults.map((result) => (
              <Card key={result.id} className="bg-gray-800/50 border-gray-700 hover:border-gray-600 transition-colors">
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    {/* Score and Date */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="text-sm font-semibold text-white">
                          Score: <span className="text-blue-400">{result.score.toFixed(4)}</span>
                        </div>
                        <div className="w-32 bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-blue-500 h-2 rounded-full"
                            style={{ width: `${Math.min(result.score * 100, 100)}%` }}
                          />
                        </div>
                      </div>
                      <span className="text-xs text-gray-400">{formatRelativeTime(result.created_at)}</span>
                    </div>

                    {/* Content */}
                    <p className="text-gray-300 leading-relaxed">
                      {truncateText(result.content, 300)}
                    </p>

                    {/* Entities */}
                    {result.entities && Object.values(result.entities).flat().length > 0 && (
                      <div className="space-y-2">
                        <p className="text-xs font-semibold text-gray-400 uppercase">Entities</p>
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(result.entities).map(([type, entities]) =>
                            entities.map(entity => (
                              <Badge
                                key={`${type}-${entity}`}
                                className={getEntityColor(type)}
                              >
                                {entity}
                              </Badge>
                            ))
                          )}
                        </div>
                      </div>
                    )}

                    {/* Relationships */}
                    {result.relationships && result.relationships.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-xs font-semibold text-gray-400 uppercase">Relationships</p>
                        <div className="flex flex-wrap gap-2">
                          {result.relationships.map((rel, idx) => (
                            <Badge
                              key={idx}
                              variant="outline"
                              className="border-gray-600"
                              style={{
                                borderColor: getRelationshipColor(rel.type),
                                color: getRelationshipColor(rel.type),
                              }}
                            >
                              {rel.type.toUpperCase()} ({rel.confidence.toFixed(2)})
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
