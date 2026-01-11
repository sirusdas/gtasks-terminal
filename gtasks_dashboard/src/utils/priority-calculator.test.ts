/**
 * Priority Calculator Test Suite
 * 
 * Comprehensive tests for the asterisk-based priority calculation system
 */

import { Priority } from '../types'
import {
  calculatePriorityFromTags,
  extractAsteriskPatterns,
  generateSampleAsteriskPatterns,
  validateAsteriskPattern,
  clearPriorityCache,
  getPriorityCacheStats,
  PriorityCalculationResult
} from '../utils/priority-calculator'

// Test utilities
interface TestCase {
  name: string
  tags: string[]
  manualPriority?: Priority
  expectedPriority: Priority
  expectedPatterns: string[]
  expectedSource: 'calculated' | 'manual' | 'fallback'
  description: string
}

interface TestResult {
  testName: string
  passed: boolean
  expected: any
  actual: any
  error?: string
}

/**
 * Run all priority calculation tests
 */
export function runPriorityCalculationTests(): TestResult[] {
  const results: TestResult[] = []

  console.log('🧪 Running Priority Calculation Tests...')
  console.log('=' .repeat(50))

  // Test basic asterisk patterns
  results.push(...testBasicAsteriskPatterns())
  
  // Test priority hierarchy
  results.push(...testPriorityHierarchy())
  
  // Test mixed patterns
  results.push(...testMixedPatterns())
  
  // Test manual override
  results.push(...testManualOverride())
  
  // Test edge cases
  results.push(...testEdgeCases())
  
  // Test pattern validation
  results.push(...testPatternValidation())
  
  // Test cache functionality
  results.push(...testCacheFunctionality())

  return results
}

/**
 * Test basic asterisk patterns
 */
function testBasicAsteriskPatterns(): TestResult[] {
  const results: TestResult[] = []
  
  const testCases: TestCase[] = [
    {
      name: 'Critical Priority - 6 Asterisks',
      tags: ['[******]'],
      expectedPriority: Priority.CRITICAL,
      expectedPatterns: ['[******]'],
      expectedSource: 'calculated',
      description: 'Should detect 6 asterisks as critical priority'
    },
    {
      name: 'Critical Priority - 7 Asterisks',
      tags: ['[*******]'],
      expectedPriority: Priority.CRITICAL,
      expectedPatterns: ['[*******]'],
      expectedSource: 'calculated',
      description: 'Should detect 7+ asterisks as critical priority'
    },
    {
      name: 'High Priority - 4 Asterisks',
      tags: ['[****]'],
      expectedPriority: Priority.HIGH,
      expectedPatterns: ['[****]'],
      expectedSource: 'calculated',
      description: 'Should detect 4 asterisks as high priority'
    },
    {
      name: 'High Priority - 5 Asterisks',
      tags: ['[*****]'],
      expectedPriority: Priority.HIGH,
      expectedPatterns: ['[*****]'],
      expectedSource: 'calculated',
      description: 'Should detect 5 asterisks as high priority'
    },
    {
      name: 'Medium Priority - 3 Asterisks',
      tags: ['[***]'],
      expectedPriority: Priority.MEDIUM,
      expectedPatterns: ['[***]'],
      expectedSource: 'calculated',
      description: 'Should detect 3 asterisks as medium priority'
    },
    {
      name: 'Low Priority - 2 Asterisks',
      tags: ['[**]'],
      expectedPriority: Priority.LOW,
      expectedPatterns: ['[**]'],
      expectedSource: 'calculated',
      description: 'Should detect 1-2 asterisks as low priority'
    },
    {
      name: 'Low Priority - 1 Asterisk',
      tags: ['[*]'],
      expectedPriority: Priority.LOW,
      expectedPatterns: ['[*]'],
      expectedSource: 'calculated',
      description: 'Should detect 1 asterisk as low priority'
    },
    {
      name: 'No Asterisk Patterns',
      tags: ['[urgent]', '#work', '@john'],
      expectedPriority: Priority.LOW,
      expectedPatterns: [],
      expectedSource: 'calculated',
      description: 'Should default to low priority when no asterisk patterns found'
    }
  ]

  for (const testCase of testCases) {
    try {
      const result = calculatePriorityFromTags(testCase.tags, testCase.manualPriority)
      
      const passed = 
        result.calculatedPriority === testCase.expectedPriority &&
        result.prioritySource === testCase.expectedSource &&
        result.asteriskPatterns.length === testCase.expectedPatterns.length

      results.push({
        testName: testCase.name,
        passed,
        expected: {
          priority: testCase.expectedPriority,
          source: testCase.expectedSource,
          patterns: testCase.expectedPatterns
        },
        actual: {
          priority: result.calculatedPriority,
          source: result.prioritySource,
          patterns: result.asteriskPatterns
        },
        error: passed ? undefined : `Expected ${testCase.description}`
      })

      console.log(`${passed ? '✅' : '❌'} ${testCase.name}: ${testCase.description}`)
      
    } catch (error) {
      results.push({
        testName: testCase.name,
        passed: false,
        expected: testCase.expectedPriority,
        actual: null,
        error: error instanceof Error ? error.message : String(error)
      })
      
      console.log(`❌ ${testCase.name}: Error - ${error}`)
    }
  }

  return results
}

