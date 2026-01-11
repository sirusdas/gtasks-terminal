/**
 * Due Today Utilities - Helper functions for "Tasks Due Today" functionality
 * Handles timezone calculations, task processing, and real-time updates
 */

import type { 
  DueTodayTask, 
  DueTodayTaskGroup, 
  DueTodayTaskFilters,
  TimezoneConfig 
} from '@/types/due-today-filters'

// Default timezone configuration
const DEFAULT_TIMEZONE_CONFIG: TimezoneConfig = {
  timezone: 'UTC',
  useLocalTimezone: true,
  format: '24h',
  showSeconds: false
}

/**
 * Check if a task is due today
 */
export const isDueToday = (dueDate: string, timezone?: string): boolean => {
  if (!dueDate) return false
  
  const taskDate = new Date(dueDate)
  const now = timezone ? new Date(new Date().toLocaleString("en-US", {timeZone: timezone})) : new Date()
  
  // Get date components in the target timezone
  const taskDateStr = taskDate.toLocaleDateString('en-CA', { 
    timeZone: timezone || Intl.DateTimeFormat().resolvedOptions().timeZone 
  })
  const todayStr = now.toLocaleDateString('en-CA', { 
    timeZone: timezone || Intl.DateTimeFormat().resolvedOptions().timeZone 
  })
  
  return taskDateStr === todayStr
}

/**
 * Check if a task is overdue
 */
export const isOverdue = (dueDate: string): boolean => {
  if (!dueDate) return false
  
  const taskDate = new Date(dueDate)
  const now = new Date()
  
  return taskDate < now
}

/**
 * Calculate time until task is due
 */
export const getTimeUntilDue = (dueDate: string): string => {
  if (!dueDate) return 'No due date'
  
  const taskDate = new Date(dueDate)
  const now = new Date()
  const diffMs = taskDate.getTime() - now.getTime()
  
  if (diffMs <= 0) {
    const overdueMs = Math.abs(diffMs)
    const overdueMinutes = Math.floor(overdueMs / (1000 * 60))
    const overdueHours = Math.floor(overdueMinutes / 60)
    const overdueDays = Math.floor(overdueHours / 24)
    
    if (overdueDays > 0) {
      return `Overdue by ${overdueDays} day${overdueDays > 1 ? 's' : ''}`
    } else if (overdueHours > 0) {
      return `Overdue by ${overdueHours} hour${overdueHours > 1 ? 's' : ''}`
    } else {
      return `Overdue by ${overdueMinutes} minute${overdueMinutes > 1 ? 's' : ''}`
    }
  }
  
  const minutes = Math.floor(diffMs / (1000 * 60))
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (days > 0) {
    return `Due in ${days} day${days > 1 ? 's' : ''}`
  } else if (hours > 0) {
    return `Due in ${hours} hour${hours > 1 ? 's' : ''}`
  } else if (minutes > 0) {
    return `Due in ${minutes} minute${minutes > 1 ? 's' : ''}`
  } else {
    return 'Due now'
  }
}

/**
 * Get due time group for task based on grouping type
 */
export const getDueTimeGroup = (dueDate: string, groupingType: string): string => {
  if (!dueDate) return 'No Due Time'
  
  const taskDate = new Date(dueDate)
  const hour = taskDate.getHours()
  
  switch (groupingType) {
    case 'hour':
      return `${hour.toString().padStart(2, '0')}:00`
    
    case 'morning':
      if (hour >= 6 && hour < 12) return 'Morning (6AM-12PM)'
      if (hour >= 12 && hour < 18) return 'Afternoon (12PM-6PM)'
      if (hour >= 18 || hour < 6) return 'Evening (6PM-6AM)'
      return 'No Time Set'
    
    case 'afternoon':
      if (hour >= 9 && hour < 17) return 'Business Hours (9AM-5PM)'
      return 'Outside Business Hours'
    
    case 'evening':
      return 'Work Time' // This would need task data to determine properly
    
    default:
      return 'Due Today'
  }
}

/**
 * Process tasks for due today display
 */
export const processTasksForDueToday = (
  tasks: any[], 
  filters: DueTodayTaskFilters
): DueTodayTask[] => {
  const processedTasks: DueTodayTask[] = []
  
  for (const task of tasks) {
    // Apply base filters first
    if (!passesBaseFilters(task, filters)) continue
    
    // Check due today constraint
    const dueToday = isDueToday(task.due, filters.realtime?.enabled ? DEFAULT_TIMEZONE_CONFIG.timezone : undefined)
    const overdue = isOverdue(task.due)
    
    // Skip if not due today (unless including overdue)
    if (!dueToday && !(filters.include_overdue && overdue)) continue
    
    // Process task for display
    const processedTask: DueTodayTask = {
      ...task,
      isOverdue: overdue,
      isDueNow: dueToday && task.due && new Date(task.due) <= new Date(),
      timeUntilDue: getTimeUntilDue(task.due),
      priorityColor: getPriorityColor(task.priority),
      statusIcon: getStatusIcon(task.status)
    }
    
    processedTasks.push(processedTask)
  }
  
  // Sort tasks
  const sortBy = filters.sortBy || 'due'
  const sortOrder = filters.sortOrder || 'asc'
  return sortDueTodayTasks(processedTasks, sortBy, sortOrder)
}

/**
 * Group tasks by time periods
 */
