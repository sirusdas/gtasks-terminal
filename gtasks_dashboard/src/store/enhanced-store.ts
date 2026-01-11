/**
 * Enhanced Task Management Store with Multiselect Filters and Date Range Support
 * This store extends the existing dashboard store with comprehensive filtering capabilities
 */

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
  DashboardError,
  TaskStatus,
  Priority
} from '@/types'
import { 
  EnhancedTaskFilters, 
  DateRange, 
  FilterConfig, 
  DEFAULT_FILTER_CONFIG,
  DATE_RANGE_PRESETS,
  ActiveFilter 
} from '@/types/enhanced-filters'

interface EnhancedDashboardState {
  // Data
  tasks: Task[]
  accounts: Account[]
  activeAccount: string | null
  
  // Enhanced UI State
  filters: EnhancedTaskFilters
  config: DashboardConfig
  loading: boolean
  errors: DashboardError[]
  
  // Real-time
  realtime: RealtimeData
  
  // Filter configuration
  filterConfig: FilterConfig
  
  // Enhanced Actions
  setTasks: (tasks: Task[]) => void
  addTask: (task: Task) => void
  updateTask: (id: string, updates: Partial<Task>) => void
  deleteTask: (id: string) => void
  
  setAccounts: (accounts: Account[]) => void
  addAccount: (account: Account) => void
  updateAccount: (id: string, updates: Partial<Account>) => void
  setActiveAccount: (accountId: string) => void
  
  // Enhanced filter actions
  setFilters: (filters: Partial<EnhancedTaskFilters>) => void
  clearFilters: () => void
  resetToDefaultPending: () => void
  addStatusFilter: (status: TaskStatus) => void
  removeStatusFilter: (status: TaskStatus) => void
  addPriorityFilter: (priority: Priority) => void
  removePriorityFilter: (priority: Priority) => void
  addProjectFilter: (project: string) => void
  removeProjectFilter: (project: string) => void
  addTagFilter: (tag: string) => void
  removeTagFilter: (tag: string) => void
  setDateRange: (field: 'created_date_range' | 'due_date_range' | 'modified_date_range', range?: DateRange) => void
  clearDateRange: (field: 'created_date_range' | 'due_date_range' | 'modified_date_range') => void
  
  // Filter management
  getActiveFilters: () => ActiveFilter[]
  applyQuickDatePreset: (preset: keyof typeof DATE_RANGE_PRESETS) => void
  toggleFilterLogic: () => void
  
  setConfig: (config: Partial<DashboardConfig>) => void
  updateConfig: (path: string, value: any) => void
  
  setLoading: (loading: boolean) => void
  addError: (error: DashboardError) => void
  removeError: (index: number) => void
  clearErrors: () => void
  
  updateRealtime: (realtime: Partial<RealtimeData>) => void
  
  // Enhanced computed getters
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
  getFilterOptions: () => {
    status: { value: string; label: string; count: number }[]
    priority: { value: string; label: string; count: number }[]
    projects: { value: string; label: string; count: number }[]
    tags: { value: string; label: string; count: number }[]
    accounts: { value: string; label: string; count: number }[]
  }
}

// Helper function to check if date falls within range
const isDateInRange = (date: string, range?: DateRange): boolean => {
  if (!range || (!range.start && !range.end)) return true
  
  const taskDate = new Date(date)
  const start = range.start ? new Date(range.start) : null
  const end = range.end ? new Date(range.end) : null
  
  if (start && taskDate < start) return false
  if (end && taskDate > end) return false
  
  return true
}

// Default enhanced filters with pending status
const getDefaultEnhancedFilters = (): EnhancedTaskFilters => ({
  // Default to pending tasks for task management
  status: [TaskStatus.PENDING],
  priority: [],
  project: [],
  tags: [],
  list: [],
  account_type: [],
  assignee: [],
  tasklist: [],
  created_date_range: undefined,
  due_date_range: undefined,
  modified_date_range: undefined,
  search: '',
  sortBy: 'due',
  sortOrder: 'asc',
  includeDeleted: false,
  defaultPending: true,
  filter_logic: 'AND'
})

