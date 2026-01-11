import React, { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'
import { Toaster } from 'react-hot-toast'
import { motion, AnimatePresence } from 'framer-motion'

// Layouts
import DashboardLayout from '@/layouts/DashboardLayout'

// Pages
import Dashboard from '@/pages/Dashboard'
import Tasks from '@/pages/Tasks'
import Graph from '@/pages/Graph'
import Calendar from '@/pages/Calendar'
import Reports from '@/pages/Reports'
import Settings from '@/pages/Settings'
import Accounts from '@/pages/Accounts'

// Hooks
import { useDashboardStore } from '@/store'
import { useAPI } from '@/api/client'

// Styles
import '@/styles/globals.css'

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

function App() {
  const { config, setLoading, addError } = useDashboardStore()
  const api = useAPI()

  useEffect(() => {
    // Initialize the application
    const initializeApp = async () => {
      try {
        setLoading(true)
        
        // Connect to WebSocket for real-time updates
        api.connectWebSocket()
        
        // Set up WebSocket event listeners
        api.on('task_updated', (data) => {
          // Handle real-time task updates
          console.log('Task updated:', data)
        })

        api.on('task_created', (data) => {
          // Handle real-time task creation
          console.log('Task created:', data)
        })

        api.on('task_deleted', (data) => {
          // Handle real-time task deletion
          console.log('Task deleted:', data)
        })

        api.on('sync_started', (data) => {
          console.log('Sync started:', data)
        })

        api.on('sync_completed', (data) => {
          console.log('Sync completed:', data)
        })

        api.on('account_switched', (data) => {
          console.log('Account switched:', data)
        })

        // Health check
        const health = await api.healthCheck()
        if (!health.success) {
          throw new Error(health.error || 'Health check failed')
        }

        console.log('App initialized successfully')
      } catch (error) {
        console.error('Failed to initialize app:', error)
        addError({
          code: 'INIT_ERROR',
          message: 'Failed to initialize application',
          details: error,
          timestamp: new Date().toISOString(),
          recoverable: true
        })
      } finally {
        setLoading(false)
      }
    }

    initializeApp()

    // Cleanup on unmount
    return () => {
      api.disconnectWebSocket()
    }
  }, [])

  // Apply theme
  useEffect(() => {
    const root = document.documentElement
    
    if (config.appearance.theme === 'dark') {
      root.classList.add('dark')
    } else if (config.appearance.theme === 'light') {
      root.classList.remove('dark')
    } else {
      // System theme
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      if (prefersDark) {
        root.classList.add('dark')
      } else {
        root.classList.remove('dark')
      }
    }

    // Apply accent color
    root.style.setProperty('--accent-color', config.appearance.accentColor)
    
    // Apply font size
    const fontSizeMap = {
      small: '14px',
      medium: '16px',
      large: '18px'
    }
    root.style.fontSize = fontSizeMap[config.appearance.fontSize]

    // Apply density
    const densityMap = {
      compact: '0.875rem',
      comfortable: '1rem',
      spacious: '1.125rem'
    }
    root.style.lineHeight = densityMap[config.appearance.density]
  }, [config.appearance])

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
          <AnimatePresence mode="wait">
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={
                <DashboardLayout>
                  <Dashboard />
                </DashboardLayout>
              } />
              <Route path="/tasks" element={
                <DashboardLayout>
                  <Tasks />
                </DashboardLayout>
              } />
              <Route path="/graph" element={
                <DashboardLayout>
                  <Graph />
                </DashboardLayout>
              } />
              <Route path="/calendar" element={
                <DashboardLayout>
                  <Calendar />
                </DashboardLayout>
              } />
              <Route path="/reports" element={
                <DashboardLayout>
                  <Reports />
                </DashboardLayout>
              } />
              <Route path="/accounts" element={
                <DashboardLayout>
                  <Accounts />
                </DashboardLayout>
              } />
              <Route path="/settings" element={
                <DashboardLayout>
                  <Settings />
                </DashboardLayout>
              } />
            </Routes>
          </AnimatePresence>
          
          {/* Global toast notifications */}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: 'var(--toast-bg, #fff)',
                color: 'var(--toast-color, #374151)',
                border: '1px solid var(--toast-border, #e5e7eb)',
              },
              success: {
                iconTheme: {
                  primary: '#10b981',
                  secondary: '#fff',
                },
              },
              error: {
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />
        </div>
      </Router>
    </QueryClientProvider>
  )
}

export default App