import React, { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'

// Components
import Sidebar from '@/components/layout/Sidebar'
import Header from '@/components/layout/Header'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ErrorBoundary from '@/components/ui/ErrorBoundary'

// Hooks
import { useDashboardStore } from '@/store'
import { useAPI } from '@/api/client'

interface EnhancedDashboardLayoutProps {
  children: React.ReactNode
}

const EnhancedDashboardLayout: React.FC<EnhancedDashboardLayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [menuVisible, setMenuVisible] = useState(true) // Default to visible
  const [isLoading, setIsLoading] = useState(true)
  const { loading, errors } = useDashboardStore()
  const { getSettings, updateSettings } = useAPI()
  const location = useLocation()

  // Load settings on mount
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const response = await getSettings()
        if (response.success && response.data) {
          const settings = response.data
          setMenuVisible(settings.menu_visible !== false) // Default to true if not set
        }
      } catch (error) {
        console.warn('Failed to load settings, using defaults:', error)
        // Continue with defaults
      } finally {
        setIsLoading(false)
      }
    }

    loadSettings()
  }, [getSettings])

  // Save settings when menu visibility changes
  const handleMenuToggle = async () => {
    const newMenuVisible = !menuVisible
    setMenuVisible(newMenuVisible)
    setSidebarOpen(newMenuVisible) // Keep sidebar state in sync

    try {
      await updateSettings({ menu_visible: newMenuVisible })
    } catch (error) {
      console.warn('Failed to save menu visibility setting:', error)
      // Revert on error
      setMenuVisible(!newMenuVisible)
      setSidebarOpen(!newMenuVisible)
    }
  }

  // Handle sidebar open/close for mobile
  const handleSidebarToggle = (open: boolean) => {
    setSidebarOpen(open)
  }

  // Keyboard shortcut handler
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ctrl+M or Cmd+M to toggle menu
      if ((event.ctrlKey || event.metaKey) && event.key === 'm') {
        event.preventDefault()
        handleMenuToggle()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [menuVisible])

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      // Close mobile sidebar on desktop
      if (window.innerWidth >= 1024) {
        setSidebarOpen(false)
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const getPageTitle = () => {
    const path = location.pathname
    const titles: Record<string, string> = {
      '/dashboard': 'Dashboard',
      '/tasks': 'Tasks',
      '/hierarchy': 'Hierarchy',
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

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
        {/* Sidebar */}
        <Sidebar 
          open={sidebarOpen && menuVisible} 
          onClose={() => setSidebarOpen(false)} 
        />
        
        {/* Main Content */}
        <div 
          className={`
            flex-1 flex flex-col transition-all duration-300 ease-in-out
            ${menuVisible ? 'lg:ml-64' : 'lg:ml-0'}
          `}
        >
          {/* Header */}
          <Header
            title={getPageTitle()}
            breadcrumbs={getBreadcrumbs()}
            onMenuClick={handleMenuToggle}
            menuVisible={menuVisible}
          />
          
          {/* Page Content */}
          <main className="flex-1 overflow-y-auto">
            <div className="p-4 sm:p-6 lg:p-8">
              {loading ? (
                <div className="flex items-center justify-center h-64">
                  <LoadingSpinner size="lg" />
                </div>
              ) : (
                children
              )}
            </div>
          </main>
          
          {/* Error Notifications */}
          {errors.length > 0 && (
            <div className="fixed bottom-4 right-4 z-50 space-y-2">
              {errors.map((error, index) => (
                <div
                  key={`${error.code}-${index}`}
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
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && menuVisible && (
        <div
          className="fixed inset-0 bg-gray-600 bg-opacity-75 transition-opacity duration-300 ease-linear z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      
      {/* Keyboard Shortcut Hint */}
      <div className="hidden lg:block fixed bottom-4 left-4 z-30">
        <div className="bg-gray-800 dark:bg-gray-700 text-white text-xs px-3 py-2 rounded-lg shadow-lg opacity-70 hover:opacity-100 transition-opacity">
          Press <kbd className="bg-gray-600 px-1 rounded">Ctrl</kbd> + <kbd className="bg-gray-600 px-1 rounded">M</kbd> to toggle menu
        </div>
      </div>
    </ErrorBoundary>
  )
}

export default EnhancedDashboardLayout