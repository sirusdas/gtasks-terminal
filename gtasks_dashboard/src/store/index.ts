import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { subscribeWithSelector } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
import type { 
  Task, 
  Account, 
  DashboardData, 
  TaskFilters, 
  DashboardConfig, 
  RealtimeData,
  DashboardError 
} from '@/types'

interface DashboardState {
  // Data
  tasks: Task[]
  accounts: Account[]
  activeAccount: string | null
  
  // UI State
  filters: TaskFilters
  config: DashboardConfig
  loading: boolean
  errors: DashboardError[]
  
  // Real-time
  realtime: RealtimeData
  
  // Actions
  setTasks: (tasks: Task[]) => void
  addTask: (task: Task) => void
  updateTask: (id: string, updates: Partial<Task>) => void
  deleteTask: (id: string) => void
  
  setAccounts: (accounts: Account[]) => void
  addAccount: (account: Account) => void
  updateAccount: (id: string, updates: Partial<Account>) => void
  setActiveAccount: (accountId: string) => void
  
  setFilters: (filters: Partial<TaskFilters>) => void
  clearFilters: () => void
  
  setConfig: (config: Partial<DashboardConfig>) => void
  updateConfig: (path: string, value: any) => void
  
  setLoading: (loading: boolean) => void
  addError: (error: DashboardError) => void
  removeError: (index: number) => void
  clearErrors: () => void
  
  updateRealtime: (realtime: Partial<RealtimeData>) => void
  
  // Computed getters
  getFilteredTasks: () => Task[]
  getActiveAccount: () => Account | undefined
  getAccountTasks: (accountId?: string) => Task[]
  getStats: () => {
    totalTasks: number
    completedTasks: number
    pendingTasks: number
    overdueTasks: number
    completionRate: number
  }
}

const defaultFilters: TaskFilters = {
  // Default to pending tasks for task management
  status: ['pending'],
  priority: [],
  project: [],
  tags: [],
  list: [],
  account_type: [],
  assignee: [],
  tasklist: [],
  search: '',
  sortBy: 'due',
  sortOrder: 'asc',
  includeDeleted: false,
  defaultPending: true,
  filter_logic: 'AND'
}

const defaultConfig: DashboardConfig = {
  general: {
    refreshInterval: 30000,
    autoRefresh: true,
    showCompleted: true,
    compactView: false,
    defaultView: 'dashboard'
  },
  notifications: {
    enabled: true,
    desktop: true,
    sound: false,
    overdue: true,
    dueSoon: true
  },
  appearance: {
    theme: 'system',
    accentColor: '#3b82f6',
    fontSize: 'medium',
    density: 'comfortable'
  },
  accounts: {
    autoSwitch: false,
    showAllAccounts: false,
    defaultAccount: ''
  }
}

