import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays} days ago`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`
  return `${Math.floor(diffDays / 365)} years ago`
}

export function calculateTimeDecay(createdAt: string, halfLife: number = 90): number {
  const created = new Date(createdAt)
  const now = new Date()
  const ageDays = (now.getTime() - created.getTime()) / (1000 * 60 * 60 * 24)
  return Math.exp(-ageDays / halfLife)
}

export function getEntityColor(entityType: string): string {
  const colors: Record<string, string> = {
    persons: 'bg-blue-500/20 text-blue-400 border-blue-500/50',
    organizations: 'bg-purple-500/20 text-purple-400 border-purple-500/50',
    locations: 'bg-green-500/20 text-green-400 border-green-500/50',
    emails: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
    urls: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/50',
    phones: 'bg-orange-500/20 text-orange-400 border-orange-500/50',
    keywords: 'bg-gray-500/20 text-gray-400 border-gray-500/50',
  }
  return colors[entityType] || colors.keywords
}

export function getRelationshipColor(type: string): string {
  const colors: Record<string, string> = {
    updates: '#3b82f6', // blue
    extends: '#a855f7', // purple
    derives: '#22c55e', // green
    similar: '#eab308', // yellow
  }
  return colors[type] || '#6b7280'
}

export function truncateText(text: string, maxLength: number = 100): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

export function highlightEntities(text: string, entities: string[]): string {
  let highlighted = text
  entities.forEach(entity => {
    const regex = new RegExp(`\\b${entity}\\b`, 'gi')
    highlighted = highlighted.replace(regex, `<mark class="bg-yellow-200 dark:bg-yellow-900/50">$&</mark>`)
  })
  return highlighted
}
