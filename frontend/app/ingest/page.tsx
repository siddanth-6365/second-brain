'use client'

import { useState } from 'react'
import { Brain, Upload, Loader2, CheckCircle, Link2, FileText } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ingestDocument } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { getEntityColor } from '@/lib/utils'
import { ProtectedRoute } from '@/components/protected-route'

export default function IngestPage() {
  const [mode, setMode] = useState<'note' | 'link' | 'file'>('note')
  const [content, setContent] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [linkUrl, setLinkUrl] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [entities, setEntities] = useState<Record<string, string[]>>({})
  const [success, setSuccess] = useState(false)
  const { toast } = useToast()

  const extractEntitiesPreview = (text: string) => {
    // Simple entity extraction preview (regex-based)
    const extracted: Record<string, string[]> = {
      persons: [],
      organizations: [],
      locations: [],
      emails: [],
      urls: [],
      phones: [],
    }

    // Extract emails
    const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g
    extracted.emails = Array.from(new Set(text.match(emailRegex) || []))

    // Extract URLs
    const urlRegex = /https?:\/\/[^\s]+/g
    extracted.urls = Array.from(new Set(text.match(urlRegex) || []))

    // Extract phone numbers
    const phoneRegex = /\(?[\d\s\-+()]{10,}\)?/g
    extracted.phones = Array.from(new Set(text.match(phoneRegex) || [])).slice(0, 3)

    // Extract capitalized words (simple person/org/location detection)
    const capitalizedRegex = /\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b/g
    const capitalized = Array.from(new Set(text.match(capitalizedRegex) || []))
    
    // Simple heuristic: if followed by "Inc", "Corp", "Ltd" -> organization
    const orgKeywords = ['Inc', 'Corp', 'Ltd', 'LLC', 'Company', 'Organization', 'University', 'Bank']
    extracted.organizations = capitalized.filter(word => 
      orgKeywords.some(keyword => text.includes(`${word} ${keyword}`))
    ).slice(0, 5)

    // Rest are persons
    extracted.persons = capitalized
      .filter(word => !extracted.organizations.includes(word))
      .slice(0, 5)

    // Extract locations (common city/country names)
    const locationKeywords = ['San Francisco', 'New York', 'London', 'Paris', 'Tokyo', 'Seattle', 'California', 'USA', 'UK', 'India']
    extracted.locations = locationKeywords.filter(loc => text.includes(loc))

    return extracted
  }

  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const text = e.target.value
    setContent(text)
    if (mode === 'note' && text.length > 20) {
      setEntities(extractEntitiesPreview(text))
    } else {
      setEntities({})
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (mode === 'note' && !content.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter some content',
        variant: 'destructive',
      })
      return
    }

    if (mode === 'link' && !linkUrl.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter a valid link',
        variant: 'destructive',
      })
      return
    }

    if (mode === 'file' && !selectedFile) {
      toast({
        title: 'Error',
        description: 'Please choose a file to upload',
        variant: 'destructive',
      })
      return
    }

    setLoading(true)
    try {
      await ingestDocument({
        type: mode,
        title: title || undefined,
        description: description || undefined,
        content: mode === 'note' ? content : undefined,
        url: mode === 'link' ? linkUrl : undefined,
        file: mode === 'file' ? selectedFile : undefined,
      })

      toast({
        title: 'Success!',
        description: 'Memory ingested successfully',
      })

      setSuccess(true)
      setContent('')
      setTitle('')
      setDescription('')
      setLinkUrl('')
      setSelectedFile(null)
      setEntities({})

      setTimeout(() => setSuccess(false), 3000)
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to ingest document',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const totalEntities = mode === 'note' ? Object.values(entities).flat().length : 0

  return (
    <ProtectedRoute>
      <div className="space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <Brain className="w-8 h-8 text-blue-400" />
          <h1 className="text-4xl font-bold text-white">Add Memory</h1>
        </div>
        <p className="text-gray-400">
          Capture notes, links, or files. The system enriches them with entities, embeddings, and relationships automatically.
        </p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Form */}
        <div className="lg:col-span-2">
          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white">Create New Memory</CardTitle>
              <CardDescription>Enter content and optional metadata</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-2">
                  <Label className="text-gray-300">Memory Type</Label>
                  <Tabs value={mode} onValueChange={(val) => setMode(val as typeof mode)}>
                    <TabsList className="grid grid-cols-3 bg-gray-800/80 text-white">
                      <TabsTrigger value="note">Note</TabsTrigger>
                      <TabsTrigger value="link">Link</TabsTrigger>
                      <TabsTrigger value="file">File</TabsTrigger>
                    </TabsList>
                  </Tabs>
                </div>

                {/* Title */}
                <div className="space-y-2">
                  <Label htmlFor="title" className="text-gray-300">Title (Optional)</Label>
                  <Input
                    id="title"
                    placeholder="Give this memory a title..."
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="bg-gray-700 border-gray-600 text-white placeholder-gray-400"
                  />
                </div>

                {/* Description */}
                <div className="space-y-2">
                  <Label htmlFor="description" className="text-gray-300">Description (Optional)</Label>
                  <Input
                    id="description"
                    placeholder="Add a quick description..."
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="bg-gray-700 border-gray-600 text-white placeholder-gray-400"
                  />
                </div>

                {mode === 'note' && (
                  <div className="space-y-2">
                    <Label htmlFor="content" className="text-gray-300">Content</Label>
                    <Textarea
                      id="content"
                      placeholder="Paste your text here... (emails, articles, notes, etc.)"
                      value={content}
                      onChange={handleContentChange}
                      rows={10}
                      className="bg-gray-700 border-gray-600 text-white placeholder-gray-400 resize-none"
                    />
                    <p className="text-xs text-gray-400">{content.length} characters</p>
                  </div>
                )}

                {mode === 'link' && (
                  <div className="space-y-2">
                    <Label htmlFor="link" className="text-gray-300">Link URL</Label>
                    <Input
                      id="link"
                      type="url"
                      placeholder="https://example.com/article"
                      value={linkUrl}
                      onChange={(e) => setLinkUrl(e.target.value)}
                      className="bg-gray-700 border-gray-600 text-white placeholder-gray-400"
                    />
                  </div>
                )}

                {mode === 'file' && (
                  <div className="space-y-2">
                    <Label htmlFor="file" className="text-gray-300">Upload File</Label>
                    <Input
                      id="file"
                      type="file"
                      accept=".pdf,.docx,.txt,.md"
                      onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                      className="bg-gray-700 border-gray-600 text-white placeholder-gray-400"
                    />
                    {selectedFile && (
                      <p className="text-xs text-gray-400">
                        Selected: {selectedFile.name} ({Math.round(selectedFile.size / 1024)} KB)
                      </p>
                    )}
                  </div>
                )}

                {/* Submit */}
                <Button
                  type="submit"
                  disabled={
                    loading ||
                    (mode === 'note' && !content.trim()) ||
                    (mode === 'link' && !linkUrl.trim()) ||
                    (mode === 'file' && !selectedFile)
                  }
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Ingesting...
                    </>
                  ) : success ? (
                    <>
                      <CheckCircle className="mr-2 h-4 w-4" />
                      Memory Added!
                    </>
                  ) : (
                    <>
                      <Upload className="mr-2 h-4 w-4" />
                      Add Memory
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Entity / Source Preview */}
        <div className="space-y-4">
          <Card className="bg-gray-800/50 border-gray-700 sticky top-24">
            <CardHeader>
              <CardTitle className="text-white text-lg">
                {mode === 'note' ? 'Entity Preview' : 'Input Summary'}
              </CardTitle>
              <CardDescription>
                {mode === 'note'
                  ? 'Extracted from your content'
                  : mode === 'link'
                    ? 'Link metadata'
                    : 'File details'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {mode === 'note' ? (
                totalEntities === 0 ? (
                  <p className="text-gray-400 text-sm">Start typing to see extracted entities...</p>
                ) : (
                  <>
                    {/* Persons */}
                    {entities.persons && entities.persons.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-xs font-semibold text-gray-300 uppercase">Persons ({entities.persons.length})</p>
                        <div className="flex flex-wrap gap-2">
                          {entities.persons.map((person) => (
                            <Badge key={person} className={getEntityColor('persons')}>
                              {person}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Organizations */}
                    {entities.organizations && entities.organizations.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-xs font-semibold text-gray-300 uppercase">Organizations ({entities.organizations.length})</p>
                        <div className="flex flex-wrap gap-2">
                          {entities.organizations.map((org) => (
                            <Badge key={org} className={getEntityColor('organizations')}>
                              {org}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Locations */}
                    {entities.locations && entities.locations.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-xs font-semibold text-gray-300 uppercase">Locations ({entities.locations.length})</p>
                        <div className="flex flex-wrap gap-2">
                          {entities.locations.map((loc) => (
                            <Badge key={loc} className={getEntityColor('locations')}>
                              {loc}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Emails */}
                    {entities.emails && entities.emails.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-xs font-semibold text-gray-300 uppercase">Emails ({entities.emails.length})</p>
                        <div className="flex flex-wrap gap-2">
                          {entities.emails.map((email) => (
                            <Badge key={email} className={getEntityColor('emails')} variant="outline">
                              {email}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* URLs */}
                    {entities.urls && entities.urls.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-xs font-semibold text-gray-300 uppercase">URLs ({entities.urls.length})</p>
                        <div className="flex flex-wrap gap-2">
                          {entities.urls.map((url) => (
                            <Badge key={url} className={getEntityColor('urls')} variant="outline">
                              {url.slice(0, 20)}...
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Phones */}
                    {entities.phones && entities.phones.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-xs font-semibold text-gray-300 uppercase">Phones ({entities.phones.length})</p>
                        <div className="flex flex-wrap gap-2">
                          {entities.phones.map((phone) => (
                            <Badge key={phone} className={getEntityColor('phones')} variant="outline">
                              {phone}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="pt-4 border-t border-gray-700">
                      <p className="text-xs text-gray-400">
                        Total: <span className="font-semibold text-blue-400">{totalEntities}</span> entities
                      </p>
                    </div>
                  </>
                )
              ) : mode === 'link' ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-white/80">
                    <Link2 className="h-4 w-4 text-blue-400" />
                    <span>Link preview</span>
                  </div>
                  {linkUrl ? (
                    <p className="text-sm text-blue-300 break-all">{linkUrl}</p>
                  ) : (
                    <p className="text-gray-400 text-sm">Paste a link to see details.</p>
                  )}
                </div>
              ) : (
                <>
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-white/80">
                      <FileText className="h-4 w-4 text-blue-400" />
                      <span>File details</span>
                    </div>
                    {selectedFile ? (
                      <div className="text-sm text-white/80">
                        <p>{selectedFile.name}</p>
                        <p className="text-white/50">{Math.round(selectedFile.size / 1024)} KB</p>
                      </div>
                    ) : (
                      <p className="text-gray-400 text-sm">Upload a file to extract its contents.</p>
                    )}
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
      </div>
    </ProtectedRoute>
  )
}
