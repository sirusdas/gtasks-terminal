# Kilo Coding Rulebook - CORRECTED VERSION

## Overview
This rulebook establishes best practices for Kilo when developing modular, maintainable code with a focus on **enhancing existing files rather than creating redundant versions**. These guidelines ensure code quality, maintainability, and adherence to software engineering principles.

## Core Principles

### 1. **Modular Architecture First**
- **Single Responsibility Principle**: Each module/file should have one clear purpose
- **Separation of Concerns**: Different functionalities should be in separate modules
- **High Cohesion**: Related code should be grouped together
- **Loose Coupling**: Modules should minimize dependencies on each other

### 2. **File Enhancement vs. New File Creation - CRITICAL**
- **Enhance Existing Files First**: Always improve existing functionality in the original file before creating new files
- **NO "Enhanced" Versions**: Never create files like `enhanced_feature.py`, `super_feature.py`, or `feature_v2.py`
- **Refactor for Size**: If a file becomes too large, split it into logical modules within the same file namespace
- **Clear File Purpose**: Each file should have one clear, single purpose without duplication

## Anti-Patterns to Avoid

### ❌ BAD Examples (DO NOT DO):
```
❌ main_dashboard.py (original)
❌ enhanced_main_dashboard.py (redundant)
❌ super_enhanced_main_dashboard.py (more redundant)

❌ api_handlers.py (original)
❌ enhanced_api_handlers.py (redundant)

❌ data_manager.py (original)
❌ enhanced_data_manager.py (redundant)
```

### ✅ GOOD Examples (DO THIS):
```
✅ main_dashboard.py (enhanced with all features)

✅ api_handlers.py (enhanced with all API functionality)

✅ data_manager.py (enhanced with all data operations)
```

## Correct Enhancement Pattern

### Before (Bad Pattern):
```
# Don't do this:
# main_dashboard.py - basic functionality
# enhanced_main_dashboard.py - "enhanced" version
# super_enhanced_main_dashboard.py - "super enhanced" version

# This creates:
# ❌ Version confusion
# ❌ Maintenance nightmares  
# ❌ Code duplication
# ❌ Unclear which is "current"
```

### After (Good Pattern):
```
# Do this instead:
# main_dashboard.py - single, comprehensive implementation with all features

# Benefits:
# ✅ Clear single source of truth
# ✅ Easy maintenance
# ✅ No duplication
# ✅ Clear what the "current" version is
```

## Directory Structure Guidelines

### Standard Project Structure
```
project_root/
├── src/                    # Source code
│   ├── core/               # Core business logic
│   ├── commands/           # CLI commands
│   ├── models/             # Data models
│   ├── storage/            # Data persistence
│   ├── integrations/       # External services
│   ├── utils/              # Utility functions
│   ├── reports/            # Report generation
│   ├── ai/                 # AI-related functionality
│   └── ui/                 # User interface components
├── config/                 # Configuration files
├── examples/               # Usage examples
├── tests/                  # Test files
├── docs/                   # Documentation
└── scripts/                # Build/deployment scripts
```

### File Naming Conventions

#### Python Files
- **Modules**: `snake_case.py` - ONE FILE PER FEATURE
- **Classes**: Each class in appropriate module
- **Constants**: `UPPER_SNAKE_CASE.py`
- **Private modules**: `_private_module.py`
- **Test files**: `test_feature_name.py`

#### Configuration Files
- **YAML**: `feature_name_config.yaml`
- **JSON**: `settings.json`
- **Environment**: `.env.example`

#### Documentation Files
- **Feature docs**: `FEATURE_NAME.md`
- **API docs**: `API_REFERENCE.md`
- **Guides**: `USER_GUIDE.md`

## Enhancement Guidelines

### 1. **When to Enhance vs. Create**

#### Enhance Existing Files When:
- Adding new features to existing functionality
- Improving existing methods or classes
- Adding new API endpoints to existing API files
- Enhancing UI components in existing files
- Adding new data models to existing model files
- Expanding configuration options

#### Create New Files Only When:
- Adding completely new, unrelated features
- Creating entirely new command modules
- Implementing new data models for new functionality
- Adding new utility functions for new use cases
- Creating new integration modules for new services
- Adding completely new report types

### 2. **Proper Enhancement Pattern**

#### Step 1: Analyze Existing Code
```python
# Before enhancing, understand the current implementation
def existing_function():
    """Current implementation"""
    pass

# Identify what needs to be added
```

#### Step 2: Enhance in Place
```python
# GOOD: Enhance the existing function
def existing_function():
    """
    Enhanced implementation with additional features
    
    Now includes:
    - Feature A
    - Feature B
    - Better error handling
    """
    # Original functionality
    pass
    
    # New enhanced functionality
    pass
```

#### Step 3: Remove Redundant Files
```bash
# Remove any "enhanced" or "super" versions
rm enhanced_main_dashboard.py
rm super_enhanced_main_dashboard.py
rm enhanced_api_handlers.py
rm enhanced_data_manager.py
```

### 3. **Refactoring for Size**

If a file becomes too large (>500 lines), split it logically:

```python
# Instead of one huge file:
# main_dashboard.py (1000+ lines)

# Do this:
# main_dashboard.py (main orchestration)
# dashboard/components.py (UI components)
# dashboard/handlers.py (request handlers)
# dashboard/utils.py (dashboard utilities)
```

## Coding Standards

### 1. **Module Organization**

