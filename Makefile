TESTS = tests/unit
INTEGRATIONTESTS = $(wildcard tests/integration/test_*.py)
export PYTHONPATH := .
PYTHON = python3
PYTEST = pytest

test: unit-test integration-test

.PHONY: runtest $(TESTS) runintegrationtest $(INTEGRATIONTESTS)

unit-test: $(TESTS)

$(TESTS):
	@echo "\n** Running test $@"
	@${PYTEST} $@

integration-test: $(INTEGRATIONTESTS)

$(INTEGRATIONTESTS):
	@echo "\n** Running integration test $@"
	@${PYTHON} $@

pytest:
	@${PYTEST}

clean:
	@find -name "*~" -delete
	@find -name "*.pyc" -delete
	@find -name "__pycache__" -delete
	@rm -rf build/