export const useEnhancedDashboardStore = create<EnhancedDashboardState>()(
  devtools(
    persist(
      subscribeWithSelector(
        immer((set, get) => ({
          // Initial state
          tasks: [],
          accounts: [],
          activeAccount: null,
          filters: getDefaultEnhancedFilters(),
          config: {
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
          },
          loading: false,
          errors: [],
          realtime: {
            connected: false,
            lastUpdate: new Date().toISOString(),
            activeUsers: 1,
            syncStatus: 'idle',
            pendingChanges: 0
          },
          filterConfig: DEFAULT_FILTER_CONFIG,

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

          // Enhanced filter actions
          setFilters: (newFilters) => set((state) => {
            Object.assign(state.filters, newFilters)
          }),

          clearFilters: () => set((state) => {
            state.filters = getDefaultEnhancedFilters()
          }),

          resetToDefaultPending: () => set((state) => {
            state.filters.status = [TaskStatus.PENDING]
            state.filters.defaultPending = true
          }),

          addStatusFilter: (status) => set((state) => {
            if (!state.filters.status?.includes(status)) {
              state.filters.status = [...(state.filters.status || []), status]
            }
          }),

          removeStatusFilter: (status) => set((state) => {
            state.filters.status = state.filters.status?.filter(s => s !== status) || []
          }),

          addPriorityFilter: (priority) => set((state) => {
            if (!state.filters.priority?.includes(priority)) {
              state.filters.priority = [...(state.filters.priority || []), priority]
            }
          }),

          removePriorityFilter: (priority) => set((state) => {
            state.filters.priority = state.filters.priority?.filter(p => p !== priority) || []
          }),

          addProjectFilter: (project) => set((state) => {
            if (!state.filters.project?.includes(project)) {
              state.filters.project = [...(state.filters.project || []), project]
            }
          }),

          removeProjectFilter: (project) => set((state) => {
            state.filters.project = state.filters.project?.filter(p => p !== project) || []
          }),

          addTagFilter: (tag) => set((state) => {
            if (!state.filters.tags?.includes(tag)) {
              state.filters.tags = [...(state.filters.tags || []), tag]
            }
          }),

          removeTagFilter: (tag) => set((state) => {
            state.filters.tags = state.filters.tags?.filter(t => t !== tag) || []
          }),

          setDateRange: (field, range) => set((state) => {
            state.filters[field] = range
          }),

          clearDateRange: (field) => set((state) => {
            state.filters[field] = undefined
          }),

          getActiveFilters: () => {
            const { filters } = get()
            const activeFilters: ActiveFilter[] = []

            // Status filters
            if (filters.status?.length) {
              filters.status.forEach(status => {
                activeFilters.push({
                  id: `status-${status}`,
                  type: 'status',
                  label: `Status: ${status}`,
                  value: status,
                  remove: () => get().removeStatusFilter(status)
                })
              })
            }

            // Priority filters
            if (filters.priority?.length) {
              filters.priority.forEach(priority => {
                activeFilters.push({
                  id: `priority-${priority}`,
                  type: 'priority',
                  label: `Priority: ${priority}`,
                  value: priority,
                  remove: () => get().removePriorityFilter(priority)
                })
              })
            }

            // Date range filters
            if (filters.created_date_range) {
              activeFilters.push({
                id: 'created-date-range',
                type: 'date_range',
                label: `Created: ${filters.created_date_range.start || 'Any'} to ${filters.created_date_range.end || 'Any'}`,
                value: filters.created_date_range,
                remove: () => get().clearDateRange('created_date_range')
              })
            }

            if (filters.due_date_range) {
              activeFilters.push({
                id: 'due-date-range',
                type: 'date_range',
                label: `Due: ${filters.due_date_range.start || 'Any'} to ${filters.due_date_range.end || 'Any'}`,
                value: filters.due_date_range,
                remove: () => get().clearDateRange('due_date_range')
              })
            }

            return activeFilters
          },

          applyQuickDatePreset: (presetKey) => {
            const preset = DATE_RANGE_PRESETS[presetKey]
            if (preset) {
              get().setDateRange('created_date_range', preset.getValue())
            }
          },

          toggleFilterLogic: () => set((state) => {
            state.filters.filter_logic = state.filters.filter_logic === 'AND' ? 'OR' : 'AND'
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

          // Enhanced computed getters
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

              // Account type filter (if available)
              if (filters.account_type && filters.account_type.length > 0) {
                const accountType = task.account_type || 'default'
                if (!filters.account_type.includes(accountType)) return false
              }

              // Assignee filter (if available)
              if (filters.assignee && filters.assignee.length > 0) {
                const assignee = task.assignee || 'unassigned'
                if (!filters.assignee.includes(assignee)) return false
              }

              // Enhanced date range filters
              if (filters.created_date_range) {
                if (!isDateInRange(task.created_at, filters.created_date_range)) return false
              }

              if (filters.due_date_range) {
                if (task.due && !isDateInRange(task.due, filters.due_date_range)) return false
              }

              if (filters.modified_date_range) {
                if (!isDateInRange(task.modified_at, filters.modified_date_range)) return false
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
                  const priorityOrder = { [Priority.CRITICAL]: 4, [Priority.HIGH]: 3, [Priority.MEDIUM]: 2, [Priority.LOW]: 1 }
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
          },

          getFilterOptions: () => {
            const { tasks } = get()
            
            // Calculate options with counts
            const statusOptions = Object.values(TaskStatus).map(status => ({
              value: status,
              label: status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' '),
              count: tasks.filter(task => task.status === status).length
            }))

            const priorityOptions = Object.values(Priority).map(priority => ({
              value: priority,
              label: priority.charAt(0).toUpperCase() + priority.slice(1),
              count: tasks.filter(task => task.priority === priority).length
            }))

            const projectMap = new Map<string, number>()
            tasks.forEach(task => {
              const project = task.project || 'Unassigned'
              projectMap.set(project, (projectMap.get(project) || 0) + 1)
            })

            const projectOptions = Array.from(projectMap.entries()).map(([project, count]) => ({
              value: project,
              label: project,
              count
            }))

            const tagMap = new Map<string, number>()
            tasks.forEach(task => {
              task.tags.forEach(tag => {
                tagMap.set(tag, (tagMap.get(tag) || 0) + 1)
              })
            })

            const tagOptions = Array.from(tagMap.entries()).map(([tag, count]) => ({
              value: tag,
              label: tag,
              count
            }))

            const accountMap = new Map<string, number>()
            tasks.forEach(task => {
              const account = task.account_type || 'default'
              accountMap.set(account, (accountMap.get(account) || 0) + 1)
            })

            const accountOptions = Array.from(accountMap.entries()).map(([account, count]) => ({
              value: account,
              label: account,
              count
            }))

            return {
              status: statusOptions,
              priority: priorityOptions,
              projects: projectOptions,
              tags: tagOptions,
              accounts: accountOptions
            }
          }
        }))
      ),
      {
        name: 'gtasks-enhanced-dashboard',
        partialize: (state) => ({
          config: state.config,
          filters: state.filters,
          activeAccount: state.activeAccount,
          filterConfig: state.filterConfig
        })
      }
    )
  )
)

// Enhanced selector hooks
export const useEnhancedTasks = () => useEnhancedDashboardStore(state => state.tasks)
export const useEnhancedAccounts = () => useEnhancedDashboardStore(state => state.accounts)
export const useEnhancedActiveAccount = () => useEnhancedDashboardStore(state => state.getActiveAccount())
export const useEnhancedFilters = () => useEnhancedDashboardStore(state => state.filters)
export const useEnhancedConfig = () => useEnhancedDashboardStore(state => state.config)
export const useEnhancedStats = () => useEnhancedDashboardStore(state => state.getStats())
export const useEnhancedFilteredTasks = () => useEnhancedDashboardStore(state => state.getFilteredTasks())
export const useEnhancedActiveFilters = () => useEnhancedDashboardStore(state => state.getActiveFilters())
export const useEnhancedFilterOptions = () => useEnhancedDashboardStore(state => state.getFilterOptions())
export const useEnhancedRealtime = () => useEnhancedDashboardStore(state => state.realtime)
export const useEnhancedErrors = () => useEnhancedDashboardStore(state => state.errors)
export const useEnhancedLoading = () => useEnhancedDashboardStore(state => state.loading)