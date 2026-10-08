# Windows without make: run the same commands from engine/ with `uv run ...`.
.PHONY: verify test check

verify:
	cd engine && uv run verify

test:
	cd engine && uv run pytest -q

check:
	cd engine && uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run pytest -q && uv run verify
