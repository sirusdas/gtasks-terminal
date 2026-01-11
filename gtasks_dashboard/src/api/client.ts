/**
 * API client for GTasks Dashboard
 * Handles communication with the backend server and MCP integration
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios'
import type {
  Task,
  Account,
  ApiResponse,
  PaginatedResponse,
  MCPMessage,
  WebSocketEvent,
  CreateTaskForm,
  UpdateTaskForm,
  DashboardData,
  GraphData,
  UserSettings
} from '@/types'

class APIClient {
  private client: AxiosInstance
  private ws: WebSocket | null = null
  private wsCallbacks: Map<string, (data: any) => void> = new Map()

  constructor(baseURL: string = 'http://localhost:8080') {
    this.client = axios.create({
      baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    // Request interceptor for auth
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error.response?.data || error.message)
        throw error
      }
    )
  }

  // Generic request method
  private async request<T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    endpoint: string,
    data?: any
  ): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<ApiResponse<T>> = await this.client.request({
        method,
        url: endpoint,
        data
      })
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        return {
          success: false,
          error: error.response?.data?.error || error.message,
          timestamp: new Date().toISOString()
        }
      }
      throw error
    }
  }

  // Task API methods
  async getTasks(filters?: any): Promise<ApiResponse<Task[]>> {
    const params = new URLSearchParams()
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            value.forEach(v => params.append(key, v.toString()))
          } else {
            params.append(key, value.toString())
          }
        }
      })
    }
    return this.request<Task[]>('GET', `/api/tasks?${params.toString()}`)
  }

  async getTask(id: string): Promise<ApiResponse<Task>> {
    return this.request<Task>('GET', `/api/tasks/${id}`)
  }

  async createTask(task: CreateTaskForm): Promise<ApiResponse<Task>> {
    return this.request<Task>('POST', '/api/tasks', task)
  }

  async updateTask(id: string, updates: UpdateTaskForm): Promise<ApiResponse<Task>> {
    return this.request<Task>('PUT', `/api/tasks/${id}`, updates)
  }

  async deleteTask(id: string): Promise<ApiResponse<void>> {
    return this.request<void>('DELETE', `/api/tasks/${id}`)
  }

  async completeTask(id: string): Promise<ApiResponse<Task>> {
    return this.request<Task>('POST', `/api/tasks/${id}/complete`)
  }

  // Deleted task management methods
  async softDeleteTask(id: string): Promise<ApiResponse<Task>> {
    return this.request<Task>('POST', `/api/tasks/${id}/soft-delete`)
  }

  async restoreTask(id: string): Promise<ApiResponse<Task>> {
    return this.request<Task>('POST', `/api/tasks/${id}/restore`)
  }

  async permanentlyDeleteTask(id: string): Promise<ApiResponse<void>> {
    return this.request<void>('DELETE', `/api/tasks/${id}/permanently`)
  }

  async getDeletedTasks(filters?: any): Promise<ApiResponse<Task[]>> {
    const params = new URLSearchParams()
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString())
        }
      })
    }
    return this.request<Task[]>('GET', `/api/tasks/deleted?${params.toString()}`)
  }

  // Settings API methods
  async getSettings(): Promise<ApiResponse<UserSettings>> {
    return this.request<UserSettings>('GET', '/api/settings')
  }

  async updateSettings(settings: Partial<UserSettings>): Promise<ApiResponse<UserSettings>> {
    return this.request<UserSettings>('POST', '/api/settings', settings)
  }

  // Account API methods
  async getAccounts(): Promise<ApiResponse<Account[]>> {
    return this.request<Account[]>('GET', '/api/accounts')
  }

  async getAccount(id: string): Promise<ApiResponse<Account>> {
    return this.request<Account>('GET', `/api/accounts/${id}`)
  }

  async createAccount(account: Partial<Account>): Promise<ApiResponse<Account>> {
    return this.request<Account>('POST', '/api/accounts', account)
  }

  async updateAccount(id: string, updates: Partial<Account>): Promise<ApiResponse<Account>> {
    return this.request<Account>('PUT', `/api/accounts/${id}`, updates)
  }

  async deleteAccount(id: string): Promise<ApiResponse<void>> {
    return this.request<void>('DELETE', `/api/accounts/${id}`)
  }

  // Dashboard API methods
  async getDashboardData(accountId?: string): Promise<ApiResponse<DashboardData>> {
    const params = accountId ? `?accountId=${accountId}` : ''
    return this.request<DashboardData>('GET', `/api/dashboard${params}`)
  }

  async getGraphData(accountId?: string): Promise<ApiResponse<GraphData>> {
    const params = accountId ? `?accountId=${accountId}` : ''
    return this.request<GraphData>('GET', `/api/graph${params}`)
  }

  async getStats(accountId?: string): Promise<ApiResponse<any>> {
    const params = accountId ? `?accountId=${accountId}` : ''
    return this.request<any>('GET', `/api/stats${params}`)
  }

  // Sync API methods
  async syncAccount(accountId: string): Promise<ApiResponse<{ status: string; message: string }>> {
    return this.request('POST', `/api/sync/${accountId}`)
  }

  async syncAllAccounts(): Promise<ApiResponse<{ synced: number; failed: number }>> {
    return this.request('POST', '/api/sync/all')
  }

  // Configuration API methods
  async getConfig(): Promise<ApiResponse<any>> {
    return this.request('GET', '/api/config')
  }

  async updateConfig(config: any): Promise<ApiResponse<any>> {
    return this.request('PUT', '/api/config', config)
  }

  // MCP (Model Context Protocol) methods
  async sendMCPMessage(message: Omit<MCPMessage, 'id' | 'timestamp'>): Promise<ApiResponse<MCPMessage>> {
    const fullMessage: MCPMessage = {
      ...message,
      id: this.generateId(),
      timestamp: new Date().toISOString()
    }
    return this.request<MCPMessage>('POST', '/api/mcp/message', fullMessage)
  }

  async getMCPTools(): Promise<ApiResponse<any[]>> {
    return this.request<any[]>('GET', '/api/mcp/tools')
  }

  // Search API methods
  async searchTasks(query: string, filters?: any): Promise<ApiResponse<Task[]>> {
    const params = new URLSearchParams({ q: query })
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString())
        }
      })
    }
    return this.request<Task[]>('GET', `/api/search/tasks?${params.toString()}`)
  }

  // Export/Import methods
  async exportTasks(accountId?: string, format: 'json' | 'csv' = 'json'): Promise<Blob> {
    const params = accountId ? `?accountId=${accountId}&format=${format}` : `?format=${format}`
    const response = await this.client.get(`/api/export/tasks${params}`, {
      responseType: 'blob'
    })
    return response.data
  }

  async importTasks(file: File, accountId?: string): Promise<ApiResponse<{ imported: number; errors: string[] }>> {
    const formData = new FormData()
    formData.append('file', file)
    if (accountId) {
      formData.append('accountId', accountId)
    }

    return this.request('POST', '/api/import/tasks', formData)
  }

  // WebSocket methods
  connectWebSocket(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return
    }

    const wsURL = this.client.defaults.baseURL?.replace('http', 'ws') + '/ws'
    this.ws = new WebSocket(wsURL)

    this.ws.onopen = () => {
      console.log('WebSocket connected')
      this.emit('connected', {})
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.emit(data.type, data)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    this.ws.onclose = () => {
      console.log('WebSocket disconnected')
      this.emit('disconnected', {})
      // Attempt to reconnect after 5 seconds
      setTimeout(() => {
        this.connectWebSocket()
      }, 5000)
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      this.emit('error', { error })
    }
  }

  disconnectWebSocket(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  on(event: string, callback: (data: any) => void): void {
    this.wsCallbacks.set(event, callback)
  }

  off(event: string): void {
    this.wsCallbacks.delete(event)
  }

  private emit(event: string, data: any): void {
    const callback = this.wsCallbacks.get(event)
    if (callback) {
      callback(data)
    }
  }

  // Utility methods
  private generateId(): string {
    return Math.random().toString(36).substr(2, 9)
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<{ status: string; version: string }>> {
    return this.request('GET', '/api/health')
  }
}

// Create and export singleton instance
export const apiClient = new APIClient()

// Export hooks for React components
export const useAPI = () => {
  return {
    // Task operations
    getTasks: (filters?: any) => apiClient.getTasks(filters),
    getTask: (id: string) => apiClient.getTask(id),
    createTask: (task: CreateTaskForm) => apiClient.createTask(task),
    updateTask: (id: string, updates: UpdateTaskForm) => apiClient.updateTask(id, updates),
    deleteTask: (id: string) => apiClient.deleteTask(id),
    completeTask: (id: string) => apiClient.completeTask(id),
    softDeleteTask: (id: string) => apiClient.softDeleteTask(id),
    restoreTask: (id: string) => apiClient.restoreTask(id),
    permanentlyDeleteTask: (id: string) => apiClient.permanentlyDeleteTask(id),
    getDeletedTasks: (filters?: any) => apiClient.getDeletedTasks(filters),

    // Settings operations
    getSettings: () => apiClient.getSettings(),
    updateSettings: (settings: Partial<UserSettings>) => apiClient.updateSettings(settings),

    // Account operations
    getAccounts: () => apiClient.getAccounts(),
    getAccount: (id: string) => apiClient.getAccount(id),
    createAccount: (account: Partial<Account>) => apiClient.createAccount(account),
    updateAccount: (id: string, updates: Partial<Account>) => apiClient.updateAccount(id, updates),
    deleteAccount: (id: string) => apiClient.deleteAccount(id),

    // Dashboard operations
    getDashboardData: (accountId?: string) => apiClient.getDashboardData(accountId),
    getGraphData: (accountId?: string) => apiClient.getGraphData(accountId),
    getStats: (accountId?: string) => apiClient.getStats(accountId),

    // Sync operations
    syncAccount: (accountId: string) => apiClient.syncAccount(accountId),
    syncAllAccounts: () => apiClient.syncAllAccounts(),

    // MCP operations
    sendMCPMessage: (message: Omit<MCPMessage, 'id' | 'timestamp'>) => apiClient.sendMCPMessage(message),
    getMCPTools: () => apiClient.getMCPTools(),

    // Search operations
    searchTasks: (query: string, filters?: any) => apiClient.searchTasks(query, filters),

    // Export/Import
    exportTasks: (accountId?: string, format?: 'json' | 'csv') => apiClient.exportTasks(accountId, format),
    importTasks: (file: File, accountId?: string) => apiClient.importTasks(file, accountId),

    // WebSocket
    connectWebSocket: () => apiClient.connectWebSocket(),
    disconnectWebSocket: () => apiClient.disconnectWebSocket(),
    on: (event: string, callback: (data: any) => void) => apiClient.on(event, callback),
    off: (event: string) => apiClient.off(event),

    // Utility
    healthCheck: () => apiClient.healthCheck()
  }
}

export default APIClient