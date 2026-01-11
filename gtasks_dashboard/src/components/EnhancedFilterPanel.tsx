/**
 * Enhanced Filter Panel with Multiselect Filters and Date Range Support
 * This component provides comprehensive filtering capabilities for the task management interface
 */

import React, { useState, useEffect, useMemo } from 'react'
import { useEnhancedFilters, useEnhancedFilteredTasks, useEnhancedFilterOptions } from '@/store/enhanced-store'
import type { DateRange, ActiveFilter, FilterOption } from '@/types/enhanced-filters'

// Multiselect Dropdown Component with Search
interface MultiselectDropdownProps {
  options: FilterOption[]
  selected: string[]
  onChange: (selected: string[]) => void
  placeholder?: string
  searchPlaceholder?: string
  maxHeight?: number
  showSearch?: boolean
  allowClear?: boolean
  disabled?: boolean
  loading?: boolean
}

const MultiselectDropdown: React.FC<MultiselectDropdownProps> = ({
  options,
  selected,
  onChange,
  placeholder = 'Select options...',
  searchPlaceholder = 'Search options...',
  maxHeight = 300,
  showSearch = true,
  allowClear = true,
  disabled = false,
  loading = false
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [focusedIndex, setFocusedIndex] = useState(-1)

  // Filter options based on search term
  const filteredOptions = useMemo(() => {
    if (!searchTerm) return options
    return options.filter(option => 
      option.label.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }, [options, searchTerm])

  // Handle selection
  const handleSelect = (value: string) => {
    if (selected.includes(value)) {
      onChange(selected.filter(v => v !== value))
    } else {
      onChange([...selected, value])
    }
  }

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        setIsOpen(true)
      }
      return
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setFocusedIndex(prev => 
          prev < filteredOptions.length - 1 ? prev + 1 : prev
        )
        break
      case 'ArrowUp':
        e.preventDefault()
        setFocusedIndex(prev => prev > 0 ? prev - 1 : -1)
        break
      case 'Enter':
        e.preventDefault()
        if (focusedIndex >= 0 && focusedIndex < filteredOptions.length) {
          handleSelect(filteredOptions[focusedIndex].value)
        }
        break
      case 'Escape':
        e.preventDefault()
        setIsOpen(false)
        setFocusedIndex(-1)
        break
    }
  }

  // Get display text
  const getDisplayText = () => {
    if (selected.length === 0) return placeholder
    if (selected.length === 1) {
      const option = options.find(opt => opt.value === selected[0])
      return option?.label || selected[0]
    }
    return `${selected.length} options selected`
  }

  // Get selected option objects
  const selectedOptions = options.filter(opt => selected.includes(opt.value))

  return (
    <div className="relative">
      <div
        className={`
          flex items-center justify-between px-3 py-2 border rounded cursor-pointer
          ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white hover:bg-gray-50'}
          ${isOpen ? 'ring-2 ring-blue-500 border-blue-500' : 'border-gray-300'}
        `}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        tabIndex={disabled ? -1 : 0}
        role="combobox"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      >
        <span className={`flex-1 ${selected.length === 0 ? 'text-gray-500' : 'text-gray-900'}`}>
          {getDisplayText()}
        </span>
        
        <div className="flex items-center space-x-1">
          {allowClear && selected.length > 0 && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation()
                onChange([])
              }}
              className="p-1 text-gray-400 hover:text-gray-600"
              aria-label="Clear selection"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
          
          <svg 
            className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {isOpen && !disabled && (
        <div 
          className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded shadow-lg"
          style={{ maxHeight: `${maxHeight}px`, overflowY: 'auto' }}
        >
          {showSearch && (
            <div className="p-2 border-b border-gray-200">
              <input
                type="text"
                placeholder={searchPlaceholder}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                autoFocus
              />
            </div>
          )}
          
          {loading ? (
            <div className="p-4 text-center text-gray-500">
              <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
              Loading...
            </div>
          ) : filteredOptions.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              {searchTerm ? 'No options found' : 'No options available'}
            </div>
          ) : (
            <div role="listbox">
              {filteredOptions.map((option, index) => {
                const isSelected = selected.includes(option.value)
                return (
                  <div
                    key={option.value}
                    role="option"
                    aria-selected={isSelected}
                    className={`
                      px-3 py-2 cursor-pointer flex items-center justify-between
                      ${focusedIndex === index ? 'bg-blue-50' : ''}
                      ${isSelected ? 'bg-blue-100 text-blue-900' : 'text-gray-900 hover:bg-gray-50'}
                    `}
                    onClick={() => handleSelect(option.value)}
                    onMouseEnter={() => setFocusedIndex(index)}
                  >
                    <span className="flex-1">{option.label}</span>
                    
                    <div className="flex items-center space-x-2">
                      {option.count !== undefined && (
                        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                          {option.count}
                        </span>
                      )}
                      
                      {isSelected && (
                        <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// Date Range Picker Component
interface DateRangePickerProps {
  value?: DateRange
  onChange: (range: DateRange | undefined) => void
  presets?: Array<{
    label: string
    type: DateRange['type']
    getValue: () => DateRange
  }>
  placeholder?: string
  disabled?: boolean
}

const DateRangePicker: React.FC<DateRangePickerProps> = ({
  value,
  onChange,
  presets,
  placeholder = 'Select date range...',
  disabled = false
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [startDate, setStartDate] = useState(value?.start || '')
  const [endDate, setEndDate] = useState(value?.end || '')
  const [selectedPreset, setSelectedPreset] = useState<DateRange['type'] | undefined>(value?.type)

  useEffect(() => {
    setStartDate(value?.start || '')
    setEndDate(value?.end || '')
    setSelectedPreset(value?.type)
  }, [value])

  const handleApply = () => {
    const range: DateRange = {
      start: startDate || undefined,
      end: endDate || undefined,
      type: selectedPreset
    }
    onChange(range)
    setIsOpen(false)
  }

  const handlePresetClick = (preset: { getValue: () => DateRange, type: DateRange['type'] }) => {
    const range = preset.getValue()
    setStartDate(range.start || '')
    setEndDate(range.end || '')
    setSelectedPreset(preset.type)
  }

  const handleClear = () => {
    setStartDate('')
    setEndDate('')
    setSelectedPreset(undefined)
    onChange(undefined)
  }

  const getDisplayText = () => {
    if (!value || (!value.start && !value.end)) return placeholder
    if (value.start && value.end) return `${value.start} to ${value.end}`
    if (value.start) return `From ${value.start}`
    if (value.end) return `Until ${value.end}`
    return placeholder
  }

  return (
    <div className="relative">
      <div
        className={`
          flex items-center justify-between px-3 py-2 border rounded cursor-pointer
          ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white hover:bg-gray-50'}
          ${isOpen ? 'ring-2 ring-blue-500 border-blue-500' : 'border-gray-300'}
        `}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        tabIndex={disabled ? -1 : 0}
      >
        <span className={`${!value ? 'text-gray-500' : 'text-gray-900'}`}>
          {getDisplayText()}
        </span>
        
        <svg 
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>

      {isOpen && !disabled && (
        <div className="absolute z-50 w-80 mt-1 bg-white border border-gray-300 rounded shadow-lg p-4">
          {/* Quick Presets */}
          {presets && presets.length > 0 && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Quick Presets</label>
              <div className="grid grid-cols-2 gap-2">
                {presets.map((preset) => (
                  <button
                    key={preset.type}
                    type="button"
                    onClick={() => handlePresetClick(preset)}
                    className={`
                      px-3 py-1 text-sm rounded border
                      ${selectedPreset === preset.type 
                        ? 'bg-blue-50 border-blue-200 text-blue-700' 
                        : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
                      }
                    `}
                  >
                    {preset.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Custom Range */}
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-between mt-4">
            <button
              type="button"
              onClick={handleClear}
              className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
            >
              Clear
            </button>
            
            <div className="space-x-2">
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleApply}
                className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Apply
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Active Filters Display Component
const ActiveFiltersDisplay: React.FC = () => {
  const activeFilters = useEnhancedFilters(state => {
    // This would be implemented with the actual store method
    return []
  })

  if (activeFilters.length === 0) return null

  return (
    <div className="flex flex-wrap gap-2 mb-4">
      {activeFilters.map((filter) => (
        <div
          key={filter.id}
          className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
        >
          <span>{filter.label}</span>
          <button
            onClick={filter.remove}
            className="p-0.5 hover:bg-blue-200 rounded-full"
            aria-label={`Remove ${filter.label}`}
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      ))}
    </div>
  )
}

// Main Enhanced Filter Panel
export const EnhancedFilterPanel: React.FC = () => {
  const {
    filters,
    setFilters,
    clearFilters,
    setDateRange,
    toggleFilterLogic,
    applyQuickDatePreset
  } = useEnhancedFilters()

  const filterOptions = useEnhancedFilterOptions()
  const filteredTasks = useEnhancedFilteredTasks()

  // Quick date presets
  const datePresets = [
    { label: 'Today', type: 'today' as const, getValue: () => ({ 
      start: new Date().toISOString().split('T')[0], 
      end: new Date().toISOString().split('T')[0],
      type: 'today' 
    })},
    { label: 'This Week', type: 'thisWeek' as const, getValue: () => {
      const now = new Date()
      const startOfWeek = new Date(now.setDate(now.getDate() - now.getDay()))
      const endOfWeek = new Date(now.setDate(now.getDate() - now.getDay() + 6))
      return {
        start: startOfWeek.toISOString().split('T')[0],
        end: endOfWeek.toISOString().split('T')[0],
        type: 'thisWeek'
      }
    }},
    { label: 'This Month', type: 'thisMonth' as const, getValue: () => {
      const now = new Date()
      const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1)
      const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0)
      return {
        start: startOfMonth.toISOString().split('T')[0],
        end: endOfMonth.toISOString().split('T')[0],
        type: 'thisMonth'
      }
    }},
  ]

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Enhanced Filters</h3>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">
            {filteredTasks.length} tasks found
          </span>
          <button
            onClick={clearFilters}
            className="px-3 py-1 text-sm text-blue-600 hover:text-blue-800 border border-blue-200 rounded hover:bg-blue-50"
          >
            Clear All
          </button>
        </div>
      </div>

      {/* Active Filters Display */}
      <ActiveFiltersDisplay />

      {/* Filter Logic Toggle */}
      <div className="flex items-center mb-4">
        <label className="text-sm font-medium text-gray-700 mr-2">Filter Logic:</label>
        <button
          onClick={toggleFilterLogic}
          className={`
            px-3 py-1 text-sm rounded border
            ${filters.filter_logic === 'AND' 
              ? 'bg-blue-50 border-blue-200 text-blue-700' 
              : 'bg-green-50 border-green-200 text-green-700'
            }
          `}
        >
          {filters.filter_logic === 'AND' ? 'AND' : 'OR'}
        </button>
      </div>

      {/* Status Filter */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
        <MultiselectDropdown
          options={filterOptions.status}
          selected={filters.status || []}
          onChange={(status) => setFilters({ status })}
          placeholder="All statuses"
          showSearch={filterOptions.status.length > 10}
        />
      </div>

      {/* Priority Filter */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">Priority</label>
        <MultiselectDropdown
          options={filterOptions.priority}
          selected={filters.priority || []}
          onChange={(priority) => setFilters({ priority })}
          placeholder="All priorities"
          showSearch={filterOptions.priority.length > 5}
        />
      </div>

      {/* Projects Filter */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">Projects</label>
        <MultiselectDropdown
          options={filterOptions.projects}
          selected={filters.project || []}
          onChange={(project) => setFilters({ project })}
          placeholder="All projects"
          showSearch={filterOptions.projects.length > 8}
        />
      </div>

      {/* Tags Filter */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>
        <MultiselectDropdown
          options={filterOptions.tags}
          selected={filters.tags || []}
          onChange={(tags) => setFilters({ tags })}
          placeholder="All tags"
          showSearch={filterOptions.tags.length > 5}
        />
      </div>

      {/* Date Range Filters */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">Created Date Range</label>
        <DateRangePicker
          value={filters.created_date_range}
          onChange={(range) => setDateRange('created_date_range', range)}
          presets={datePresets}
        />
      </div>

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">Due Date Range</label>
        <DateRangePicker
          value={filters.due_date_range}
          onChange={(range) => setDateRange('due_date_range', range)}
          presets={datePresets}
        />
      </div>

      {/* Search */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
        <input
          type="text"
          placeholder="Search tasks..."
          value={filters.search || ''}
          onChange={(e) => setFilters({ search: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
      </div>
    </div>
  )
}

export default EnhancedFilterPanel