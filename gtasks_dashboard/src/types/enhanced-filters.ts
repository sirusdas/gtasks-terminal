/**
 * Enhanced Task Filters with Multiselect and Date Range Support
 * This file extends the existing TaskFilters interface with comprehensive filtering capabilities
 */

import { TaskStatus, Priority } from './index'

// Date Range Interface for comprehensive date filtering
export interface DateRange {
  start?: string  // ISO date string
  end?: string    // ISO date string
  type?: 'today' | 'yesterday' | 'thisWeek' | 'lastWeek' | 'thisMonth' | 'lastMonth' | 'thisQuarter' | 'custom'
}

// Enhanced Task Filters Interface
export interface EnhancedTaskFilters {
  // Core multiselect filters
  status?: TaskStatus[]
  priority?: Priority[]
  project?: string[]
  tags?: string[]
  list?: string[]
  account_type?: string[]
  assignee?: string[]
  tasklist?: string[]
  
  // Comprehensive date range filtering
  created_date_range?: DateRange
  due_date_range?: DateRange
  modified_date_range?: DateRange
  dueDate?: {
    from?: string
    to?: string
    type?: 'overdue' | 'today' | 'thisWeek' | 'thisMonth' | 'custom'
  }
  
  // Search and sorting
  search?: string
  sortBy?: 'due' | 'priority' | 'created' | 'modified' | 'title'
  sortOrder?: 'asc' | 'desc'
  
  // Advanced filtering options
  filter_logic?: 'AND' | 'OR'
  includeDeleted?: boolean
  defaultPending?: boolean  // Flag to apply default pending filter
}

// Multiselect Filter Option
export interface FilterOption {
  value: string
  label: string
  count?: number
  color?: string
  icon?: string
}

// Multiselect Filter Component Props
export interface MultiselectFilterProps {
  options: FilterOption[]
  selected: string[]
  onChange: (selected: string[]) => void
  placeholder?: string
  searchPlaceholder?: string
  maxHeight?: number
  showSearch?: boolean
  allowClear?: boolean
  disabled?: boolean
  loading?: boolean
}

// Date Range Filter Component Props
export interface DateRangeFilterProps {
  value?: DateRange
  onChange: (range: DateRange | undefined) => void
  presets?: Array<{
    label: string
    type: DateRange['type']
    getValue: () => DateRange
  }>
  placeholder?: string
  disabled?: boolean
}

// Active Filter Display
export interface ActiveFilter {
  id: string
  type: 'status' | 'priority' | 'project' | 'tags' | 'list' | 'account_type' | 'assignee' | 'tasklist' | 'date_range'
  label: string
  value: string | DateRange
  remove: () => void
}

// Filter Panel State
export interface FilterPanelState {
  expanded: {
    status: boolean
    priority: boolean
    project: boolean
    tags: boolean
    dates: boolean
    advanced: boolean
  }
  searchTerm: string
  showDeleted: boolean
}

// Quick Date Presets
export const DATE_RANGE_PRESETS = {
  today: {
    label: 'Today',
    type: 'today' as const,
    getValue: (): DateRange => {
      const today = new Date()
      return {
        start: today.toISOString().split('T')[0],
        end: today.toISOString().split('T')[0],
        type: 'today'
      }
    }
  },
  yesterday: {
    label: 'Yesterday',
    type: 'yesterday' as const,
    getValue: (): DateRange => {
      const yesterday = new Date()
      yesterday.setDate(yesterday.getDate() - 1)
      return {
        start: yesterday.toISOString().split('T')[0],
        end: yesterday.toISOString().split('T')[0],
        type: 'yesterday'
      }
    }
  },
  thisWeek: {
    label: 'This Week',
    type: 'thisWeek' as const,
    getValue: (): DateRange => {
      const now = new Date()
      const startOfWeek = new Date(now.setDate(now.getDate() - now.getDay()))
      const endOfWeek = new Date(now.setDate(now.getDate() - now.getDay() + 6))
      return {
        start: startOfWeek.toISOString().split('T')[0],
        end: endOfWeek.toISOString().split('T')[0],
        type: 'thisWeek'
      }
    }
  },
  lastWeek: {
    label: 'Last Week',
    type: 'lastWeek' as const,
    getValue: (): DateRange => {
      const now = new Date()
      const startOfLastWeek = new Date(now.setDate(now.getDate() - now.getDay() - 7))
      const endOfLastWeek = new Date(now.setDate(now.getDate() - now.getDay() - 1))
      return {
        start: startOfLastWeek.toISOString().split('T')[0],
        end: endOfLastWeek.toISOString().split('T')[0],
        type: 'lastWeek'
      }
    }
  },
  thisMonth: {
    label: 'This Month',
    type: 'thisMonth' as const,
    getValue: (): DateRange => {
      const now = new Date()
      const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1)
      const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0)
      return {
        start: startOfMonth.toISOString().split('T')[0],
        end: endOfMonth.toISOString().split('T')[0],
        type: 'thisMonth'
      }
    }
  },
  lastMonth: {
    label: 'Last Month',
    type: 'lastMonth' as const,
    getValue: (): DateRange => {
      const now = new Date()
      const startOfLastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1)
      const endOfLastMonth = new Date(now.getFullYear(), now.getMonth(), 0)
      return {
        start: startOfLastMonth.toISOString().split('T')[0],
        end: endOfLastMonth.toISOString().split('T')[0],
        type: 'lastMonth'
      }
    }
  },
  thisQuarter: {
    label: 'This Quarter',
    type: 'thisQuarter' as const,
    getValue: (): DateRange => {
      const now = new Date()
      const quarter = Math.floor(now.getMonth() / 3)
      const startOfQuarter = new Date(now.getFullYear(), quarter * 3, 1)
      const endOfQuarter = new Date(now.getFullYear(), quarter * 3 + 3, 0)
      return {
        start: startOfQuarter.toISOString().split('T')[0],
        end: endOfQuarter.toISOString().split('T')[0],
        type: 'thisQuarter'
      }
    }
  }
}

// Filter Configuration
export interface FilterConfig {
  // Default filter behavior
  applyDefaultPending: boolean
  defaultPendingStatus: TaskStatus[]
  
  // UI Configuration
  showSearchInDropdowns: boolean
  dropdownSearchThreshold: number  // Show search when options exceed this count
  maxHeightDropdown: number
  
  // Performance Configuration
  debounceMs: number
  virtualScrollThreshold: number
  
  // Filter Logic
  defaultFilterLogic: 'AND' | 'OR'
  allowMixedLogic: boolean
}

// Default filter configuration
export const DEFAULT_FILTER_CONFIG: FilterConfig = {
  applyDefaultPending: true,
  defaultPendingStatus: [TaskStatus.PENDING],
  showSearchInDropdowns: true,
  dropdownSearchThreshold: 10,
  maxHeightDropdown: 300,
  debounceMs: 300,
  virtualScrollThreshold: 100,
  defaultFilterLogic: 'AND',
  allowMixedLogic: true
}