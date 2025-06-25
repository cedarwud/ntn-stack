# NTN Stack Test Suite - Reorganized Structure

## 📁 Directory Structure

### Test Categories
```
reorganized/
├── unit/              # Unit tests (isolated component testing)
│   ├── backend/       # SimWorld backend unit tests
│   ├── frontend/      # SimWorld frontend unit tests
│   └── netstack/      # NetStack API unit tests
├── integration/       # Integration tests (service-to-service)
│   ├── backend/       # Backend service integration
│   ├── frontend/      # Frontend-backend integration
│   └── netstack/      # NetStack integration tests
├── e2e/              # End-to-end tests (full user workflows)
│   ├── backend/      # Backend E2E scenarios
│   ├── frontend/     # Frontend E2E scenarios
│   └── netstack/     # NetStack E2E scenarios
├── performance/       # Performance and load tests
│   ├── backend/      # Backend performance tests
│   ├── frontend/     # Frontend performance tests
│   └── netstack/     # NetStack performance tests
└── shared/           # Shared test utilities
    ├── utils/        # Test utilities and helpers
    ├── fixtures/     # Test data and fixtures
    └── configs/      # Test configurations
```

## 🧪 Test Types

### Unit Tests
- **Purpose**: Test individual components in isolation
- **Scope**: Single functions, classes, or modules
- **Dependencies**: Mock external dependencies
- **Execution**: Fast (< 1 second per test)

### Integration Tests
- **Purpose**: Test interactions between components
- **Scope**: API endpoints, service connections, database operations
- **Dependencies**: Real services where appropriate
- **Execution**: Medium speed (1-10 seconds per test)

### End-to-End Tests
- **Purpose**: Test complete user workflows
- **Scope**: Full application scenarios from UI to database
- **Dependencies**: Full system environment
- **Execution**: Slower (10+ seconds per test)

### Performance Tests
- **Purpose**: Test system performance and limits
- **Scope**: Load testing, stress testing, benchmarking
- **Dependencies**: Production-like environment
- **Execution**: Variable (can be very long)

## 🚀 Quick Start

### Run All Tests
```bash
make test
```

### Run by Category
```bash
make test-unit      # Fast unit tests
make test-integration  # Integration tests  
make test-e2e       # End-to-end tests
make test-performance  # Performance tests
```

### Run by Component
```bash
make test-backend   # All backend tests
make test-frontend  # All frontend tests
make test-netstack  # All netstack tests
```

## 📊 Test Coverage Targets

| Component | Unit Tests | Integration Tests | E2E Tests |
|-----------|------------|-------------------|-----------|
| Backend Domain Services | 90%+ | 80%+ | Key workflows |
| Frontend Components | 80%+ | 70%+ | Critical paths |
| NetStack APIs | 90%+ | 85%+ | Core functions |

## 🛠️ Test Utilities

### Available in `shared/utils/`
- `test_client.py` - HTTP test client helpers
- `mock_factories.py` - Test data factories
- `database_utils.py` - Database test utilities
- `container_utils.py` - Docker container helpers
- `environment_setup.py` - Environment management

### Available in `shared/fixtures/`
- `satellite_data.json` - Sample satellite TLE data
- `uav_scenarios.json` - UAV test scenarios
- `handover_events.json` - Handover test data

## 🐳 Docker Testing

Tests can be run in Docker containers for consistent environments:

```bash
make test-docker      # Run all tests in Docker
make test-docker-unit # Run unit tests in Docker only
```

## 🔧 Environment Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL (for integration tests)

### Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

### Docker Environment
```bash
docker-compose -f docker-compose.testing.yml up -d
```

## 📈 Reporting

Test results and coverage reports are generated in:
- `reports/unit/` - Unit test reports
- `reports/integration/` - Integration test reports
- `reports/e2e/` - E2E test reports
- `reports/performance/` - Performance test reports
- `reports/coverage/` - Code coverage reports

## 🏷️ Test Tags

Use pytest markers to categorize tests:
- `@pytest.mark.unit` - Unit test
- `@pytest.mark.integration` - Integration test
- `@pytest.mark.e2e` - End-to-end test
- `@pytest.mark.performance` - Performance test
- `@pytest.mark.slow` - Long-running test
- `@pytest.mark.critical` - Critical functionality test

## 🔍 Test Selection

Run specific test types:
```bash
pytest -m "unit and not slow"           # Fast unit tests only
pytest -m "integration and critical"    # Critical integration tests
pytest -m "not performance"             # Skip performance tests
```