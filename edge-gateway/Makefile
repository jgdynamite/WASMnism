.PHONY: build test clean build-spin deploy-spin run-spin

# ── Build ─────────────────────────────────────────────────────
build:
	cargo build --target wasm32-wasip1 --release

test:
	cargo test

clean:
	cargo clean

# ── Spin (Akamai Functions) ──────────────────────────────────
build-spin:
	cd adapters/spin && spin build

run-spin:
	cd adapters/spin && \
	SPIN_VARIABLE_INFERENCE_URL=$${INFERENCE_URL:?Set INFERENCE_URL} \
	SPIN_VARIABLE_GATEWAY_REGION=$${GATEWAY_REGION:-us-east-1} \
	spin up

deploy-spin:
	cd adapters/spin && \
	SPIN_VARIABLE_INFERENCE_URL=$${INFERENCE_URL:?Set INFERENCE_URL} \
	SPIN_VARIABLE_GATEWAY_REGION=$${GATEWAY_REGION:-us-east-1} \
	spin deploy
