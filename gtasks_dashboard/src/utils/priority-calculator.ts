/**
 * Priority Calculator - Asterisk-based Priority System Enhancement
 * 
 * This module implements automatic priority calculation based on asterisk patterns in tags.
 * It supports parsing asterisk patterns from various tag formats and provides comprehensive
 * priority calculation with hierarchy management.
 */

import { Priority } from '../types'

// Priority hierarchy constants
export const PRIORITY_HIERARCHY = {
  CRITICAL: 4,
  HIGH: 3,
  MEDIUM: 2,
  LOW: 1
} as const

export type PriorityLevel = keyof typeof PRIORITY_HIERARCHY

// Asterisk pattern regex definitions
export const PRIORITY_PATTERNS = {
  // Critical: 6+ asterisks [******], [*******], etc.
  CRITICAL: /\[(\*{6,})\]/gi,
  // High: 4-5 asterisks [****], [*****]
  HIGH: /\[(\*{4,5})\]/gi,
  // Medium: 3 asterisks [***]
  MEDIUM: /\[(\*{3})\]/gi,
  // Low: 1-2 asterisks [**], [*] (treated as low/no priority)
  LOW: /\[(\*{1,2})\]/gi
} as const

/**
 * Interface for priority calculation options
 */
export interface PriorityCalculationOptions {
  allowManualOverride?: boolean
  cacheResults?: boolean
  caseSensitive?: boolean
}

/**
 * Interface for priority calculation result
 */
export interface PriorityCalculationResult {
  calculatedPriority: Priority
  manualPriority?: Priority
  asteriskPatterns: string[]
  prioritySource: 'calculated' | 'manual' | 'fallback'
  confidence: number // 0-1, how confident we are in the calculation
}

/**
 * Enhanced tag extraction interface for priority calculation
 */
export interface PriorityTagExtraction {
  bracketTags: string[]
  hashTags: string[]
  userTags: string[]
  asteriskPatterns: {
    critical: string[]
    high: string[]
    medium: string[]
    low: string[]
  }
}

/**
 * Cache for priority calculations to improve performance
 */
class PriorityCalculationCache {
  private cache = new Map<string, PriorityCalculationResult>()
  private maxCacheSize = 1000

  set(key: string, result: PriorityCalculationResult): void {
    if (this.cache.size >= this.maxCacheSize) {
      const firstKey = this.cache.keys().next().value
      if (firstKey !== undefined) {
        this.cache.delete(firstKey)
      }
    }
    this.cache.set(key, result)
  }

  get(key: string): PriorityCalculationResult | undefined {
    return this.cache.get(key)
  }

  clear(): void {
    this.cache.clear()
  }

  getSize(): number {
    return this.cache.size
  }
}

const priorityCache = new PriorityCalculationCache()

/**
 * Extract and categorize asterisk patterns from tags
 * 
 * @param tags - Array of tags to analyze
 * @returns PriorityTagExtraction with categorized asterisk patterns
 */
export function extractAsteriskPatterns(tags: string[]): PriorityTagExtraction {
  const bracketTags: string[] = []
  const hashTags: string[] = []
  const userTags: string[] = []
  const asteriskPatterns = {
    critical: [] as string[],
    high: [] as string[],
    medium: [] as string[],
    low: [] as string[]
  }

  // Process each tag
  for (const tag of tags) {
    const cleanTag = tag.trim().toLowerCase()
    
    // Categorize by tag format
    if (cleanTag.startsWith('[') && cleanTag.endsWith(']')) {
      bracketTags.push(cleanTag)
      analyzeAsteriskPattern(cleanTag, asteriskPatterns)
    } else if (cleanTag.startsWith('#')) {
      hashTags.push(cleanTag)
    } else if (cleanTag.startsWith('@')) {
      userTags.push(cleanTag)
    }
  }

  return {
    bracketTags,
    hashTags,
    userTags,
    asteriskPatterns
  }
}

/**
 * Analyze a single tag for asterisk patterns
 */
