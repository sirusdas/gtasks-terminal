/**
 * Tasks Due Today Component
 * Replaces the Recent Tasks section with comprehensive "Tasks Due Today" functionality
 * Includes full filtering capabilities from Task Management
 */

import React from 'react'
import { motion } from 'framer-motion'
import { useDueToday } from '@/hooks/use-due-today'
import { EnhancedFilterPanel } from '@/components/EnhancedFilterPanel'
import type { DueTodayTask, DueTodayTaskGroup } from '@/types/due-today-filters'

interface TasksDueTodayProps {
  className?: string
}

const TasksDueToday: React.FC<TasksDueTodayProps> = ({ className = '' }) => {
  const {
    widgetState,
    dueTodayFilters,
    dueTodayTasks,
    dueTodayGroups,
    dueTodayStats,
    filterOptions,
    updateWidgetState,
    updateDueTodayFilters,
    toggleTaskSelection,
    clearTaskSelection,
    selectAllTasks,
    refreshData,
    hasSelectedTasks,
    totalTasksCount,
    selectedTasksCount
  } = useDueToday()

  // Handle task completion
  const handleTaskComplete = (taskId: string) => {
    // This would integrate with the task management system
    console.log('Complete task:', taskId)
  }

  // Handle task editing
  const handleTaskEdit = (taskId: string) => {
    // This would open task edit modal
    console.log('Edit task:', taskId)
  }

  // Handle task deletion
  const handleTaskDelete = (taskId: string) => {
    // This would handle task deletion
    console.log('Delete task:', taskId)
  }

  // Toggle filters visibility
  const toggleFilters = () => {
    updateWidgetState({ showFilters: !widgetState.showFilters })
  }

  // Change view mode
  const changeViewMode = (mode: 'list' | 'cards' | 'timeline') => {
    updateWidgetState({ viewMode: mode })
  }

  // Sort change handler
  const handleSortChange = (sortBy: string, sortOrder: 'asc' | 'desc') => {
    updateDueTodayFilters({ sortBy, sortOrder })
  }

  // Group change handler
  const handleGroupChange = (grouping: string) => {
    updateDueTodayFilters({
      timeGrouping: {
        enabled: true,
        intervals: grouping as any
      }
    })
  }

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <svg className="w-5 h-5 text-orange-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
              </svg>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Tasks Due Today
              </h3>
            </div>
            
            {/* Task count */}
            <div className="flex items-center space-x-2">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                {dueTodayStats.total}
              </span>
              
              {/* Overdue indicator */}
              {dueTodayStats.overdue > 0 && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                  {dueTodayStats.overdue} overdue
                </span>
              )}
              
              {/* Due now indicator */}
              {dueTodayStats.dueNow > 0 && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                  {dueTodayStats.dueNow} due now
                </span>
              )}
            </div>
          </div>

          {/* Header actions */}
          <div className="flex items-center space-x-2">
            {/* Refresh button */}
            <button
              onClick={refreshData}
              disabled={widgetState.isLoading}
              className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-50"
              title="Refresh"
            >
              <svg 
                className={`w-4 h-4 ${widgetState.isLoading ? 'animate-spin' : ''}`} 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>

            {/* Filter toggle */}
            <button
              onClick={toggleFilters}
              className={`p-2 rounded-md ${
                widgetState.showFilters 
                  ? 'text-blue-600 bg-blue-50' 
                  : 'text-gray-400 hover:text-gray-600'
              }`}
              title="Toggle filters"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
              </svg>
            </button>

            {/* View mode toggle */}
            <div className="flex rounded-md shadow-sm">
              <button
                onClick={() => changeViewMode('list')}
                className={`px-3 py-1 text-xs font-medium rounded-l-md border ${
                  widgetState.viewMode === 'list'
                    ? 'bg-blue-50 text-blue-700 border-blue-200'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                List
              </button>
              <button
                onClick={() => changeViewMode('cards')}
                className={`px-3 py-1 text-xs font-medium border-t border-b ${
                  widgetState.viewMode === 'cards'
                    ? 'bg-blue-50 text-blue-700 border-blue-200'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                Cards
              </button>
              <button
                onClick={() => changeViewMode('timeline')}
                className={`px-3 py-1 text-xs font-medium rounded-r-md border ${
                  widgetState.viewMode === 'timeline'
                    ? 'bg-blue-50 text-blue-700 border-blue-200'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                Timeline
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Filters Panel */}
      {widgetState.showFilters && (
        <div className="border-b border-gray-200 dark:border-gray-700">
          <EnhancedFilterPanel />
        </div>
      )}

      {/* Controls */}
      <div className="px-6 py-3 bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {/* Bulk actions */}
            {hasSelectedTasks && (
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600 dark:text-gray-300">
                  {selectedTasksCount} selected
                </span>
                <button
                  onClick={clearTaskSelection}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  Clear
                </button>
              </div>
            )}

            {/* Sort controls */}
            <div className="flex items-center space-x-2">
              <label className="text-sm text-gray-600 dark:text-gray-300">Sort by:</label>
              <select
                value={dueTodayFilters.sortBy}
                onChange={(e) => handleSortChange(e.target.value, dueTodayFilters.sortOrder || 'asc')}
                className="text-sm border-gray-300 rounded-md dark:bg-gray-600 dark:border-gray-500"
              >
                <option value="due">Due Time</option>
                <option value="priority">Priority</option>
                <option value="created">Created Date</option>
                <option value="title">Title</option>
              </select>
              <button
                onClick={() => handleSortChange(
                  dueTodayFilters.sortBy || 'due',
                  dueTodayFilters.sortOrder === 'asc' ? 'desc' : 'asc'
                )}
                className="p-1 text-gray-400 hover:text-gray-600"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d={
                      dueTodayFilters.sortOrder === 'asc' 
                        ? "M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" 
                        : "M3 4h13M3 8h9m-9 4h9m5-4v12m0 0l-4-4m4 4l4-4"
                    } 
                  />
                </svg>
              </button>
            </div>

            {/* Grouping controls */}
            <div className="flex items-center space-x-2">
              <label className="text-sm text-gray-600 dark:text-gray-300">Group by:</label>
              <select
                value={dueTodayFilters.timeGrouping?.intervals || 'none'}
                onChange={(e) => handleGroupChange(e.target.value)}
                className="text-sm border-gray-300 rounded-md dark:bg-gray-600 dark:border-gray-500"
              >
                <option value="none">None</option>
                <option value="hour">Hour</option>
                <option value="morning">Morning/Afternoon/Evening</option>
                <option value="afternoon">Business Hours</option>
              </select>
            </div>
          </div>

          <div className="text-sm text-gray-600 dark:text-gray-300">
            {totalTasksCount} tasks
          </div>
        </div>
      </div>

      {/* Task Groups */}
      <div className="p-6">
        {dueTodayGroups.length === 0 ? (
          <div className="text-center py-12">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No tasks due today</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              All caught up! No tasks are due today.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {dueTodayGroups.map((group: DueTodayTaskGroup) => (
              <div key={group.timeSlot} className="space-y-3">
                {dueTodayGroups.length > 1 && (
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                      {group.label}
                    </h4>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {group.count} task{group.count !== 1 ? 's' : ''}
                    </span>
                  </div>
                )}

                <div className="space-y-2">
                  {group.tasks.map((task: DueTodayTask) => (
                    <TaskCard
                      key={task.id}
                      task={task}
                      isSelected={widgetState.selectedTasks.includes(task.id)}
                      onToggleSelection={() => toggleTaskSelection(task.id)}
                      onComplete={() => handleTaskComplete(task.id)}
                      onEdit={() => handleTaskEdit(task.id)}
                      onDelete={() => handleTaskDelete(task.id)}
                      viewMode={widgetState.viewMode}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// Individual Task Card Component
interface TaskCardProps {
  task: DueTodayTask
  isSelected: boolean
  onToggleSelection: () => void
  onComplete: () => void
  onEdit: () => void
  onDelete: () => void
  viewMode: 'list' | 'cards' | 'timeline'
}

const TaskCard: React.FC<TaskCardProps> = ({
  task,
  isSelected,
  onToggleSelection,
  onComplete,
  onEdit,
  onDelete,
  viewMode
}) => {
  const formatTime = (dueDate?: string) => {
    if (!dueDate) return 'No time'
    const date = new Date(dueDate)
    return date.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    })
  }

  const getPriorityBadgeColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'critical':
        return 'bg-red-100 text-red-800'
      case 'high':
        return 'bg-orange-100 text-orange-800'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800'
      case 'low':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (viewMode === 'timeline') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`
          relative flex items-start p-4 border rounded-lg cursor-pointer transition-colors
          ${isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'}
          ${task.isOverdue ? 'border-red-300 bg-red-50' : ''}
        `}
        onClick={onToggleSelection}
      >
        {/* Timeline indicator */}
        <div className="flex-shrink-0 w-16 text-center">
          <div className="text-xs font-medium text-gray-500">
            {formatTime(task.due)}
          </div>
          <div className={`w-2 h-2 rounded-full mx-auto mt-1 ${
            task.isOverdue ? 'bg-red-500' : 'bg-blue-500'
          }`} />
        </div>

        {/* Task content */}
        <div className="flex-1 ml-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                {task.title}
              </h4>
              {task.description && (
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  {task.description}
                </p>
              )}
              <div className="mt-2 flex items-center space-x-2">
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getPriorityBadgeColor(task.priority)}`}>
                  {task.priority}
                </span>
                <span className="text-xs text-gray-500">
                  {task.timeUntilDue}
                </span>
                {task.tags.map(tag => (
                  <span key={tag} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center space-x-1 ml-4">
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onComplete()
                }}
                className="p-1 text-green-600 hover:text-green-800"
                title="Mark complete"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onEdit()
                }}
                className="p-1 text-blue-600 hover:text-blue-800"
                title="Edit task"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onDelete()
                }}
                className="p-1 text-red-600 hover:text-red-800"
                title="Delete task"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`
        flex items-center p-4 border rounded-lg cursor-pointer transition-colors
        ${isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'}
        ${task.isOverdue ? 'border-red-300 bg-red-50' : ''}
      `}
      onClick={onToggleSelection}
    >
      {/* Selection checkbox */}
      <div className="flex-shrink-0">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={onToggleSelection}
          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
        />
      </div>

      {/* Task content */}
      <div className="flex-1 ml-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h4 className="text-sm font-medium text-gray-900 dark:text-white">
              {task.title}
            </h4>
            {task.description && (
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                {task.description}
              </p>
            )}
            <div className="mt-2 flex items-center space-x-2">
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getPriorityBadgeColor(task.priority)}`}>
                {task.priority}
              </span>
              <span className="text-xs text-gray-500">
                {task.due ? formatTime(task.due) : 'No time'} • {task.timeUntilDue}
              </span>
              {task.tags.slice(0, 3).map(tag => (
                <span key={tag} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                  {tag}
                </span>
              ))}
              {task.tags.length > 3 && (
                <span className="text-xs text-gray-500">
                  +{task.tags.length - 3} more
                </span>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-1 ml-4">
            <button
              onClick={(e) => {
                e.stopPropagation()
                onComplete()
              }}
              className="p-1 text-green-600 hover:text-green-800"
              title="Mark complete"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation()
                onEdit()
              }}
              className="p-1 text-blue-600 hover:text-blue-800"
              title="Edit task"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation()
                onDelete()
              }}
              className="p-1 text-red-600 hover:text-red-800"
              title="Delete task"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

export default TasksDueToday