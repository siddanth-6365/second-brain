'use client'

import { useState, useEffect, useRef } from 'react'
import { Send, Bot, User, Loader2, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Card } from '@/components/ui/card'
import { useToast } from '@/hooks/use-toast'
import { chatWithMemories, getChatHistory, clearChatHistory } from '@/lib/api'

interface ChatMessage {
    role: 'user' | 'assistant'
    content: string
    timestamp?: string
}

export function ChatInterface() {
    const [messages, setMessages] = useState<ChatMessage[]>([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const scrollRef = useRef<HTMLDivElement>(null)
    const { toast } = useToast()

    useEffect(() => {
        loadHistory()
    }, [])

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: 'smooth' })
        }
    }, [messages])

    const loadHistory = async () => {
        try {
            const history = await getChatHistory()
            if (history && Array.isArray(history.history)) {
                setMessages(history.history)
            }
        } catch (error) {
            console.error("Failed to load chat history:", error)
        }
    }

    const handleClearHistory = async () => {
        try {
            await clearChatHistory()
            setMessages([])
            toast({
                title: "History cleared",
                description: "Chat history has been deleted.",
            })
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to clear history.",
                variant: "destructive"
            })
        }
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!input.trim() || loading) return

        const userMessage = input.trim()
        setInput('')
        setMessages(prev => [...prev, { role: 'user', content: userMessage }])
        setLoading(true)

        try {
            const response = await chatWithMemories(userMessage)
            setMessages(prev => [...prev, { role: 'assistant', content: response.answer }])
        } catch (error) {
            console.error("Chat error:", error)
            toast({
                title: "Error",
                description: "Failed to get response from AI.",
                variant: "destructive"
            })
            setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I encountered an error while processing your request." }])
        } finally {
            setLoading(false)
        }
    }

    return (
        <Card className="glass-card flex flex-col h-[600px] overflow-hidden">
            <div className="p-4 border-b border-white/10 flex justify-between items-center bg-black/20">
                <div className="flex items-center gap-2">
                    <Bot className="w-5 h-5 text-blue-400" />
                    <h3 className="font-semibold text-white">Chat with Memory</h3>
                </div>
                <Button variant="ghost" size="icon" onClick={handleClearHistory} className="text-white/50 hover:text-red-400">
                    <Trash2 className="w-4 h-4" />
                </Button>
            </div>

            <ScrollArea className="flex-1 p-4">
                <div className="space-y-4">
                    {messages.length === 0 && (
                        <div className="text-center text-white/30 mt-20">
                            <Bot className="w-12 h-12 mx-auto mb-2 opacity-50" />
                            <p>Ask me anything about your memories...</p>
                        </div>
                    )}
                    {messages.map((msg, idx) => (
                        <div
                            key={idx}
                            className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            {msg.role === 'assistant' && (
                                <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0 border border-blue-500/30">
                                    <Bot className="w-4 h-4 text-blue-400" />
                                </div>
                            )}
                            <div
                                className={`max-w-[80%] rounded-lg p-3 text-sm ${msg.role === 'user'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-white/10 text-white/90 border border-white/10'
                                    }`}
                            >
                                {msg.content}
                            </div>
                            {msg.role === 'user' && (
                                <div className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center flex-shrink-0 border border-purple-500/30">
                                    <User className="w-4 h-4 text-purple-400" />
                                </div>
                            )}
                        </div>
                    ))}
                    {loading && (
                        <div className="flex gap-3 justify-start">
                            <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0 border border-blue-500/30">
                                <Bot className="w-4 h-4 text-blue-400" />
                            </div>
                            <div className="bg-white/10 rounded-lg p-3 flex items-center">
                                <Loader2 className="w-4 h-4 animate-spin text-white/50" />
                            </div>
                        </div>
                    )}
                    <div ref={scrollRef} />
                </div>
            </ScrollArea>

            <div className="p-4 border-t border-white/10 bg-black/20">
                <form onSubmit={handleSubmit} className="flex gap-2">
                    <Input
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask a question..."
                        className="glass-input text-white border-white/10 focus:border-blue-500/50"
                        disabled={loading}
                    />
                    <Button type="submit" disabled={loading || !input.trim()} className="bg-blue-600 hover:bg-blue-700">
                        <Send className="w-4 h-4" />
                    </Button>
                </form>
            </div>
        </Card>
    )
}