function analyzeAsteriskPattern(tag: string, patterns: {
  critical: string[]
  high: string[]
  medium: string[]
  low: string[]
}): void {
  // Check for critical priority patterns (6+ asterisks)
  const criticalMatches = tag.match(PRIORITY_PATTERNS.CRITICAL)
  if (criticalMatches) {
    patterns.critical.push(...criticalMatches)
  }

  // Check for high priority patterns (4-5 asterisks)
  const highMatches = tag.match(PRIORITY_PATTERNS.HIGH)
  if (highMatches) {
    patterns.high.push(...highMatches)
  }

  // Check for medium priority patterns (3 asterisks)
  const mediumMatches = tag.match(PRIORITY_PATTERNS.MEDIUM)
  if (mediumMatches) {
    patterns.medium.push(...mediumMatches)
  }

  // Check for low priority patterns (1-2 asterisks)
  const lowMatches = tag.match(PRIORITY_PATTERNS.LOW)
  if (lowMatches) {
    patterns.low.push(...lowMatches)
  }
}

/**
 * Calculate priority from asterisk patterns
 * Uses the highest priority found when multiple patterns exist
 * 
 * @param tags - Array of tags to analyze
 * @param manualPriority - Optional manually set priority
 * @param options - Calculation options
 * @returns PriorityCalculationResult
 */
export function calculatePriorityFromTags(
  tags: string[],
  manualPriority?: Priority,
  options: PriorityCalculationOptions = {}
): PriorityCalculationResult {
  const { allowManualOverride = true } = options
  
  // Generate cache key
  const cacheKey = `${tags.sort().join(',')}_${manualPriority}_${allowManualOverride}`
  
  // Check cache first
  const cached = priorityCache.get(cacheKey)
  if (cached) {
    return cached
  }

  // Extract asterisk patterns
  const extraction = extractAsteriskPatterns(tags)
  const { asteriskPatterns } = extraction

  // Determine calculated priority based on patterns
  let calculatedPriority: Priority = Priority.LOW // Default to low
  let confidence = 0.1 // Base confidence for no patterns
  const asteriskPatternsFound: string[] = []

  // Priority hierarchy: Critical > High > Medium > Low
  if (asteriskPatterns.critical.length > 0) {
    calculatedPriority = Priority.CRITICAL
    confidence = 1.0
    asteriskPatternsFound.push(...asteriskPatterns.critical)
  } else if (asteriskPatterns.high.length > 0) {
    calculatedPriority = Priority.HIGH
    confidence = 0.9
    asteriskPatternsFound.push(...asteriskPatterns.high)
  } else if (asteriskPatterns.medium.length > 0) {
    calculatedPriority = Priority.MEDIUM
    confidence = 0.8
    asteriskPatternsFound.push(...asteriskPatterns.medium)
  } else if (asteriskPatterns.low.length > 0) {
    calculatedPriority = Priority.LOW
    confidence = 0.7
    asteriskPatternsFound.push(...asteriskPatterns.low)
  } else {
    // No asterisk patterns found - low priority
    calculatedPriority = Priority.LOW
    confidence = 0.3
  }

  // Determine final priority
  let finalPriority: Priority
  let prioritySource: 'calculated' | 'manual' | 'fallback'
  
  if (allowManualOverride && manualPriority) {
    finalPriority = manualPriority
    prioritySource = 'manual'
    confidence = 1.0 // Manual priority has highest confidence
  } else {
    finalPriority = calculatedPriority
    prioritySource = 'calculated'
  }

  const result: PriorityCalculationResult = {
    calculatedPriority,
    manualPriority,
    asteriskPatterns: asteriskPatternsFound,
    prioritySource,
    confidence
  }

  // Cache the result
  if (options.cacheResults !== false) {
    priorityCache.set(cacheKey, result)
  }

  return result
}

/**
 * Validate asterisk pattern syntax
 * 
 * @param pattern - Pattern to validate
 * @returns boolean indicating if pattern is valid
 */
