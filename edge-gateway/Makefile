.PHONY: build test clean build-spin deploy-spin deploy-akamai run-spin build-fastly build-workers build-lambda build-frontend

# ── Build ─────────────────────────────────────────────────────
build:
	cargo build --target wasm32-wasip1 --release

test:
	cargo test

clean:
	cargo clean
	rm -rf adapters/spin/static

# ── Frontend (build + copy to Spin static dir) ───────────────
build-frontend:
	cd ../frontend && npm install && npm run build
	mkdir -p adapters/spin/static
	cp -r ../frontend/dist/* adapters/spin/static/

# ── Spin (Akamai Functions) ──────────────────────────────────
build-spin: build-frontend
	cd adapters/spin && spin build

run-spin:
	cd adapters/spin && \
	SPIN_VARIABLE_GATEWAY_REGION=$${GATEWAY_REGION:-us-east-1} \
	spin up

deploy-spin:
	cd adapters/spin && \
	spin cloud deploy \
	  --variable "gateway_platform=Fermyon Cloud" \
	  --variable gateway_region=$${GATEWAY_REGION:-us-ord}

deploy-akamai:
	cd adapters/spin && \
	spin aka deploy --no-confirm \
	  --variable "gateway_platform=Akamai Functions" \
	  --variable gateway_region=$${GATEWAY_REGION:-us-ord}

# ── Fastly Compute ───────────────────────────────────────────
build-fastly:
	cargo build --target wasm32-wasip1 --release -p clipclap-gateway-fastly

deploy-fastly:
	cd adapters/fastly && fastly compute deploy --package ../../target/wasm32-wasip1/release/clipclap_gateway_fastly.wasm

# ── Cloudflare Workers ───────────────────────────────────────
build-workers:
	cargo build --target wasm32-unknown-unknown --release -p clipclap-gateway-workers

deploy-workers:
	cd adapters/workers && npx wrangler deploy

# ── AWS Lambda ───────────────────────────────────────────────
build-lambda:
	cd adapters/lambda && cargo lambda build --release --arm64

deploy-lambda:
	cd adapters/lambda && cargo lambda deploy --iam-role $${LAMBDA_ROLE:?Set LAMBDA_ROLE}