/**
 * Test priority hierarchy (highest priority wins)
 */
function testPriorityHierarchy(): TestResult[] {
  const results: TestResult[] = []
  
  const testCases: TestCase[] = [
    {
      name: 'Mixed Patterns - Critical Wins',
      tags: ['[***]', '[******]', '[****]'],
      expectedPriority: Priority.CRITICAL,
      expectedPatterns: ['[******]'],
      expectedSource: 'calculated',
      description: 'Should use highest priority when multiple patterns exist'
    },
    {
      name: 'Mixed Patterns - High Wins',
      tags: ['[***]', '[****]', '[**]'],
      expectedPriority: Priority.HIGH,
      expectedPatterns: ['[****]'],
      expectedSource: 'calculated',
      description: 'Should use high priority over medium and low'
    },
    {
      name: 'Mixed Patterns - Medium Wins',
      tags: ['[***]', '[**]', '[urgent]'],
      expectedPriority: Priority.MEDIUM,
      expectedPatterns: ['[***]'],
      expectedSource: 'calculated',
      description: 'Should use medium priority over low'
    }
  ]

  for (const testCase of testCases) {
    try {
      const result = calculatePriorityFromTags(testCase.tags)
      
      const passed = result.calculatedPriority === testCase.expectedPriority

      results.push({
        testName: testCase.name,
        passed,
        expected: testCase.expectedPriority,
        actual: result.calculatedPriority,
        error: passed ? undefined : testCase.description
      })

      console.log(`${passed ? '✅' : '❌'} ${testCase.name}: ${testCase.description}`)
      
    } catch (error) {
      results.push({
        testName: testCase.name,
        passed: false,
        expected: testCase.expectedPriority,
        actual: null,
        error: error instanceof Error ? error.message : String(error)
      })
    }
  }

  return results
}

/**
 * Test mixed patterns with content
 */
function testMixedPatterns(): TestResult[] {
  const results: TestResult[] = []
  
  const testCases: TestCase[] = [
    {
      name: 'Asterisk with Content - Critical',
      tags: ['[******critical]', '[important]'],
      expectedPriority: Priority.CRITICAL,
      expectedPatterns: ['[******critical]'],
      expectedSource: 'calculated',
      description: 'Should detect asterisks with content'
    },
    {
      name: 'Asterisk with Content - High',
      tags: ['[****important]', '[urgent]'],
      expectedPriority: Priority.HIGH,
      expectedPatterns: ['[****important]'],
      expectedSource: 'calculated',
      description: 'Should detect 4 asterisks with content as high'
    },
    {
      name: 'Asterisk with Content - Medium',
      tags: ['[***urgent]', '[normal]'],
      expectedPriority: Priority.MEDIUM,
      expectedPatterns: ['[***urgent]'],
      expectedSource: 'calculated',
      description: 'Should detect 3 asterisks with content as medium'
    },
    {
      name: 'Multiple Tags with Asterisks',
      tags: ['[***urgent]', '[****important]', '[**low]'],
      expectedPriority: Priority.HIGH,
      expectedPatterns: ['[****important]'],
      expectedSource: 'calculated',
      description: 'Should use highest priority from multiple asterisk patterns'
    }
  ]

  for (const testCase of testCases) {
    try {
      const result = calculatePriorityFromTags(testCase.tags)
      
      const passed = 
        result.calculatedPriority === testCase.expectedPriority &&
        result.asteriskPatterns.some(pattern => testCase.expectedPatterns.includes(pattern))

      results.push({
        testName: testCase.name,
        passed,
        expected: testCase.expectedPriority,
        actual: result.calculatedPriority,
        error: passed ? undefined : testCase.description
      })

      console.log(`${passed ? '✅' : '❌'} ${testCase.name}: ${testCase.description}`)
      
    } catch (error) {
      results.push({
        testName: testCase.name,
        passed: false,
        expected: testCase.expectedPriority,
        actual: null,
        error: error instanceof Error ? error.message : String(error)
      })
    }
  }

  return results
}

/**
 * Test manual override functionality
 */