export function validateAsteriskPattern(pattern: string): boolean {
  // Check for balanced brackets
  const bracketCount = (pattern.match(/\[/g) || []).length
  const bracketCountEnd = (pattern.match(/\]/g) || []).length
  
  if (bracketCount !== bracketCountEnd) {
    return false
  }

  // Check for valid asterisk counts
  const asteriskMatches = pattern.match(/\*/g)
  if (!asteriskMatches) {
    return true // No asterisks is valid (just a regular tag)
  }

  const asteriskCount = asteriskMatches.length
  return asteriskCount >= 1 // Allow 1+ asterisks
}

/**
 * Generate sample asterisk patterns for testing
 * 
 * @returns Array of sample patterns with expected priorities
 */
export function generateSampleAsteriskPatterns(): Array<{
  pattern: string
  expectedPriority: Priority
  description: string
}> {
  return [
    // Critical patterns (6+ asterisks)
    { pattern: '[******]', expectedPriority: Priority.CRITICAL, description: '6 asterisks - Critical' },
    { pattern: '[*******]', expectedPriority: Priority.CRITICAL, description: '7 asterisks - Critical' },
    { pattern: '[********]', expectedPriority: Priority.CRITICAL, description: '8 asterisks - Critical' },
    
    // High patterns (4-5 asterisks)
    { pattern: '[****]', expectedPriority: Priority.HIGH, description: '4 asterisks - High' },
    { pattern: '[*****]', expectedPriority: Priority.HIGH, description: '5 asterisks - High' },
    
    // Medium patterns (3 asterisks)
    { pattern: '[***]', expectedPriority: Priority.MEDIUM, description: '3 asterisks - Medium' },
    
    // Low patterns (1-2 asterisks)
    { pattern: '[*]', expectedPriority: Priority.LOW, description: '1 asterisk - Low' },
    { pattern: '[**]', expectedPriority: Priority.LOW, description: '2 asterisks - Low' },
    
    // Mixed patterns with content
    { pattern: '[***urgent]', expectedPriority: Priority.MEDIUM, description: '3 asterisks with content - Medium' },
    { pattern: '[****important]', expectedPriority: Priority.HIGH, description: '4 asterisks with content - High' },
    { pattern: '[******critical]', expectedPriority: Priority.CRITICAL, description: '6 asterisks with content - Critical' },
    
    // Non-asterisk patterns (should not affect priority)
    { pattern: '[urgent]', expectedPriority: Priority.LOW, description: 'No asterisks - Low (default)' },
    { pattern: '[important]', expectedPriority: Priority.LOW, description: 'No asterisks - Low (default)' },
    { pattern: '#work', expectedPriority: Priority.LOW, description: 'Hash tag - Low (default)' },
    { pattern: '@john', expectedPriority: Priority.LOW, description: 'User tag - Low (default)' }
  ]
}

/**
 * Clear the priority calculation cache
 */
export function clearPriorityCache(): void {
  priorityCache.clear()
}

/**
 * Get cache statistics
 */
export function getPriorityCacheStats(): { size: number; maxSize: number } {
  return {
    size: priorityCache.getSize(),
    maxSize: 1000
  }
}

/**
 * Batch calculate priorities for multiple tasks
 * 
 * @param tasks - Array of tasks with tags
 * @param options - Calculation options
 * @returns Array of priority calculation results
 */
export function batchCalculatePriorities(
  tasks: Array<{ tags: string[]; priority?: Priority }>,
  options: PriorityCalculationOptions = {}
): PriorityCalculationResult[] {
  return tasks.map(task => 
    calculatePriorityFromTags(task.tags, task.priority, options)
  )
}

/**
 * Get priority level from priority value
 * 
 * @param priority - Priority enum value
 * @returns Priority level number
 */
export function getPriorityLevel(priority: Priority): number {
  return PRIORITY_HIERARCHY[priority.toUpperCase() as PriorityLevel] || 0
}

/**
 * Compare two priorities
 * 
 * @param priority1 - First priority
 * @param priority2 - Second priority
 * @returns Negative if priority1 < priority2, 0 if equal, positive if priority1 > priority2
 */
export function comparePriorities(priority1: Priority, priority2: Priority): number {
  return getPriorityLevel(priority2) - getPriorityLevel(priority1)
}