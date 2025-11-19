'use client'

import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
} from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { formatRelativeTime } from "@/lib/utils"
import { ExternalLink, Calendar, Tag, FileText } from "lucide-react"

interface GraphNode {
    id: string
    name: string
    content: string
    created_at: string
    entities?: Record<string, string[]>
    color?: string
}

interface MemoryDetailDialogProps {
    node: GraphNode | null
    open: boolean
    onOpenChange: (open: boolean) => void
}

export function MemoryDetailDialog({ node, open, onOpenChange }: MemoryDetailDialogProps) {
    if (!node) return null

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="glass-card border-white/10 text-white max-w-2xl max-h-[80vh] flex flex-col">
                <DialogHeader>
                    <DialogTitle className="text-xl font-bold flex items-center gap-2">
                        <FileText className="w-5 h-5 text-blue-400" />
                        Memory Details
                    </DialogTitle>
                    <DialogDescription className="text-white/50">
                        Created {formatRelativeTime(node.created_at)}
                    </DialogDescription>
                </DialogHeader>

                <ScrollArea className="flex-1 pr-4">
                    <div className="space-y-6">
                        {/* Content Section */}
                        <div className="space-y-2">
                            <h3 className="text-sm font-semibold text-white/70 uppercase tracking-wider">Content</h3>
                            <div className="bg-white/5 rounded-lg p-4 border border-white/10 whitespace-pre-wrap text-white/90 leading-relaxed">
                                {node.content}
                            </div>
                        </div>

                        {/* Entities Section */}
                        {node.entities && Object.keys(node.entities).length > 0 && (
                            <div className="space-y-2">
                                <h3 className="text-sm font-semibold text-white/70 uppercase tracking-wider flex items-center gap-2">
                                    <Tag className="w-4 h-4" /> Entities
                                </h3>
                                <div className="flex flex-wrap gap-2">
                                    {Object.entries(node.entities).map(([type, values]) =>
                                        values.map((value, idx) => (
                                            <Badge key={`${type}-${idx}`} variant="outline" className="bg-blue-500/10 border-blue-500/30 text-blue-300 hover:bg-blue-500/20">
                                                <span className="opacity-50 mr-1 text-xs">{type}:</span>
                                                {value}
                                            </Badge>
                                        ))
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Metadata Section (if any) */}
                        <div className="grid grid-cols-2 gap-4 text-sm">
                            <div className="bg-white/5 p-3 rounded-md border border-white/10">
                                <span className="text-white/50 block mb-1">ID</span>
                                <code className="text-xs bg-black/30 px-1 py-0.5 rounded text-white/80">{node.id}</code>
                            </div>
                            {/* Add more metadata fields here if available */}
                        </div>
                    </div>
                </ScrollArea>
            </DialogContent>
        </Dialog>
    )
}
