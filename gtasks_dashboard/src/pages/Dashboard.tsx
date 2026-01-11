import React from 'react'
import { motion } from 'framer-motion'

// Components
import StatsCards from '@/components/dashboard/StatsCards'
import TaskGraph from '@/components/dashboard/TaskGraph'
import TasksDueToday from '@/components/dashboard/TasksDueToday'
import AccountSwitcher from '@/components/dashboard/AccountSwitcher'
import QuickActions from '@/components/dashboard/QuickActions'
import ProductivityChart from '@/components/dashboard/ProductivityChart'

// Hooks
import { useDashboardStore, useStats, useFilteredTasks } from '@/store'

const Dashboard: React.FC = () => {
  const { accounts, activeAccount } = useDashboardStore()
  const stats = useStats()
  const tasks = useFilteredTasks()

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  }

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        type: "spring",
        stiffness: 100
      }
    }
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Dashboard
          </h1>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            Welcome back! Here's what's happening with your tasks.
          </p>
        </div>
        
        <div className="mt-4 sm:mt-0 flex items-center space-x-3">
          <AccountSwitcher />
          <QuickActions />
        </div>
      </motion.div>

      {/* Stats Cards */}
      <motion.div variants={itemVariants}>
        <StatsCards stats={stats} />
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Task Graph - Takes 2 columns on large screens */}
        <motion.div 
          variants={itemVariants}
          className="lg:col-span-2"
        >
          <TaskGraph />
        </motion.div>

        {/* Productivity Chart - Takes 1 column on large screens */}
        <motion.div variants={itemVariants}>
          <ProductivityChart />
        </motion.div>
      </div>

      {/* Tasks Due Today - Replaces Recent Tasks */}
      <motion.div variants={itemVariants}>
        <TasksDueToday />
      </motion.div>

      {/* Additional Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div variants={itemVariants} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                  Due Today
                </dt>
                <dd className="text-lg font-medium text-gray-900 dark:text-white">
                  {tasks.filter(task => {
                    if (!task.due) return false
                    const today = new Date().toDateString()
                    return new Date(task.due).toDateString() === today
                  }).length}
                </dd>
              </dl>
            </div>
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-yellow-100 dark:bg-yellow-900 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-yellow-600 dark:text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                  Overdue
                </dt>
                <dd className="text-lg font-medium text-gray-900 dark:text-white">
                  {stats.overdueTasks}
                </dd>
              </dl>
            </div>
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-100 dark:bg-green-900 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                  Completion Rate
                </dt>
                <dd className="text-lg font-medium text-gray-900 dark:text-white">
                  {stats.completionRate.toFixed(1)}%
                </dd>
              </dl>
            </div>
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-purple-100 dark:bg-purple-900 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-purple-600 dark:text-purple-400" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                  Active Accounts
                </dt>
                <dd className="text-lg font-medium text-gray-900 dark:text-white">
                  {accounts.filter(acc => acc.isActive).length}
                </dd>
              </dl>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Multi-Account Summary */}
      {accounts.length > 1 && (
        <motion.div 
          variants={itemVariants}
          className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
        >
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Account Summary
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {accounts.map((account) => (
              <div 
                key={account.id}
                className={`p-4 rounded-lg border-2 transition-colors ${
                  account.id === activeAccount
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {account.avatar ? (
                      <img 
                        src={account.avatar} 
                        alt={account.name}
                        className="w-8 h-8 rounded-full"
                      />
                    ) : (
                      <div className="w-8 h-8 bg-gray-300 dark:bg-gray-600 rounded-full flex items-center justify-center">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          {account.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                    )}
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {account.name}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {account.email}
                      </p>
                    </div>
                  </div>
                  {account.id === activeAccount && (
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  )}
                </div>
                {account.stats && (
                  <div className="mt-3 grid grid-cols-3 gap-2 text-center">
                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Tasks</p>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {account.stats.totalTasks}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Done</p>
                      <p className="text-sm font-medium text-green-600 dark:text-green-400">
                        {account.stats.completedTasks}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Rate</p>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {account.stats.completionRate.toFixed(0)}%
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}

export default Dashboard