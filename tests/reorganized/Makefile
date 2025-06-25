# NTN Stack Test Suite - Reorganized Structure
# Comprehensive testing with clear separation of concerns

.PHONY: help install test test-unit test-integration test-e2e test-performance
.PHONY: test-backend test-frontend test-netstack test-critical test-smoke
.PHONY: test-docker test-venv coverage report clean
.PHONY: setup-docker setup-venv verify-env migrate-old-tests

# Colors for output
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
CYAN=\033[0;36m
BOLD=\033[1m
NC=\033[0m # No Color

# Default target
help:
	@echo "$(CYAN)$(BOLD)🧪 NTN Stack Test Suite - Reorganized$(NC)"
	@echo "=================================================="
	@echo ""
	@echo "$(GREEN)📋 Quick Commands:$(NC)"
	@echo "  $(YELLOW)install$(NC)          - Install test dependencies"
	@echo "  $(YELLOW)test$(NC)             - Run all tests (recommended)"
	@echo "  $(YELLOW)test-critical$(NC)    - Run only critical tests"
	@echo "  $(YELLOW)test-smoke$(NC)       - Run smoke tests"
	@echo "  $(YELLOW)coverage$(NC)         - Run tests with coverage report"
	@echo ""
	@echo "$(GREEN)🎯 Test Categories:$(NC)"
	@echo "  $(BLUE)test-unit$(NC)        - Unit tests (fast, isolated)"
	@echo "  $(BLUE)test-integration$(NC) - Integration tests (service-to-service)"
	@echo "  $(BLUE)test-e2e$(NC)         - End-to-end tests (full workflows)"
	@echo "  $(BLUE)test-performance$(NC) - Performance and load tests"
	@echo ""
	@echo "$(GREEN)📦 Component Tests:$(NC)"
	@echo "  $(BLUE)test-backend$(NC)     - SimWorld backend tests"
	@echo "  $(BLUE)test-frontend$(NC)    - SimWorld frontend tests"
	@echo "  $(BLUE)test-netstack$(NC)    - NetStack API tests"
	@echo ""
	@echo "$(GREEN)🐳 Environment Options:$(NC)"
	@echo "  $(BLUE)test-docker$(NC)      - Run tests in Docker containers"
	@echo "  $(BLUE)test-venv$(NC)        - Run tests in virtual environment"
	@echo "  $(BLUE)setup-docker$(NC)     - Setup Docker test environment"
	@echo "  $(BLUE)setup-venv$(NC)       - Setup virtual environment"
	@echo ""
	@echo "$(GREEN)🛠️ Utilities:$(NC)"
	@echo "  $(BLUE)verify-env$(NC)       - Verify test environment"
	@echo "  $(BLUE)migrate-old-tests$(NC) - Migrate tests from old structure"
	@echo "  $(BLUE)report$(NC)           - Generate test reports"
	@echo "  $(BLUE)clean$(NC)            - Clean test artifacts"

# ============================================================================
# Installation and Setup
# ============================================================================

install:
	@echo "$(YELLOW)📦 Installing test dependencies...$(NC)"
	@pip install -q pytest pytest-asyncio pytest-html pytest-cov pytest-xdist
	@pip install -q httpx aiohttp
	@pip install -q -r ../requirements.txt
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

setup-venv:
	@echo "$(YELLOW)🐍 Setting up virtual environment...$(NC)"
	@python3 -m venv ../venv
	@../venv/bin/pip install --upgrade pip
	@../venv/bin/pip install -r ../requirements.txt
	@../venv/bin/pip install pytest pytest-asyncio pytest-html pytest-cov pytest-xdist httpx aiohttp
	@mkdir -p ../reports/{unit,integration,e2e,performance,coverage}
	@echo "$(GREEN)✅ Virtual environment setup complete$(NC)"
	@echo "$(CYAN)To activate: source ../venv/bin/activate$(NC)"

setup-docker:
	@echo "$(YELLOW)🐳 Setting up Docker test environment...$(NC)"
	@docker-compose -f ../docker-compose.testing.yml build
	@docker-compose -f ../docker-compose.testing.yml up -d
	@echo "$(GREEN)✅ Docker test environment ready$(NC)"

verify-env:
	@echo "$(YELLOW)🔍 Verifying test environment...$(NC)"
	@python3 -c "import pytest, httpx, asyncio; print('✅ Python dependencies OK')" || (echo "$(RED)❌ Missing Python dependencies$(NC)" && exit 1)
	@ls -la ../reports/ >/dev/null 2>&1 && echo "✅ Reports directory exists" || echo "❌ Reports directory missing"
	@echo "$(CYAN)Environment verification complete$(NC)"

# ============================================================================
# Test Execution
# ============================================================================

# Run all tests with intelligent ordering
test: verify-env
	@echo "$(YELLOW)🚀 Running comprehensive test suite...$(NC)"
	@echo "$(CYAN)Phase 1: Critical tests (must pass)$(NC)"
	@pytest -m "critical" --tb=short -v || (echo "$(RED)❌ Critical tests failed - stopping$(NC)" && exit 1)
	@echo "$(GREEN)✅ Critical tests passed$(NC)"
	@echo "$(CYAN)Phase 2: Unit tests$(NC)"
	@pytest unit/ -v --tb=short
	@echo "$(CYAN)Phase 3: Integration tests$(NC)"
	@pytest integration/ -v --tb=short
	@echo "$(CYAN)Phase 4: E2E tests$(NC)"
	@pytest e2e/ -v --tb=short
	@echo "$(GREEN)✅ All test phases completed$(NC)"

# Test by category
test-unit: verify-env
	@echo "$(BLUE)🔧 Running unit tests...$(NC)"
	@pytest unit/ -v --tb=short --durations=10

test-integration: verify-env
	@echo "$(BLUE)🔗 Running integration tests...$(NC)"
	@pytest integration/ -v --tb=short --durations=10

test-e2e: verify-env
	@echo "$(BLUE)🎭 Running end-to-end tests...$(NC)"
	@pytest e2e/ -v --tb=short --durations=10

test-performance: verify-env
	@echo "$(BLUE)⚡ Running performance tests...$(NC)"
	@pytest performance/ -v --tb=short --durations=20

# Test by component
test-backend: verify-env
	@echo "$(CYAN)🖥️ Running backend tests...$(NC)"
	@pytest -m "backend" -v --tb=short

test-frontend: verify-env
	@echo "$(CYAN)🌐 Running frontend tests...$(NC)"
	@pytest -m "frontend" -v --tb=short

test-netstack: verify-env
	@echo "$(CYAN)📡 Running NetStack tests...$(NC)"
	@pytest -m "netstack" -v --tb=short

# Special test categories
test-critical: verify-env
	@echo "$(RED)🚨 Running critical tests only...$(NC)"
	@pytest -m "critical" -v --tb=short

test-smoke: verify-env
	@echo "$(YELLOW)💨 Running smoke tests...$(NC)"
	@pytest -m "smoke or critical" -v --tb=short

test-fast: verify-env
	@echo "$(GREEN)⚡ Running fast tests only...$(NC)"
	@pytest -m "unit and not slow" -v --tb=short

# ============================================================================
# Environment-Specific Testing
# ============================================================================

test-docker: setup-docker
	@echo "$(BLUE)🐳 Running tests in Docker environment...$(NC)"
	@docker-compose -f ../docker-compose.testing.yml exec test-runner pytest . -v --tb=short
	@echo "$(GREEN)✅ Docker tests completed$(NC)"

test-venv:
	@echo "$(BLUE)🐍 Running tests in virtual environment...$(NC)"
	@if [ ! -d "../venv" ]; then $(MAKE) setup-venv; fi
	@../venv/bin/pytest . -v --tb=short
	@echo "$(GREEN)✅ Virtual environment tests completed$(NC)"

# ============================================================================
# Coverage and Reporting
# ============================================================================

coverage: verify-env
	@echo "$(YELLOW)📊 Running tests with coverage analysis...$(NC)"
	@pytest . --cov=. --cov-report=html:../reports/coverage/html --cov-report=term-missing --cov-report=xml:../reports/coverage.xml -v
	@echo "$(GREEN)✅ Coverage report generated$(NC)"
	@echo "$(CYAN)📄 HTML Report: file://$(PWD)/../reports/coverage/html/index.html$(NC)"

coverage-unit: verify-env
	@echo "$(YELLOW)📊 Unit test coverage...$(NC)"
	@pytest unit/ --cov=unit --cov-report=html:../reports/coverage/unit_html --cov-report=term-missing

coverage-integration: verify-env
	@echo "$(YELLOW)📊 Integration test coverage...$(NC)"
	@pytest integration/ --cov=integration --cov-report=html:../reports/coverage/integration_html --cov-report=term-missing

report:
	@echo "$(YELLOW)📋 Generating comprehensive test report...$(NC)"
	@python3 shared/utils/generate_report.py
	@echo "$(GREEN)✅ Test report generated$(NC)"

# ============================================================================
# Parallel and Advanced Testing
# ============================================================================

test-parallel: verify-env
	@echo "$(YELLOW)⚡ Running tests in parallel...$(NC)"
	@pytest . -n auto --tb=short -v

test-verbose: verify-env
	@echo "$(YELLOW)📝 Running tests with verbose output...$(NC)"
	@pytest . -v -s --tb=long

test-failed: verify-env
	@echo "$(YELLOW)🔄 Re-running failed tests...$(NC)"
	@pytest --lf -v --tb=short

test-debug: verify-env
	@echo "$(YELLOW)🐛 Running tests in debug mode...$(NC)"
	@pytest --pdb -v -s

# ============================================================================
# Migration and Maintenance
# ============================================================================

migrate-old-tests:
	@echo "$(YELLOW)📦 Migrating tests from old structure...$(NC)"
	@python3 shared/utils/migrate_tests.py
	@echo "$(GREEN)✅ Test migration completed$(NC)"

validate-structure:
	@echo "$(YELLOW)🔍 Validating test structure...$(NC)"
	@python3 shared/utils/validate_structure.py
	@echo "$(GREEN)✅ Structure validation completed$(NC)"

# ============================================================================
# Cleanup
# ============================================================================

clean:
	@echo "$(YELLOW)🧹 Cleaning test artifacts...$(NC)"
	@rm -rf .pytest_cache/ __pycache__/ .coverage
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@rm -f ../reports/*.xml ../reports/*.log
	@echo "$(GREEN)✅ Cleanup completed$(NC)"

clean-reports:
	@echo "$(YELLOW)🗑️ Cleaning test reports...$(NC)"
	@rm -rf ../reports/*/
	@mkdir -p ../reports/{unit,integration,e2e,performance,coverage}
	@echo "$(GREEN)✅ Reports cleaned$(NC)"

clean-all: clean clean-reports
	@echo "$(YELLOW)🧽 Deep cleaning all test artifacts...$(NC)"
	@docker-compose -f ../docker-compose.testing.yml down -v 2>/dev/null || true
	@rm -rf ../venv/ 2>/dev/null || true
	@echo "$(GREEN)✅ Deep clean completed$(NC)"

# ============================================================================
# CI/CD Integration
# ============================================================================

test-ci: verify-env
	@echo "$(YELLOW)🤖 Running CI/CD test suite...$(NC)"
	@pytest . --tb=short --junitxml=../reports/junit.xml --html=../reports/test_report.html --self-contained-html -v
	@echo "$(GREEN)✅ CI/CD tests completed$(NC)"

test-production-ready: verify-env
	@echo "$(YELLOW)🚀 Running production readiness tests...$(NC)"
	@pytest -m "critical or smoke" --tb=short -v
	@pytest performance/ --tb=short -v
	@echo "$(GREEN)✅ Production readiness verified$(NC)"

# ============================================================================
# Development Helpers
# ============================================================================

watch:
	@echo "$(YELLOW)👀 Watching for changes and running tests...$(NC)"
	@while true; do \
		inotifywait -r -e modify,create,delete . --exclude="(__pycache__|\.pyc|\.git)" 2>/dev/null; \
		echo "$(CYAN)🔄 Change detected, running fast tests...$(NC)"; \
		pytest -m "unit and not slow" --tb=line -q; \
	done

test-random:
	@echo "$(YELLOW)🎲 Running tests in random order...$(NC)"
	@pytest . --random-order --tb=short -v

benchmark:
	@echo "$(YELLOW)📈 Running benchmark tests...$(NC)"
	@pytest performance/ --benchmark-only --benchmark-sort=mean -v