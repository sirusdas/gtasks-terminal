import React from 'react'

interface Breadcrumb {
  label: string
  path: string
}

interface HeaderProps {
  title: string
  breadcrumbs: Breadcrumb[]
  onMenuClick: () => void
}

const Header: React.FC<HeaderProps> = ({ title, breadcrumbs, onMenuClick }) => {
  return (
    <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
        {/* Left side - Mobile menu button and breadcrumbs */}
        <div className="flex items-center">
          {/* Mobile menu button */}
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
            aria-label="Open menu"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          {/* Breadcrumbs */}
          <nav className="flex ml-4 lg:ml-0" aria-label="Breadcrumb">
            <ol className="flex items-center space-x-4">
              {breadcrumbs.map((breadcrumb, index) => (
                <li key={breadcrumb.path}>
                  <div className="flex items-center">
                    {index > 0 && (
                      <svg
                        className="flex-shrink-0 h-5 w-5 text-gray-300 dark:text-gray-600 mx-2"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    )}
                    <a
                      href={breadcrumb.path}
                      className={`
                        text-sm font-medium transition-colors duration-200
                        ${index === breadcrumbs.length - 1
                          ? 'text-gray-900 dark:text-white cursor-default'
                          : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                        }
                      `}
                      aria-current={index === breadcrumbs.length - 1 ? 'page' : undefined}
                    >
                      {breadcrumb.label}
                    </a>
                  </div>
                </li>
              ))}
            </ol>
          </nav>
        </div>

        {/* Right side - Actions and user menu */}
        <div className="flex items-center space-x-4">
          {/* Toggle Menu Button for Desktop */}
          <button
            onClick={onMenuClick}
            className="hidden lg:inline-flex p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500 transition-colors duration-200"
            aria-label="Toggle sidebar menu"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          {/* Page Title */}
          <h1 className="hidden sm:block text-lg font-semibold text-gray-900 dark:text-white">
            {title}
          </h1>

          {/* User menu placeholder */}
          <div className="flex items-center">
            <button className="p-2 rounded-full text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
              <span className="sr-only">View notifications</span>
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header