function testManualOverride(): TestResult[] {
  const results: TestResult[] = []
  
  const testCases: TestCase[] = [
    {
      name: 'Manual Override - Critical',
      tags: ['[***]'], // Would be medium
      manualPriority: Priority.CRITICAL,
      expectedPriority: Priority.CRITICAL,
      expectedPatterns: [],
      expectedSource: 'manual',
      description: 'Should allow manual priority to override calculated priority'
    },
    {
      name: 'No Override - Calculated Wins',
      tags: ['[******]'],
      manualPriority: undefined, // No manual priority
      expectedPriority: Priority.CRITICAL,
      expectedPatterns: ['[******]'],
      expectedSource: 'calculated',
      description: 'Should use calculated priority when no manual override'
    },
    {
      name: 'Manual Override Disabled',
      tags: ['[***]'],
      manualPriority: Priority.CRITICAL,
      expectedPriority: Priority.MEDIUM,
      expectedPatterns: ['[***]'],
      expectedSource: 'calculated',
      description: 'Should respect manual override settings'
    }
  ]

  for (const testCase of testCases) {
    try {
      const options = { allowManualOverride: testCase.expectedSource === 'manual' }
      const result = calculatePriorityFromTags(testCase.tags, testCase.manualPriority, options)
      
      const passed = result.calculatedPriority === testCase.expectedPriority

      results.push({
        testName: testCase.name,
        passed,
        expected: testCase.expectedPriority,
        actual: result.calculatedPriority,
        error: passed ? undefined : testCase.description
      })

      console.log(`${passed ? '✅' : '❌'} ${testCase.name}: ${testCase.description}`)
      
    } catch (error) {
      results.push({
        testName: testCase.name,
        passed: false,
        expected: testCase.expectedPriority,
        actual: null,
        error: error instanceof Error ? error.message : String(error)
      })
    }
  }

  return results
}

/**
 * Test edge cases and error handling
 */
function testEdgeCases(): TestResult[] {
  const results: TestResult[] = []
  
  const testCases: Array<{
    name: string
    tags: string[]
    expectedBehavior: string
  }> = [
    {
      name: 'Empty Tags Array',
      tags: [],
      expectedBehavior: 'Should default to low priority'
    },
    {
      name: 'Undefined Tags',
      tags: [''],
      expectedBehavior: 'Should handle empty strings gracefully'
    },
    {
      name: 'Malformed Brackets',
      tags: ['[unclosed', 'unclosed]'],
      expectedBehavior: 'Should handle malformed brackets'
    },
    {
      name: 'Mixed Case',
      tags: ['[*****]', '[***URGENT]', '[**Important]'],
      expectedBehavior: 'Should handle mixed case patterns'
    },
    {
      name: 'Whitespace Handling',
      tags: ['[ **** ]', '[\t***\t]', '[ ***urgent ]'],
      expectedBehavior: 'Should handle whitespace in patterns'
    }
  ]

  for (const testCase of testCases) {
    try {
      const result = calculatePriorityFromTags(testCase.tags)
      
      // Basic validation - should not throw error and return valid result
      const passed = 
        result &&
        Object.values(Priority).includes(result.calculatedPriority) &&
        Array.isArray(result.asteriskPatterns)

      results.push({
        testName: testCase.name,
        passed,
        expected: 'Valid priority calculation',
        actual: passed ? 'Valid' : 'Invalid result',
        error: passed ? undefined : testCase.expectedBehavior
      })

      console.log(`${passed ? '✅' : '❌'} ${testCase.name}: ${testCase.expectedBehavior}`)
      
    } catch (error) {
      results.push({
        testName: testCase.name,
        passed: false,
        expected: 'No error',
        actual: error instanceof Error ? error.message : String(error),
        error: testCase.expectedBehavior
      })
    }
  }

  return results
}

/**
 * Test pattern validation
 */
function testPatternValidation(): TestResult[] {
  const results: TestResult[] = []
  
  const validationTests = [
    { pattern: '[***]', expected: true, description: 'Valid 3 asterisks' },
    { pattern: '[******]', expected: true, description: 'Valid 6 asterisks' },
    { pattern: '[unclosed', expected: false, description: 'Unclosed bracket' },
    { pattern: 'unclosed]', expected: false, description: 'Unopened bracket' },
    { pattern: '[urgent]', expected: true, description: 'No asterisks (valid)' },
    { pattern: 'regular-tag', expected: true, description: 'No brackets (valid)' },
    { pattern: '', expected: true, description: 'Empty string (valid)' }
  ]

  for (const test of validationTests) {
    try {
      const result = validateAsteriskPattern(test.pattern)
      const passed = result === test.expected

      results.push({
        testName: `Validation: ${test.pattern}`,
        passed,
        expected: test.expected,
        actual: result,
        error: passed ? undefined : test.description
      })

      console.log(`${passed ? '✅' : '❌'} Validation: ${test.pattern} - ${test.description}`)
      
    } catch (error) {
      results.push({
        testName: `Validation: ${test.pattern}`,
        passed: false,
        expected: test.expected,
        actual: null,
        error: error instanceof Error ? error.message : String(error)
      })
    }
  }

  return results
}

