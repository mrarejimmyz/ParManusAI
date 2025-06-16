# LLM-Driven Planning System

## Overview
This module provides an intelligent planning system that creates comprehensive project plans, manages todo lists, and tracks task progress using LLM capabilities.

## Architecture

### Core Components

#### `analyzer.py`
**Responsibility**: Analyzes user requests and creates comprehensive plans using LLM.

**Key Features**:
- LLM-powered request analysis
- Comprehensive plan generation
- Context-aware planning
- Fallback planning when LLM unavailable

**Main Class**: `PlanAnalyzer`

**Methods**:
- `analyze_request(request)`: Analyzes request and creates plan
- `_create_fallback_plan(request)`: Creates basic plan without LLM
- `_parse_llm_response(response)`: Parses LLM response into structured plan

#### `generator.py`
**Responsibility**: Formats and validates plans into proper structures.

**Key Features**:
- Plan formatting and validation
- Status management
- Step prioritization
- Progress tracking

**Main Class**: `PlanGenerator`

**Methods**:
- `format_plan(plan)`: Formats plan into standard structure
- `validate_plan(plan)`: Validates plan completeness
- `update_status(plan, status)`: Updates plan status

#### `todo_manager.py`
**Responsibility**: Manages todo file creation, updates, and persistence.

**Key Features**:
- Todo file management
- Markdown formatting
- Progress tracking
- File I/O operations

**Main Class**: `TodoManager`

**Methods**:
- `create_todo_from_plan(plan)`: Creates todo file from plan
- `update_todo_status(task_id, status)`: Updates task status
- `get_todo_file_path()`: Returns todo file path
- `read_existing_todo()`: Reads current todo file

#### `main.py`
**Responsibility**: Main interface that coordinates all planning components.

**Key Features**:
- Clean public API
- Component coordination
- Error handling
- Backward compatibility

**Main Class**: `LLMDrivenPlanner`

**Public Methods**:
- `create_comprehensive_plan(request)`: Creates complete plan
- `update_plan_progress(task_id, status)`: Updates task progress
- `get_current_plan()`: Returns current active plan

## Usage

### Basic Usage
```python
from app.planning import LLMDrivenPlanner

# Initialize with LLM (optional)
planner = LLMDrivenPlanner(llm=your_llm)

# Create a plan
plan = await planner.create_comprehensive_plan("Build a web application")

# Update progress
await planner.update_plan_progress("task-1", "completed")
```

### Advanced Usage
```python
# Access individual components
from app.planning.analyzer import PlanAnalyzer
from app.planning.generator import PlanGenerator
from app.planning.todo_manager import TodoManager

# Create custom planning workflow
analyzer = PlanAnalyzer(llm)
generator = PlanGenerator()
todo_manager = TodoManager()

# Analyze request
plan = await analyzer.analyze_request("complex project")

# Format and validate
formatted_plan = generator.format_plan(plan)

# Create todo file
todo_manager.create_todo_from_plan(formatted_plan)
```

## Plan Structure

Plans follow a standardized structure:

```python
{
    "title": "Project Title",
    "description": "Detailed description",
    "steps": [
        {
            "id": "step-1",
            "title": "Step Title",
            "description": "Step description",
            "priority": "high|medium|low",
            "status": "pending|in_progress|completed",
            "estimated_time": "2 hours",
            "dependencies": ["step-0"]
        }
    ],
    "status": "pending|in_progress|completed",
    "created_at": "2025-06-16T09:00:00Z",
    "updated_at": "2025-06-16T09:00:00Z"
}
```

## Todo File Format

The system generates markdown todo files:

```markdown
# Project Title

## Description
Detailed project description

## Tasks

### High Priority
- [ ] Task 1 (2 hours) [step-1]
- [ ] Task 2 (1 hour) [step-2]

### Medium Priority
- [ ] Task 3 (30 minutes) [step-3]

### Low Priority
- [ ] Task 4 (15 minutes) [step-4]

## Progress
- Total Tasks: 4
- Completed: 0
- In Progress: 0
- Pending: 4
```

## Configuration

The planning system supports configuration options:

- **Todo file location**: Set custom todo file paths
- **Plan templates**: Configure plan formatting templates
- **LLM settings**: Configure LLM prompts and parameters
- **Status options**: Customize task status values

## Error Handling

Robust error handling includes:

- **LLM failures**: Fallback to template-based planning
- **File I/O errors**: Graceful handling of file operations
- **Plan validation**: Ensures plan completeness and consistency
- **Progress tracking**: Handles invalid status updates

## Features

### Intelligent Planning
- **Context Analysis**: LLM analyzes request context
- **Step Dependencies**: Automatic dependency detection
- **Time Estimation**: AI-powered time estimates
- **Priority Assignment**: Intelligent task prioritization

### Progress Management
- **Status Tracking**: Track task completion status
- **Progress Reports**: Generate progress summaries
- **Time Tracking**: Monitor actual vs estimated time
- **Dependency Management**: Handle task dependencies

### File Management
- **Auto-save**: Automatic todo file updates
- **Version Control**: Track plan changes over time
- **Backup**: Automatic backup of plan files
- **Export**: Export plans to various formats

## Backward Compatibility

The modular system maintains full backward compatibility through:
- `app/llm_planning.py` - Legacy interface wrapper
- Same public API as original monolithic version
- No breaking changes to existing code

## Testing

Individual components can be tested separately:

```python
# Test plan analyzer
python -m pytest tests/test_analyzer.py

# Test plan generator
python -m pytest tests/test_generator.py

# Test todo manager
python -m pytest tests/test_todo_manager.py
```

## Integration

The planning system integrates with:

- **Agent Core**: Used by main agent for task planning
- **Search System**: Plans can include search tasks
- **Tool System**: Plans can include tool usage
- **Memory System**: Plans stored in agent memory

## Benefits of Modular Design

1. **Single Responsibility**: Each module has one clear purpose
2. **Easy Debugging**: Isolate issues to specific components
3. **Independent Testing**: Test components in isolation
4. **Easier Maintenance**: Modify one aspect without affecting others
5. **Better Extensibility**: Add new planning strategies easily
6. **Code Reusability**: Components can be used independently
