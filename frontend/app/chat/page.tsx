'use client'

import { useState, useRef, useEffect } from 'react'
import { MessageSquare, Send, Loader2, Copy, CheckCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { chatWithMemories } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { formatRelativeTime, truncateText } from '@/lib/utils'
import { useSearchParams } from 'next/navigation'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Components } from 'react-markdown'
import { ProtectedRoute } from '@/components/protected-route'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  memories?: Array<{
    id: string
    content: string
    score: number
    created_at: string
  }>
  timestamp: Date
}

const markdownComponents: Components = {
  table: ({ node, ...props }) => (
    <div className="overflow-x-auto rounded-lg border border-white/10">
      <table
        {...props}
        className="w-full border-collapse text-sm text-white/90 [&_th]:font-semibold"
      />
    </div>
  ),
  th: ({ node, ...props }) => (
    <th
      {...props}
      className="border border-white/10 bg-white/10 px-3 py-2 text-left text-white"
    />
  ),
  td: ({ node, ...props }) => (
    <td
      {...props}
      className="border border-white/10 px-3 py-2 align-top text-white/90"
    />
  ),
  a: ({ node, ...props }) => (
    <a
      {...props}
      className="text-blue-300 underline hover:text-blue-200 break-words"
      target="_blank"
      rel="noreferrer"
    />
  ),
  ul: ({ node, ordered, ...props }) => (
    <ul {...props} className="list-disc list-inside space-y-1 text-white/90" />
  ),
  ol: ({ node, ordered, ...props }) => (
    <ol {...props} className="list-decimal list-inside space-y-1 text-white/90" />
  ),
  li: ({ node, ordered, ...props }) => <li {...props} className="leading-relaxed" />,
  p: ({ node, ...props }) => <p {...props} className="leading-relaxed text-white/90" />,
  code: ({ node, inline, ...props }) =>
    inline ? (
      <code {...props} className="rounded bg-white/10 px-1 py-0.5 text-sm" />
    ) : (
      <code
        {...props}
        className="block rounded bg-black/40 p-3 text-sm text-white/90 overflow-x-auto"
      />
    ),
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { toast } = useToast()
  const searchParams = useSearchParams()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Handle query parameter from homepage
  useEffect(() => {
    const query = searchParams.get('q')
    if (query) {
      setInput(decodeURIComponent(query))
    }
  }, [searchParams])

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!input.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter a message',
        variant: 'destructive',
      })
      return
    }

    // Add user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await chatWithMemories(input, 5, 'openai/gpt-oss-20b')

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.response || response.answer || 'No response',
        memories: response.memories || [],
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to get response',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  return (
    <ProtectedRoute>
      <div className="space-y-6 h-[calc(100vh-200px)] flex flex-col">
        {/* Header */}
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <MessageSquare className="w-8 h-8 text-yellow-400" />
            <h1 className="text-4xl font-bold text-white">Chat with Memories</h1>
          </div>
          <p className="text-white/70">
            Ask questions about your memories. Powered by RAG with Groq LLM and your knowledge graph.
          </p>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-4">
          {messages.length === 0 ? (
            <Card className="glass-card h-full flex items-center justify-center">
              <CardContent className="text-center py-12">
                <MessageSquare className="w-16 h-16 text-white/30 mx-auto mb-4" />
                <p className="text-white/70 mb-2">No messages yet</p>
                <p className="text-white/50 text-sm">Ask a question about your memories to get started</p>
              </CardContent>
            </Card>
          ) : (
            messages.map((message) => (
              <div key={message.id} className="space-y-2">
                {/* Message */}
                <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <Card
                    className={`max-w-2xl glass-card-hover ${message.role === 'user'
                        ? 'bg-blue-500/20 border-blue-400/30'
                        : 'bg-white/10 border-white/20'
                      }`}
                  >
                    <CardContent className="pt-4 space-y-4">
                      {message.role === 'assistant' ? (
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={markdownComponents}
                          className="space-y-3 text-sm text-white/90"
                        >
                          {message.content}
                        </ReactMarkdown>
                      ) : (
                        <p className="text-white/90 whitespace-pre-wrap">{message.content}</p>
                      )}
                      <div className="flex items-center justify-between mt-3">
                        <span className="text-xs text-white/50">
                          {message.timestamp.toLocaleTimeString()}
                        </span>
                        {message.role === 'assistant' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => copyToClipboard(message.content, message.id)}
                            className="h-6 w-6 p-0 text-white/50 hover:text-white/90 transition-colors"
                          >
                            {copiedId === message.id ? (
                              <CheckCircle className="h-4 w-4 text-green-400" />
                            ) : (
                              <Copy className="h-4 w-4" />
                            )}
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Context Memories */}
                {message.memories && message.memories.length > 0 && (
                  <div className="ml-4 space-y-2">
                    <p className="text-xs font-semibold text-white/50 uppercase">Context Memories</p>
                    <div className="space-y-2">
                      {message.memories.map((memory) => (
                        <Card
                          key={memory.id}
                          className="glass-card text-xs hover:bg-white/15 transition-colors"
                        >
                          <CardContent className="pt-3">
                            <div className="flex items-start justify-between gap-2">
                              <p className="text-white/80 flex-1">
                                {truncateText(memory.content, 150)}
                              </p>
                              <Badge className="bg-blue-500/30 text-blue-300 border-blue-400/50 flex-shrink-0">
                                {memory.score.toFixed(3)}
                              </Badge>
                            </div>
                            <p className="text-white/50 mt-2">
                              {formatRelativeTime(memory.created_at)}
                            </p>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        <Separator className="bg-white/10" />

        {/* Input Form */}
        <form onSubmit={handleSendMessage} className="flex gap-2">
          <Input
            placeholder="Ask something about your memories..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            className="glass-card bg-white/5 border-white/20 text-white placeholder-white/40 flex-1 focus:bg-white/10 focus:border-white/30 transition-colors"
          />
          <Button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>
      </div>
    </ProtectedRoute>
  )
}
