/**
 * Temporary RecentTasks component - to be replaced by TasksDueToday
 * This maintains compatibility while TasksDueToday is being implemented
 */

import React from 'react'
import { motion } from 'framer-motion'
import type { Task } from '@/types'

interface RecentTasksProps {
  tasks: Task[]
  className?: string
}

const RecentTasks: React.FC<RecentTasksProps> = ({ tasks, className = '' }) => {
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border ${className}`}>
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Recent Tasks
          </h3>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {tasks.length} tasks
          </span>
        </div>
      </div>

      <div className="p-6">
        <div className="space-y-4">
          {tasks.length === 0 ? (
            <div className="text-center py-8">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No recent tasks</h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Tasks will appear here as they are created.
              </p>
            </div>
          ) : (
            tasks.slice(0, 5).map((task, index) => (
              <motion.div
                key={task.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-start space-x-3 p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <div className="flex-shrink-0 mt-1">
                  <div className={`w-2 h-2 rounded-full ${
                    task.status === 'completed' 
                      ? 'bg-green-500' 
                      : task.priority === 'high' 
                        ? 'bg-red-500' 
                        : 'bg-blue-500'
                  }`} />
                </div>
                
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {task.title}
                  </h4>
                  {task.description && (
                    <p className="mt-1 text-xs text-gray-500 dark:text-gray-400 line-clamp-2">
                      {task.description}
                    </p>
                  )}
                  <div className="mt-2 flex items-center space-x-2">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                      task.priority === 'high' 
                        ? 'bg-red-100 text-red-800' 
                        : task.priority === 'medium'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-green-100 text-green-800'
                    }`}>
                      {task.priority}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {task.status}
                    </span>
                    {task.tags.map(tag => (
                      <span key={tag} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </motion.div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export default RecentTasks