export const useDashboardStore = create<DashboardState>()(
  devtools(
    persist(
      subscribeWithSelector(
        immer((set, get) => ({
          // Initial state
          tasks: [],
          accounts: [],
          activeAccount: null,
          filters: defaultFilters,
          config: defaultConfig,
          loading: false,
          errors: [],
          realtime: {
            connected: false,
            lastUpdate: new Date().toISOString(),
            activeUsers: 1,
            syncStatus: 'idle',
            pendingChanges: 0
          },

          // Task actions
          setTasks: (tasks) => set((state) => {
            state.tasks = tasks
          }),

          addTask: (task) => set((state) => {
            state.tasks.unshift(task)
          }),

          updateTask: (id, updates) => set((state) => {
            const taskIndex = state.tasks.findIndex(task => task.id === id)
            if (taskIndex !== -1) {
              Object.assign(state.tasks[taskIndex], updates)
            }
          }),

          deleteTask: (id) => set((state) => {
            state.tasks = state.tasks.filter(task => task.id !== id)
          }),

          // Account actions
          setAccounts: (accounts) => set((state) => {
            state.accounts = accounts
            // Set first account as active if none selected
            if (!state.activeAccount && accounts.length > 0) {
              state.activeAccount = accounts[0].id
            }
          }),

          addAccount: (account) => set((state) => {
            state.accounts.push(account)
            if (!state.activeAccount) {
              state.activeAccount = account.id
            }
          }),

          updateAccount: (id, updates) => set((state) => {
            const accountIndex = state.accounts.findIndex(account => account.id === id)
            if (accountIndex !== -1) {
              Object.assign(state.accounts[accountIndex], updates)
            }
          }),

          setActiveAccount: (accountId) => set((state) => {
            state.activeAccount = accountId
          }),

          // Filter actions
          setFilters: (newFilters) => set((state) => {
            Object.assign(state.filters, newFilters)
          }),

          clearFilters: () => set((state) => {
            state.filters = { ...defaultFilters }
          }),

          // Config actions
          setConfig: (newConfig) => set((state) => {
            Object.assign(state.config, newConfig)
          }),

          updateConfig: (path, value) => set((state) => {
            const keys = path.split('.')
            let current: any = state.config
            for (let i = 0; i < keys.length - 1; i++) {
              if (!current[keys[i]]) {
                current[keys[i]] = {}
              }
              current = current[keys[i]]
            }
            current[keys[keys.length - 1]] = value
          }),

          // Loading and error actions
          setLoading: (loading) => set((state) => {
            state.loading = loading
          }),

          addError: (error) => set((state) => {
            state.errors.push(error)
            // Auto-remove errors after 5 seconds for non-critical errors
            if (error.recoverable) {
              setTimeout(() => {
                set((state) => {
                  state.errors = state.errors.filter(e => e !== error)
                })
              }, 5000)
            }
          }),

          removeError: (index) => set((state) => {
            state.errors.splice(index, 1)
          }),

          clearErrors: () => set((state) => {
            state.errors = []
          }),

          // Real-time actions
          updateRealtime: (realtime) => set((state) => {
            Object.assign(state.realtime, realtime)
          }),

          // Computed getters
          getFilteredTasks: () => {
            const { tasks, filters, activeAccount } = get()
            
            return tasks.filter(task => {
              // Account filter
              if (activeAccount && task.tasklist_id !== activeAccount) {
                return false
              }
              
              // Status filter
              if (filters.status && filters.status.length > 0) {
                if (!filters.status.includes(task.status)) return false
              }
              
              // Priority filter
              if (filters.priority && filters.priority.length > 0) {
                if (!filters.priority.includes(task.priority)) return false
              }
              
              // Project filter
              if (filters.project && filters.project.length > 0) {
                if (!filters.project.includes(task.project || '')) return false
              }
              
              // Tags filter
              if (filters.tags && filters.tags.length > 0) {
                const hasMatchingTag = filters.tags.some(filterTag => 
                  task.tags.some(taskTag => taskTag.toLowerCase().includes(filterTag.toLowerCase()))
                )
                if (!hasMatchingTag) return false
              }
              
              // List filter
              if (filters.list && filters.list.length > 0) {
                if (!filters.list.includes(task.list_title || '')) return false
              }
              
              // Search filter
              if (filters.search) {
                const searchLower = filters.search.toLowerCase()
                const matchesTitle = task.title.toLowerCase().includes(searchLower)
                const matchesDescription = task.description?.toLowerCase().includes(searchLower)
                const matchesNotes = task.notes?.toLowerCase().includes(searchLower)
                const matchesTags = task.tags.some(tag => tag.toLowerCase().includes(searchLower))
                
                if (!matchesTitle && !matchesDescription && !matchesNotes && !matchesTags) {
                  return false
                }
              }
              
              return true
            }).sort((a, b) => {
              // Apply sorting
              let comparison = 0
              
              switch (filters.sortBy) {
                case 'due':
                  if (!a.due && !b.due) comparison = 0
                  else if (!a.due) comparison = 1
                  else if (!b.due) comparison = -1
                  else comparison = new Date(a.due).getTime() - new Date(b.due).getTime()
                  break
                case 'priority':
                  const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 }
                  comparison = (priorityOrder[b.priority] || 0) - (priorityOrder[a.priority] || 0)
                  break
                case 'created':
                  comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
                  break
                case 'modified':
                  comparison = new Date(a.modified_at).getTime() - new Date(b.modified_at).getTime()
                  break
                case 'title':
                  comparison = a.title.localeCompare(b.title)
                  break
                default:
                  comparison = 0
              }
              
              return filters.sortOrder === 'desc' ? -comparison : comparison
            })
          },

          getActiveAccount: () => {
            const { accounts, activeAccount } = get()
            return accounts.find(account => account.id === activeAccount)
          },

          getAccountTasks: (accountId) => {
            const { tasks } = get()
            const targetAccountId = accountId || get().activeAccount
            if (!targetAccountId) return []
            
            return tasks.filter(task => task.tasklist_id === targetAccountId)
          },

          getStats: () => {
            const tasks = get().getFilteredTasks()
            const totalTasks = tasks.length
            const completedTasks = tasks.filter(task => task.status === TaskStatus.COMPLETED).length
            const pendingTasks = tasks.filter(task => task.status === TaskStatus.PENDING).length
            const overdueTasks = tasks.filter(task => {
              return task.due && new Date(task.due) < new Date() && task.status !== TaskStatus.COMPLETED
            }).length
            
            const completionRate = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0
            
            return {
              totalTasks,
              completedTasks,
              pendingTasks,
              overdueTasks,
              completionRate
            }
          }
        }))
      ),
      {
        name: 'gtasks-dashboard',
        partialize: (state) => ({
          config: state.config,
          filters: state.filters,
          activeAccount: state.activeAccount
        })
      }
    )
  )
)

// Selector hooks for better performance
export const useTasks = () => useDashboardStore(state => state.tasks)
export const useAccounts = () => useDashboardStore(state => state.accounts)
export const useActiveAccount = () => useDashboardStore(state => state.getActiveAccount())
export const useFilters = () => useDashboardStore(state => state.filters)
export const useConfig = () => useDashboardStore(state => state.config)
export const useStats = () => useDashboardStore(state => state.getStats())
export const useFilteredTasks = () => useDashboardStore(state => state.getFilteredTasks())
export const useRealtime = () => useDashboardStore(state => state.realtime)
export const useErrors = () => useDashboardStore(state => state.errors)
export const useLoading = () => useDashboardStore(state => state.loading)