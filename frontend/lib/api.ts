import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Health & Stats
export const getHealth = async () => {
  const response = await api.get('/health')
  return response.data
}

export const getGraphStats = async () => {
  const response = await api.get('/graph/stats')
  return response.data
}

export const exportGraph = async () => {
  const response = await api.get('/graph/export')
  return response.data
}

// Document Operations
export const ingestDocument = async (content: string, title?: string, source?: string) => {
  const response = await api.post('/documents/ingest', {
    content,
    title: title || undefined,
    source: source || undefined,
  })
  return response.data
}

export const getDocumentMemories = async (documentId: string, skip = 0, limit = 50) => {
  const response = await api.get(`/documents/${documentId}/memories`, {
    params: { skip, limit },
  })
  return response.data
}

// Memory Operations
export const searchMemories = async (
  query: string,
  limit = 10,
  onlyLatest = false,
  keywords: string[] = [],
  semanticWeight = 0.7
) => {
  const response = await api.post('/memories/search', {
    query,
    limit,
    only_latest: onlyLatest,
    keywords,
    semantic_weight: semanticWeight,
  })
  return response.data
}

export const getMemory = async (memoryId: string) => {
  const response = await api.get(`/memories/${memoryId}`)
  return response.data
}

export const getRelatedMemories = async (memoryId: string, maxDepth = 2) => {
  const response = await api.get(`/memories/${memoryId}/related`, {
    params: { max_depth: maxDepth },
  })
  return response.data
}

export const getMemoryTimeline = async (topic: string) => {
  const response = await api.get(`/memories/timeline/${encodeURIComponent(topic)}`)
  return response.data
}

// Chat
export const chat = async (
  question: string,
  maxMemories = 5,
  model = 'openai/gpt-oss-20b'
) => {
  const response = await api.post('/chat', {
    question,
    max_memories: maxMemories,
    model,
  })
  return response.data
}

// Admin
export const clearAllData = async () => {
  const response = await api.delete('/admin/clear-all')
  return response.data
}

// Error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error
      throw new Error(error.response.data.detail || error.response.data.message || 'Server error')
    } else if (error.request) {
      // Request made but no response
      throw new Error('No response from server. Is the backend running on port 8000?')
    } else {
      // Request setup error
      throw new Error(error.message)
    }
  }
)

export default api