export const groupTasksByTime = (
  tasks: DueTodayTask[], 
  groupingType: string
): DueTodayTaskGroup[] => {
  if (!groupingType || groupingType === 'none') {
    return [{
      timeSlot: 'all',
      label: 'All Tasks Due Today',
      tasks: tasks,
      count: tasks.length
    }]
  }
  
  const groups: { [key: string]: DueTodayTask[] } = {}
  
  for (const task of tasks) {
    const timeGroup = getDueTimeGroup(task.due || '', groupingType)
    
    if (!groups[timeGroup]) {
      groups[timeGroup] = []
    }
    groups[timeGroup].push(task)
  }
  
  // Convert to array format and sort by time
  return Object.entries(groups)
    .map(([timeSlot, tasks]) => ({
      timeSlot,
      label: timeSlot,
      tasks: tasks.sort((a, b) => {
        if (!a.due && !b.due) return 0
        if (!a.due) return 1
        if (!b.due) return -1
        return new Date(a.due).getTime() - new Date(b.due).getTime()
      }),
      count: tasks.length
    }))
    .sort((a, b) => {
      // Sort time groups chronologically
      const timeOrder = getTimeGroupOrder()
      return (timeOrder[a.timeSlot] || 999) - (timeOrder[b.timeSlot] || 999)
    })
}

/**
 * Calculate time until midnight for refresh scheduling
 */
export const getTimeUntilMidnight = (): number => {
  const now = new Date()
  const midnight = new Date()
  midnight.setHours(24, 0, 0, 0) // Next midnight
  
  return midnight.getTime() - now.getTime()
}

/**
 * Check if we should refresh for midnight rollover
 */
export const shouldRefreshForMidnight = (lastRefresh: Date): boolean => {
  const now = new Date()
  const lastRefreshDate = new Date(lastRefresh)
  
  // Refresh if last refresh was before today
  const today = now.toDateString()
  const lastRefreshDay = lastRefreshDate.toDateString()
  
  return today !== lastRefreshDay
}

/**
 * Get priority color for task display
 */
const getPriorityColor = (priority: string): string => {
  switch (priority?.toLowerCase()) {
    case 'critical':
      return 'text-red-600 bg-red-100'
    case 'high':
      return 'text-orange-600 bg-orange-100'
    case 'medium':
      return 'text-yellow-600 bg-yellow-100'
    case 'low':
      return 'text-green-600 bg-green-100'
    default:
      return 'text-gray-600 bg-gray-100'
  }
}

/**
 * Get status icon for task display
 */
const getStatusIcon = (status: string): string => {
  switch (status?.toLowerCase()) {
    case 'completed':
      return '✓'
    case 'in_progress':
      return '⟳'
    case 'pending':
      return '○'
    case 'cancelled':
      return '✗'
    default:
      return '○'
  }
}

/**
 * Time group ordering for chronological sorting
 */
const getTimeGroupOrder = (): { [key: string]: number } => {
  return {
    'Morning (6AM-12PM)': 1,
    'Afternoon (12PM-6PM)': 2,
    'Evening (6PM-6AM)': 3,
    'Business Hours (9AM-5PM)': 1,
    'Outside Business Hours': 2,
    'No Due Time': 4,
    'No Time Set': 4,
    '00:00': 0,
    '01:00': 1,
    '02:00': 2,
    '03:00': 3,
    '04:00': 4,
    '05:00': 5,
    '06:00': 6,
    '07:00': 7,
    '08:00': 8,
    '09:00': 9,
    '10:00': 10,
    '11:00': 11,
    '12:00': 12,
    '13:00': 13,
    '14:00': 14,
    '15:00': 15,
    '16:00': 16,
    '17:00': 17,
    '18:00': 18,
    '19:00': 19,
    '20:00': 20,
    '21:00': 21,
    '22:00': 22,
    '23:00': 23
  }
}

/**
 * Apply base filters to task
 */
const passesBaseFilters = (task: any, filters: DueTodayTaskFilters): boolean => {
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
      task.tags.some((taskTag: string) => taskTag.toLowerCase().includes(filterTag.toLowerCase()))
    )
    if (!hasMatchingTag) return false
  }
  
  // List filter
  if (filters.list && filters.list.length > 0) {
    if (!filters.list.includes(task.list_title || '')) return false
  }
  
  // Account type filter
  if (filters.account_type && filters.account_type.length > 0) {
    const accountType = task.account_type || 'default'
    if (!filters.account_type.includes(accountType)) return false
  }
  
  // Search filter
  if (filters.search) {
    const searchLower = filters.search.toLowerCase()
    const matchesTitle = task.title.toLowerCase().includes(searchLower)
    const matchesDescription = task.description?.toLowerCase().includes(searchLower)
    const matchesNotes = task.notes?.toLowerCase().includes(searchLower)
    const matchesTags = task.tags.some((tag: string) => tag.toLowerCase().includes(searchLower))
    
    if (!matchesTitle && !matchesDescription && !matchesNotes && !matchesTags) {
      return false
    }
  }
  
  return true
}

/**
 * Sort due today tasks
 */
const sortDueTodayTasks = (
  tasks: DueTodayTask[], 
  sortBy: string, 
  sortOrder: 'asc' | 'desc'
): DueTodayTask[] => {
  return [...tasks].sort((a, b) => {
    let comparison = 0
    
    switch (sortBy) {
      case 'due':
        if (!a.due && !b.due) comparison = 0
        else if (!a.due) comparison = 1
        else if (!b.due) comparison = -1
        else comparison = new Date(a.due).getTime() - new Date(b.due).getTime()
        break
      
      case 'priority':
        const priorityOrder = { 'critical': 4, 'high': 3, 'medium': 2, 'low': 1 }
        comparison = (priorityOrder[b.priority as keyof typeof priorityOrder] || 0) - 
                   (priorityOrder[a.priority as keyof typeof priorityOrder] || 0)
        break
      
      case 'created':
        comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        break
      
      case 'title':
        comparison = a.title.localeCompare(b.title)
        break
      
      default:
        comparison = 0
    }
    
    return sortOrder === 'desc' ? -comparison : comparison
  })
}