/**
 * Enhanced Task Filters for "Tasks Due Today" Dashboard Section
 * This file extends the enhanced filters with specific "due today" functionality
 */

import { EnhancedTaskFilters } from './enhanced-filters'

// Extended filters for "Tasks Due Today" functionality
export interface DueTodayTaskFilters extends EnhancedTaskFilters {
  // Specific "due today" configuration
  due_today_only: boolean  // Always true for this widget
  include_overdue: boolean  // Option to include overdue tasks
  group_by_time: boolean    // Group tasks by due time periods
  
  // Time-based grouping options
  timeGrouping?: {
    enabled: boolean
    intervals: 'hour' | 'morning' | 'afternoon' | 'evening' | 'custom'
    customIntervals?: Array<{
      label: string
      start: string  // HH:mm format
      end: string    // HH:mm format
    }>
  }
  
  // Real-time update configuration
  realtime?: {
    enabled: boolean
    refreshInterval: number  // milliseconds
    midnightRefresh: boolean  // Refresh at midnight for new "due today" tasks
  }
}

// Task grouping for "due today" display
export interface DueTodayTaskGroup {
  timeSlot: string
  label: string
  tasks: DueTodayTask[]
  count: number
}

// Extended task interface for due today display
export interface DueTodayTask {
  id: string
  title: string
  description?: string
  status: string
  priority: string
  due?: string
  dueTime?: string
  list_title?: string
  tags: string[]
  project?: string
  account_type?: string
  assignee?: string
  completed_at?: string
  created_at: string
  modified_at: string
  
  // Additional fields for dashboard display
  isOverdue: boolean
  isDueNow: boolean
  timeUntilDue?: string
  priorityColor: string
  statusIcon: string
}

// Time zone configuration
export interface TimezoneConfig {
  timezone: string
  useLocalTimezone: boolean
  format: '12h' | '24h'
  showSeconds: boolean
}

// Quick date presets specifically for due today
export const DUE_TODAY_QUICK_PRESETS = {
  today: {
    label: 'Today',
    type: 'today' as const,
    getValue: () => {
      const today = new Date()
      return {
        start: today.toISOString().split('T')[0],
        end: today.toISOString().split('T')[0],
        type: 'today'
      }
    }
  },
  overdue: {
    label: 'Overdue',
    type: 'overdue' as const,
    getValue: () => {
      const yesterday = new Date()
      yesterday.setDate(yesterday.getDate() - 1)
      return {
        start: undefined,
        end: yesterday.toISOString().split('T')[0],
        type: 'overdue'
      }
    }
  },
  thisWeek: {
    label: 'This Week',
    type: 'thisWeek' as const,
    getValue: () => {
      const now = new Date()
      const startOfWeek = new Date(now.setDate(now.getDate() - now.getDay()))
      const endOfWeek = new Date(now.setDate(now.getDate() - now.getDay() + 6))
      return {
        start: startOfWeek.toISOString().split('T')[0],
        end: endOfWeek.toISOString().split('T')[0],
        type: 'thisWeek'
      }
    }
  }
}

// Time grouping presets
export const TIME_GROUPING_PRESETS = {
  hour: {
    label: 'By Hour',
    intervals: 'hour' as const,
    description: 'Group tasks by specific hour'
  },
  morning: {
    label: 'Morning/Afternoon/Evening',
    intervals: 'morning' as const,
    description: 'Group by time periods: 6AM-12PM, 12PM-6PM, 6PM-12AM'
  },
  afternoon: {
    label: 'Business Hours',
    intervals: 'afternoon' as const,
    description: 'Group by business hours: 9AM-5PM vs Outside hours'
  },
  evening: {
    label: 'Work/Personal',
    intervals: 'evening' as const,
    description: 'Group by task type: Work vs Personal tasks'
  }
}

// Default configuration for due today widget
export const DEFAULT_DUE_TODAY_CONFIG: DueTodayTaskFilters = {
  due_today_only: true,
  include_overdue: false,
  group_by_time: true,
  timeGrouping: {
    enabled: true,
    intervals: 'morning',
    customIntervals: []
  },
  realtime: {
    enabled: true,
    refreshInterval: 30000, // 30 seconds
    midnightRefresh: true
  },
  status: [],
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
  defaultPending: false,  // Don't default to pending for due today
  filter_logic: 'AND'
}

// Widget state interface
export interface DueTodayWidgetState {
  expanded: boolean
  filtersVisible: boolean
  selectedTasks: string[]
  viewMode: 'list' | 'cards' | 'timeline'
  sortBy: 'due' | 'priority' | 'created' | 'title'
  sortOrder: 'asc' | 'desc'
  showFilters: boolean
  lastRefresh: Date
  isLoading: boolean
  error?: string
}

// Export utility functions
export interface DueTodayUtils {
  // Time calculations
  isDueToday: (dueDate: string, timezone?: string) => boolean
  isOverdue: (dueDate: string) => boolean
  getTimeUntilDue: (dueDate: string) => string
  getDueTimeGroup: (dueDate: string, groupingType: string) => string
  
  // Task processing
  processTasksForDueToday: (tasks: any[], filters: DueTodayTaskFilters) => DueTodayTask[]
  groupTasksByTime: (tasks: DueTodayTask[], groupingType: string) => DueTodayTaskGroup[]
  
  // Real-time utilities
  getTimeUntilMidnight: () => number
  shouldRefreshForMidnight: (lastRefresh: Date) => boolean
}