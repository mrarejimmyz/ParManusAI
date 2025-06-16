# LLM-Driven Search System

## Overview
This module provides an intelligent, LLM-driven search system that dynamically selects optimal search strategies based on query analysis.

## Architecture

### Core Components

#### `strategy_analyzer.py`
**Responsibility**: Analyzes search queries using LLM to determine the best search strategy.

**Key Features**:
- LLM-powered query analysis
- Dynamic strategy selection
- Fallback strategies when LLM is unavailable
- Query preprocessing and optimization

**Main Class**: `SearchStrategyAnalyzer`

**Methods**:
- `analyze_query(query)`: Analyzes query and returns optimal strategy
- `_get_fallback_strategy(query)`: Provides fallback when LLM unavailable

#### `sources.py`
**Responsibility**: Implements individual search engine interfaces and result processing.

**Key Features**:
- Multiple search engine support (DuckDuckGo, Bing, Wikipedia, Academic)
- Unified result format
- Error handling and retry logic
- Rate limiting and timeout management

**Main Classes**: `SearchSources`

**Search Engines**:
- DuckDuckGo Web Search
- DuckDuckGo Instant Answers
- Bing Search (with API key)
- Wikipedia API
- Academic Search
- Local File Search

#### `executor.py`
**Responsibility**: Executes search strategies and manages result aggregation.

**Key Features**:
- Strategy execution coordination
- Result deduplication and ranking
- Performance monitoring
- Error recovery

**Main Class**: `SearchExecutor`

**Methods**:
- `execute_strategy(strategy, queries)`: Executes search strategy
- `_deduplicate_results(results)`: Removes duplicate results
- `_rank_results(results)`: Scores and ranks results

#### `main.py`
**Responsibility**: Main interface that coordinates all components.

**Key Features**:
- Clean public API
- Component coordination
- Logging and monitoring
- Backward compatibility

**Main Class**: `LLMDrivenSearch`

**Public Methods**:
- `search(query)`: Primary search interface
- `get_available_strategies()`: Lists available strategies

## Usage

### Basic Usage
```python
from app.search import LLMDrivenSearch

# Initialize with LLM (optional)
search = LLMDrivenSearch(llm=your_llm)

# Perform search
results = await search.search("your query here")
```

### Advanced Usage
```python
# Access individual components
from app.search.strategy_analyzer import SearchStrategyAnalyzer
from app.search.sources import SearchSources
from app.search.executor import SearchExecutor

# Analyze strategy
analyzer = SearchStrategyAnalyzer(llm)
strategy = await analyzer.analyze_query("complex query")

# Execute manually
executor = SearchExecutor()
results = await executor.execute_strategy(strategy, ["query"])
```

## Configuration

The search system supports various configuration options:

- **Timeout settings**: Configure per-engine timeouts
- **Result limits**: Set maximum results per engine
- **API keys**: Configure search engine API keys
- **Fallback behavior**: Configure LLM fallback strategies

## Error Handling

The system includes robust error handling:

- **Network timeouts**: Graceful handling of slow/unavailable services
- **API rate limits**: Automatic retry with backoff
- **LLM failures**: Fallback to rule-based strategies
- **Result processing**: Handles malformed or empty results

## Performance Features

- **Concurrent execution**: Multiple search engines run in parallel
- **Caching**: Results cached for repeated queries
- **Deduplication**: Intelligent removal of duplicate results
- **Result ranking**: AI-powered result scoring and ranking

## Backward Compatibility

The modular system maintains full backward compatibility through:
- `app/tool/optimized_bulletproof_search.py` - Legacy interface wrapper
- Same public API as original monolithic version
- No breaking changes to existing code

## Testing

Individual components can be tested separately:

```python
# Test strategy analyzer
python -m pytest tests/test_strategy_analyzer.py

# Test search sources
python -m pytest tests/test_sources.py

# Test executor
python -m pytest tests/test_executor.py
```

## Benefits of Modular Design

1. **Single Responsibility**: Each module has one clear purpose
2. **Easy Debugging**: Isolate issues to specific components
3. **Independent Testing**: Test components in isolation
4. **Easier Maintenance**: Modify one aspect without affecting others
5. **Better Extensibility**: Add new search engines or strategies easily
6. **Code Reusability**: Components can be used independently