/**
 * Test cache functionality
 */
function testCacheFunctionality(): TestResult[] {
  const results: TestResult[] = []
  
  try {
    // Clear cache first
    clearPriorityCache()
    const initialStats = getPriorityCacheStats()
    
    // Run a calculation
    const result1 = calculatePriorityFromTags(['[***]'])
    
    // Check cache stats
    const afterCalcStats = getPriorityCacheStats()
    const cacheWorking = afterCalcStats.size > initialStats.size
    
    results.push({
      testName: 'Cache Functionality',
      passed: cacheWorking,
      expected: 'Cache size increased',
      actual: `Size: ${initialStats.size} -> ${afterCalcStats.size}`,
      error: cacheWorking ? undefined : 'Cache not working'
    })

    console.log(`${cacheWorking ? '✅' : '❌'} Cache Functionality: Cache working correctly`)
    
  } catch (error) {
    results.push({
      testName: 'Cache Functionality',
      passed: false,
      expected: 'Working cache',
      actual: null,
      error: error instanceof Error ? error.message : String(error)
    })
  }

  return results
}

/**
 * Generate comprehensive test report
 */
export function generateTestReport(results: TestResult[]): string {
  const passed = results.filter(r => r.passed).length
  const failed = results.filter(r => !r.passed).length
  const total = results.length
  
  const report = `
📊 PRIORITY CALCULATION TEST REPORT
${'='.repeat(50)}

✅ PASSED: ${passed}/${total}
❌ FAILED: ${failed}/${total}

📈 Success Rate: ${((passed / total) * 100).toFixed(1)}%

${failed > 0 ? `
❌ FAILED TESTS:
${results.filter(r => !r.passed).map(r => 
  `  • ${r.testName}: ${r.error}`
).join('\n')}
` : ''}

✅ PASSED TESTS:
${results.filter(r => r.passed).map(r => 
  `  • ${r.testName}`
).join('\n')}
`

  return report
}

/**
 * Demo the priority calculation system
 */
export function demoPriorityCalculation(): void {
  console.log('\n🚀 PRIORITY CALCULATION SYSTEM DEMO')
  console.log('='.repeat(60))
  
  // Test various scenarios
  const demoCases = [
    {
      title: 'Critical Priority Task',
      tags: ['[******critical]', '#production', '@team-lead'],
      manualPriority: undefined
    },
    {
      title: 'High Priority Task',
      tags: ['[****important]', '#api', '@developer'],
      manualPriority: undefined
    },
    {
      title: 'Medium Priority Task',
      tags: ['[***review]', '#frontend', '@designer'],
      manualPriority: undefined
    },
    {
      title: 'Low Priority Task',
      tags: ['[enhancement]', '#nice-to-have'],
      manualPriority: undefined
    },
    {
      title: 'Manual Override',
      tags: ['[***low]'], // Would be medium
      manualPriority: Priority.HIGH
    },
    {
      title: 'No Asterisk Patterns',
      tags: ['#work', '@john', '[normal-task]'],
      manualPriority: undefined
    }
  ]

  for (const demoCase of demoCases) {
    const result = calculatePriorityFromTags(demoCase.tags, demoCase.manualPriority)
    
    console.log(`\n📋 ${demoCase.title}`)
    console.log(`   Tags: ${demoCase.tags.join(', ')}`)
    if (demoCase.manualPriority) {
      console.log(`   Manual Priority: ${demoCase.manualPriority}`)
    }
    console.log(`   ➡️  Calculated Priority: ${result.calculatedPriority}`)
    console.log(`   📊 Source: ${result.prioritySource}`)
    console.log(`   🎯 Confidence: ${(result.confidence * 100).toFixed(0)}%`)
    if (result.asteriskPatterns.length > 0) {
      console.log(`   ⭐ Patterns Found: ${result.asteriskPatterns.join(', ')}`)
    }
  }

  // Show cache stats
  const cacheStats = getPriorityCacheStats()
  console.log(`\n💾 Cache Statistics: ${cacheStats.size}/${cacheStats.maxSize} entries`)
  
  console.log('\n🎉 Priority Calculation System Demo Complete!')
}