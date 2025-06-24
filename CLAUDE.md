# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Commands
```bash
# Full setup with dependency installation and testing
python setup_and_test.py

# Development mode without external dependencies
python setup_and_test.py --offline

# Run integration tests only
python setup_and_test.py --test-only

# Start the bot locally
python start_bot.py

# Run individual component tests
python src/simple_module_test.py
python test_educational_guide.py
python test_performance_benchmark_system.py
```

### Deployment Commands
```bash
# Deploy to Render.com (auto-triggered on main branch push)
git push origin main

# Local production mode
ENVIRONMENT=production python start_bot.py
```

## Architecture Overview

### Core System Design
This is a **multi-layered educational AI bot** with sophisticated AI model orchestration:

**AI Integration Layer (`ai_handler.py`, `ai_integration_engine.py`)**
- Gemini-first strategy with ChatGPT fallback (1400 daily quota management)
- 4-dimensional code analysis (complexity, performance, security, readability)
- Google Drive-based usage tracking and user preference management

**Educational System (`educational_code_guide.py`, `code_history_manager.py`)**
- 10 programming languages with adaptive learning paths
- Complete execution history with growth analytics
- Real-time performance benchmarking and optimization suggestions

**Code Execution Environment (`online_code_executor.py`)**
- Judge0 API integration with local sandboxing fallback
- Multi-language support with individual security configurations
- AI-powered code review integration

**Content Analysis (`intelligent_content_analyzer.py`)**
- 8-category emotion analysis with Korean language specialization
- Multi-dimensional quality scoring with improvement suggestions
- Hybrid AI + rule-based analysis with batch processing

### Data Management Strategy
**Hybrid Cloud-Local Storage:**
- Critical data (homework, progress) → Google Drive API
- Cache and temporary data → Local JSON files
- Automatic synchronization with intelligent fallbacks

**Configuration Management:**
- Environment-driven feature flags in `config/settings.py`
- OFFLINE_MODE for development without external dependencies
- Runtime configuration updates through `get_config()` and `update_config()`

### Bot Command Architecture
The main bot (`src/bot.py`) implements 48+ commands organized by functionality:
- `/start`, `/help` - Basic bot operations
- `/homework`, `/submit`, `/progress` - Educational features
- `/calc`, `/solar` - Solar power calculations
- `/sentiment_*`, `/quality_*` - Content analysis commands
- `/code`, `/analyze`, `/benchmark` - Code execution and analysis

### AI Model Switching Logic
```python
# Primary: Gemini 2.5 Flash (1400 calls/day)
# Fallback: OpenAI GPT-4o (when quota exceeded)
# Emergency: Rule-based analysis (when both fail)
```

## Key Development Patterns

### Error Handling & Resilience
- **Graceful degradation:** OFFLINE_MODE when external services unavailable
- **Smart fallbacks:** AI model switching → rule-based analysis
- **Comprehensive logging:** Structured logging with error context

### Performance Optimization
- **TTL-based caching:** 1-2 hour cache with intelligent invalidation
- **Async processing:** All AI calls and external requests are async
- **Resource limits:** 512MB memory, 30s execution time constraints
- **Batch processing:** Multiple URL analysis with parallel execution

### Testing Strategy
The project uses a comprehensive testing approach:
- **Integration tests:** 96% success rate (13 tests)
- **Component tests:** Individual module testing with mocking
- **OFFLINE_MODE testing:** Full functionality without external dependencies

### Configuration Patterns
Environment variables are managed through multiple `.env` file locations:
```python
# Search order: config/.env → .env → src/.env
TELEGRAM_BOT_TOKEN, GEMINI_API_KEY, OPENAI_API_KEY
ADMIN_USER_ID, OFFLINE_MODE, ENVIRONMENT
```

Feature flags control system behavior:
```python
FEATURE_FLAGS = {
    'enable_ai_integration': not OFFLINE_MODE,
    'enable_advanced_sentiment': True,
    'enable_batch_processing': True,
    # ... see config/settings.py for full list
}
```

## Working with This Codebase

### Adding New Features
1. **New Telegram commands:** Add handlers in `src/bot.py` following existing patterns
2. **AI analysis features:** Extend `ai_integration_engine.py` with new analysis types
3. **Programming languages:** Add configurations to `online_code_executor.py`
4. **Educational content:** Expand curriculum in `educational_code_guide.py`

### Understanding Module Dependencies
- **`start_bot.py`** - Main entry point with comprehensive dependency checking
- **`error_handler.py`** - Centralized error handling and user help system
- **`user_auth_manager.py`** - User authentication and permission management
- **Google Drive modules** - Cloud storage integration for persistent data

### Development Environment Setup
Always start with `setup_and_test.py` which handles:
- Dependency installation and validation
- Environment configuration
- Integration testing
- OFFLINE_MODE setup for development

### Code Quality Standards
The codebase maintains high quality standards:
- **Type hints:** Comprehensive typing throughout
- **Async patterns:** Proper async/await for I/O operations
- **Configuration-driven:** Environment-based feature toggles
- **Structured logging:** Multiple log levels with contextual information
- **Dataclass usage:** Structured data with automatic serialization

### Key Files for Extension
- **`config/settings.py`** - Central configuration with environment adjustments
- **`src/bot.py`** - Main bot logic and command routing
- **`ai_handler.py`** - AI model orchestration and quota management
- **`online_code_executor.py`** - Code execution engine and language support

This is a production-ready educational platform with enterprise-grade architecture. Follow established patterns for consistency and leverage the extensive foundation already built.