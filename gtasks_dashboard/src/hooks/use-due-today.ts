/**
 * Custom hook for "Tasks Due Today" functionality
 * Integrates with the enhanced dashboard store and provides due today specific functionality
 */

import { useState, useEffect, useCallback, useMemo } from 'react'
import { useEnhancedDashboardStore } from '@/store/enhanced-store'
import type { 
  DueTodayTask, 
  DueTodayTaskGroup, 
  DueTodayTaskFilters,
  DueTodayWidgetState 
} from '@/types/due-today-filters'
import { 
  processTasksForDueToday,
  groupTasksByTime,
  shouldRefreshForMidnight,
  getTimeUntilMidnight 
} from '@/utils/due-today-utils'

export const useDueToday = () => {
  const {
    tasks,
    activeAccount,
    filters: globalFilters,
    getFilteredTasks,
    setLoading,
    addError,
    updateRealtime
  } = useEnhancedDashboardStore()

  // Local state for due today specific functionality
  const [widgetState, setWidgetState] = useState<DueTodayWidgetState>({
    expanded: true,
    filtersVisible: false,
    selectedTasks: [],
    viewMode: 'list',
    sortBy: 'due',
    sortOrder: 'asc',
    showFilters: false,
    lastRefresh: new Date(),
    isLoading: false
  })

  // Due today specific filters
  const [dueTodayFilters, setDueTodayFilters] = useState<DueTodayTaskFilters>({
    due_today_only: true,
    include_overdue: false,
    group_by_time: true,
    timeGrouping: {
      enabled: true,
      intervals: 'morning'
    },
    realtime: {
      enabled: true,
      refreshInterval: 30000,
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
    defaultPending: false,
    filter_logic: 'AND'
  })

  // Filtered tasks using the enhanced store
  const enhancedFilteredTasks = useEnhancedDashboardStore(state => state.getFilteredTasks())

  // Process tasks for due today display
  const dueTodayTasks = useMemo(() => {
    return processTasksForDueToday(enhancedFilteredTasks, dueTodayFilters)
  }, [enhancedFilteredTasks, dueTodayFilters])

  // Group tasks by time
  const dueTodayGroups = useMemo(() => {
    if (!dueTodayFilters.group_by_time || !dueTodayFilters.timeGrouping) {
      return [{
        timeSlot: 'all',
        label: 'All Tasks Due Today',
        tasks: dueTodayTasks,
        count: dueTodayTasks.length
      }]
    }
    return groupTasksByTime(dueTodayTasks, dueTodayFilters.timeGrouping.intervals)
  }, [dueTodayTasks, dueTodayFilters.group_by_time, dueTodayFilters.timeGrouping])

  // Calculate statistics
  const dueTodayStats = useMemo(() => {
    const total = dueTodayTasks.length
    const overdue = dueTodayTasks.filter((task: DueTodayTask) => task.isOverdue).length
    const dueNow = dueTodayTasks.filter((task: DueTodayTask) => task.isDueNow).length
    const byPriority = {
      critical: dueTodayTasks.filter((task: DueTodayTask) => task.priority === 'critical').length,
      high: dueTodayTasks.filter((task: DueTodayTask) => task.priority === 'high').length,
      medium: dueTodayTasks.filter((task: DueTodayTask) => task.priority === 'medium').length,
      low: dueTodayTasks.filter((task: DueTodayTask) => task.priority === 'low').length
    }

    return {
      total,
      overdue,
      dueNow,
      byPriority,
      completionRate: 0 // Calculate based on completed vs total
    }
  }, [dueTodayTasks])

  // Update widget state
  const updateWidgetState = useCallback((updates: Partial<DueTodayWidgetState>) => {
    setWidgetState(prev => ({ ...prev, ...updates }))
  }, [])

  // Update filters
  const updateDueTodayFilters = useCallback((updates: Partial<DueTodayTaskFilters>) => {
    setDueTodayFilters(prev => ({ ...prev, ...updates }))
  }, [])

  // Toggle task selection
  const toggleTaskSelection = useCallback((taskId: string) => {
    setWidgetState(prev => ({
      ...prev,
      selectedTasks: prev.selectedTasks.includes(taskId)
        ? prev.selectedTasks.filter(id => id !== taskId)
        : [...prev.selectedTasks, taskId]
    }))
  }, [])

  // Clear task selection
  const clearTaskSelection = useCallback(() => {
    setWidgetState(prev => ({ ...prev, selectedTasks: [] }))
  }, [])

  // Select all visible tasks
  const selectAllTasks = useCallback(() => {
    const visibleTaskIds = dueTodayTasks.map((task: DueTodayTask) => task.id)
    setWidgetState(prev => ({ ...prev, selectedTasks: visibleTaskIds }))
  }, [dueTodayTasks])

  // Refresh data
  const refreshData = useCallback(async () => {
    try {
      setWidgetState(prev => ({ ...prev, isLoading: true }))
      setLoading(true)
      
      // Trigger a refresh of the enhanced store
      // This would typically involve calling an API or triggering store actions
      updateRealtime({
        lastUpdate: new Date().toISOString(),
        syncStatus: 'loading'
      })

      // Simulate refresh delay
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      setWidgetState(prev => ({ 
        ...prev, 
        isLoading: false, 
        lastRefresh: new Date() 
      }))
      setLoading(false)
      
      updateRealtime({
        syncStatus: 'idle'
      })
    } catch (error) {
      console.error('Failed to refresh due today data:', error)
      addError({
        type: 'refresh_failed',
        message: 'Failed to refresh tasks due today',
        recoverable: true
      })
      setWidgetState(prev => ({ ...prev, isLoading: false }))
      setLoading(false)
    }
  }, [setLoading, addError, updateRealtime])

  // Auto-refresh functionality
  useEffect(() => {
    if (!dueTodayFilters.realtime?.enabled) return

    const refreshInterval = dueTodayFilters.realtime.refreshInterval
    const intervalId = setInterval(() => {
      refreshData()
    }, refreshInterval)

    return () => clearInterval(intervalId)
  }, [dueTodayFilters.realtime?.enabled, dueTodayFilters.realtime?.refreshInterval, refreshData])

  // Midnight refresh
  useEffect(() => {
    if (!dueTodayFilters.realtime?.midnightRefresh) return

    const timeUntilMidnight = getTimeUntilMidnight()
    const timeoutId = setTimeout(() => {
      refreshData()
      
      // Set up recurring midnight refresh
      const midnightInterval = setInterval(() => {
        refreshData()
      }, 24 * 60 * 60 * 1000) // 24 hours

      return () => clearInterval(midnightInterval)
    }, timeUntilMidnight)

    return () => clearTimeout(timeoutId)
  }, [dueTodayFilters.realtime?.midnightRefresh, refreshData])

  // Check for midnight rollover
  useEffect(() => {
    if (shouldRefreshForMidnight(widgetState.lastRefresh)) {
      refreshData()
    }
  }, [widgetState.lastRefresh, refreshData])

  // Filter options for dropdowns
  const filterOptions = useMemo(() => {
    const options = {
      status: [] as Array<{ value: string; label: string; count: number }>,
      priority: [] as Array<{ value: string; label: string; count: number }>,
      projects: [] as Array<{ value: string; label: string; count: number }>,
      tags: [] as Array<{ value: string; label: string; count: number }>,
      lists: [] as Array<{ value: string; label: string; count: number }>
    }

    // Calculate options from due today tasks
    dueTodayTasks.forEach((task: DueTodayTask) => {
      // Status
      const statusOption = options.status.find(opt => opt.value === task.status)
      if (statusOption) {
        statusOption.count++
      } else {
        options.status.push({
          value: task.status,
          label: task.status.charAt(0).toUpperCase() + task.status.slice(1).replace('_', ' '),
          count: 1
        })
      }

      // Priority
      const priorityOption = options.priority.find(opt => opt.value === task.priority)
      if (priorityOption) {
        priorityOption.count++
      } else {
        options.priority.push({
          value: task.priority,
          label: task.priority.charAt(0).toUpperCase() + task.priority.slice(1),
          count: 1
        })
      }

      // Projects
      const project = task.project || 'Unassigned'
      const projectOption = options.projects.find(opt => opt.value === project)
      if (projectOption) {
        projectOption.count++
      } else {
        options.projects.push({
          value: project,
          label: project,
          count: 1
        })
      }

      // Tags
      task.tags.forEach((tag: string) => {
        const tagOption = options.tags.find(opt => opt.value === tag)
        if (tagOption) {
          tagOption.count++
        } else {
          options.tags.push({
            value: tag,
            label: tag,
            count: 1
          })
        }
      })

      // Lists
      const list = task.list_title || 'Unassigned'
      const listOption = options.lists.find(opt => opt.value === list)
      if (listOption) {
        listOption.count++
      } else {
        options.lists.push({
          value: list,
          label: list,
          count: 1
        })
      }
    })

    return options
  }, [dueTodayTasks])

  return {
    // State
    widgetState,
    dueTodayFilters,
    dueTodayTasks,
    dueTodayGroups,
    dueTodayStats,
    filterOptions,

    // Actions
    updateWidgetState,
    updateDueTodayFilters,
    toggleTaskSelection,
    clearTaskSelection,
    selectAllTasks,
    refreshData,

    // Computed
    hasSelectedTasks: widgetState.selectedTasks.length > 0,
    totalTasksCount: dueTodayTasks.length,
    selectedTasksCount: widgetState.selectedTasks.length
  }
}