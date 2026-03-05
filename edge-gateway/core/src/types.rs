use serde::{Deserialize, Serialize};

// ---------------------------------------------------------------------------
// Upstream classification schemas (must match ClipClap exactly)
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClassificationResult {
    pub label: String,
    pub score: f64,
    pub similarity: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InferenceMetrics {
    pub model_load_ms: f64,
    pub input_encoding_ms: f64,
    pub text_encoding_ms: f64,
    pub similarity_ms: f64,
    pub total_inference_ms: f64,
    pub num_candidates: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClassificationResponse {
    pub results: Vec<ClassificationResult>,
    pub metrics: InferenceMetrics,
}

// ---------------------------------------------------------------------------
// Gateway-only endpoint types
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthResponse {
    pub status: String,
    pub platform: String,
    pub region: String,
    pub timestamp_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EchoRequest {
    pub labels: Vec<String>,
    pub nonce: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EchoResponse {
    pub echo: EchoContent,
    pub gateway: GatewayInfo,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EchoContent {
    pub labels: Vec<String>,
    pub nonce: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GatewayInfo {
    pub platform: String,
    pub region: String,
    pub timestamp_ms: u64,
    pub request_id: String,
}

// ---------------------------------------------------------------------------
// Gateway metadata envelope (optional wrapper for proxy responses)
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GatewayEnvelope {
    pub gateway: GatewayMetadata,
    pub upstream: ClassificationResponse,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GatewayMetadata {
    pub platform: String,
    pub region: String,
    pub cold_start: bool,
    pub gateway_latency_ms: f64,
    pub upstream_latency_ms: f64,
}

// ---------------------------------------------------------------------------
// Error response
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorBody {
    pub error: ErrorDetail,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorDetail {
    pub code: String,
    pub message: String,
    pub upstream_status: Option<u16>,
}

// ---------------------------------------------------------------------------
// Runtime config passed into handlers by the adapter
// ---------------------------------------------------------------------------

#[derive(Debug, Clone)]
pub struct GatewayConfig {
    pub platform: String,
    pub region: String,
}
