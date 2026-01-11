import React, { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'

// Components
import Sidebar from '@/components/layout/Sidebar'
import Header from '@/components/layout/Header'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ErrorBoundary from '@/components/ui/ErrorBoundary'

// Hooks
import { useDashboardStore } from '@/store'

interface DashboardLayoutProps {
  children: React.ReactNode
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { loading, errors } = useDashboardStore()
  const location = useLocation()

  const getPageTitle = () => {
    const path = location.pathname
    const titles: Record<string, string> = {
      '/dashboard': 'Dashboard',
      '/tasks': 'Tasks',
      '/graph': 'Task Graph',
      '/calendar': 'Calendar',
      '/reports': 'Reports',
      '/accounts': 'Accounts',
      '/settings': 'Settings'
    }
    return titles[path] || 'GTasks Dashboard'
  }

  const getBreadcrumbs = () => {
    const path = location.pathname
    const segments = path.split('/').filter(Boolean)
    const breadcrumbs = [{ label: 'Home', path: '/' }]
    
    let currentPath = ''
    segments.forEach(segment => {
      currentPath += `/${segment}`
      const label = segment.charAt(0).toUpperCase() + segment.slice(1)
      breadcrumbs.push({ label, path: currentPath })
    })
    
    return breadcrumbs
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
        {/* Sidebar */}
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        
        {/* Main Content */}
        <div className="flex-1 flex flex-col lg:ml-64">
          {/* Header */}
          <Header
            title={getPageTitle()}
            breadcrumbs={getBreadcrumbs()}
            onMenuClick={() => setSidebarOpen(true)}
          />
          
          {/* Page Content */}
          <main className="flex-1 overflow-y-auto">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="p-4 sm:p-6 lg:p-8"
            >
              {loading ? (
                <div className="flex items-center justify-center h-64">
                  <LoadingSpinner size="lg" />
                </div>
              ) : (
                children
              )}
            </motion.div>
          </main>
          
          {/* Error Notifications */}
          {errors.length > 0 && (
            <div className="fixed bottom-4 right-4 z-50 space-y-2">
              {errors.map((error, index) => (
                <motion.div
                  key={`${error.code}-${index}`}
                  initial={{ opacity: 0, x: 100 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 100 }}
                  className="bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-200 px-4 py-3 rounded shadow-lg max-w-md"
                >
                  <div className="flex items-start">
                    <div className="flex-1">
                      <h4 className="font-medium">{error.message}</h4>
                      {error.details && (
                        <p className="text-sm mt-1 opacity-75">
                          {typeof error.details === 'string' ? error.details : JSON.stringify(error.details)}
                        </p>
                      )}
                    </div>
                    <button
                      onClick={() => {
                        // Remove error from store
                        // setErrors(errors.filter((_, i) => i !== index))
                      }}
                      className="ml-2 text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                    >
                      ×
                    </button>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>
      
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-gray-600 bg-opacity-75 transition-opacity duration-300 ease-linear z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </ErrorBoundary>
  )
}

export default DashboardLayout