#### Enhanced File Structure Template
```python
"""
Enhanced Module Name

Comprehensive implementation with all features for the module.

Features:
    - Core functionality with enhancements
    - Advanced features integrated
    - Improved error handling
    - Extended configuration options
"""

# Standard library imports
import os
import sys
from typing import List, Dict, Optional

# Third-party imports
import click
import yaml

# Local imports
from ..core.base import BaseClass
from ..utils.helpers import helper_function

# Constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

class FeatureClass:
    """Enhanced main class with all features"""
    
    def __init__(self, config: Dict):
        self.config = config
        self._initialize()
        self._setup_enhanced_features()
    
    def _initialize(self):
        """Initialize core functionality"""
        pass
    
    def _setup_enhanced_features(self):
        """Setup enhanced features"""
        pass
    
    def public_method(self, param: str) -> bool:
        """Enhanced public API method with comprehensive documentation"""
        pass
    
    def _private_method(self):
        """Private method for internal logic"""
        pass

# Utility functions
def enhanced_utility_function(param1: int, param2: str) -> Dict:
    """Enhanced utility function with all features"""
    pass

# Module-level constants
SUPPORTED_FORMATS = ['json', 'yaml', 'csv']
```

### 2. **Function Design Principles**

#### Enhanced Function Template
```python
def enhanced_function(param1: Type1, param2: Type2 = default_value) -> ReturnType:
    """
    Enhanced function with comprehensive features.
    
    Features:
    - Input validation
    - Enhanced error handling
    - Logging
    - Performance optimization
    - Comprehensive documentation
    
    Args:
        param1: Description of param1
        param2: Description of param2 (optional)
    
    Returns:
        Enhanced return value with metadata
        
    Raises:
        SpecificError: When this condition occurs
        
    Example:
        >>> result = enhanced_function("test", param2="value")
        >>> print(result)
        expected_output
    """
    # Validate inputs with enhanced validation
    if not isinstance(param1, Type1):
        raise ValueError("param1 must be of type Type1")
    
    # Enhanced implementation with logging
    result = None
    
    try:
        # Business logic with enhanced features
        result = do_enhanced_something(param1, param2)
        
        # Post-processing
        result = enhance_result(result)
        
    except Exception as e:
        # Enhanced error handling with logging
        raise CustomError(f"Enhanced error handling: {str(e)}") from e
    
    # Validate output
    if result is None:
        raise RuntimeError("Enhanced function failed to produce result")
    
    return result
```

## Testing Guidelines

### 1. **Enhanced Test Organization**
```python
# tests/test_enhanced_feature.py
"""
Enhanced tests for the module with comprehensive coverage
"""

import pytest
from unittest.mock import Mock, patch
from src.gtasks_cli.core.feature_class import FeatureClass
from src.gtasks_cli.utils.exceptions import ProcessingError

class TestEnhancedFeatureClass:
    """Comprehensive test cases for enhanced features"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.config = {'test': True, 'enhanced_mode': True}
        self.feature = FeatureClass(self.config)
    
    def test_enhanced_functionality(self):
        """Test enhanced functionality"""
        result = self.feature.enhanced_method("test data")
        assert result['success'] is True
        assert 'enhanced_data' in result
    
    def test_enhanced_error_handling(self):
        """Test enhanced error handling"""
        with pytest.raises(ProcessingError):
            self.feature.enhanced_method("")
    
    def test_enhanced_configuration(self):
        """Test enhanced configuration loading"""
        assert self.feature.config['enhanced_mode'] is True
```

## Quality Assurance

### 1. **Enhanced Code Quality Checklist**
- [ ] All functions have comprehensive docstrings
- [ ] All classes have enhanced documentation
- [ ] Type hints are provided for all parameters
- [ ] Enhanced error handling is implemented
- [ ] Tests cover all enhanced functionality
- [ ] Configuration is externalized and enhanced
- [ ] Logging is implemented for enhanced features
- [ ] Code follows enhanced naming conventions
- [ ] Dependencies are minimized and optimized
- [ ] Documentation is updated with enhancements

### 2. **Performance Considerations for Enhanced Code**
- Use generators for large datasets
- Implement caching for enhanced features
- Minimize database queries with optimizations
- Use async/await for enhanced I/O operations
- Profile enhanced code for bottlenecks

### 3. **Security Guidelines for Enhanced Features**
- Validate all enhanced inputs
- Use parameterized queries for enhanced data
- Implement proper authentication for enhanced features
- Sanitize user data in enhanced interfaces
- Use environment variables for enhanced secrets
- Implement rate limiting for enhanced endpoints

## Migration and Evolution

### 1. **Enhanced Version Management**
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Maintain backward compatibility for enhanced features
- Document all breaking changes
- Provide migration guides for enhanced functionality

### 2. **Enhanced Deprecation Strategy**
- Mark deprecated functions with enhanced warnings
- Provide alternative implementations
- Maintain deprecated code for reasonable period
- Update documentation to reflect enhancements

### 3. **Refactoring Guidelines**
- Enhance existing modules instead of creating new ones
- Remove redundant files during refactoring
- Provide clear migration paths
- Update tests for enhanced code

## Summary

This corrected rulebook establishes Kilo's approach to enhancing existing code rather than creating redundant versions. Key principles include:

1. **Single Source of Truth**: Each feature has one clear implementation
2. **Enhancement Over Duplication**: Improve existing files rather than creating new versions
3. **Clear Enhancement Path**: Logical progression of features within single files
4. **Comprehensive Testing**: Test all enhanced functionality
5. **Quality Assurance**: Consistent enhanced code quality standards

## Anti-Redundancy Rule

**NEVER create files with names like:**
- `enhanced_*`
- `super_*` 
- `*_v2`
- `*_new`
- `*_improved`

**ALWAYS enhance the original file directly.**

By following these guidelines, Kilo will consistently produce high-quality, maintainable code without the redundancy anti-patterns that create maintenance nightmares.