use anyhow::Result;
use spin_sdk::{
    http::{IntoResponse, Method, Params, Request, Response, Router},
    http_component, variables,
};
use uuid::Uuid;

use clipclap_gateway_core::{
    error::{map_upstream_status, GatewayError},
    handlers,
    types::{EchoRequest, GatewayConfig},
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

fn config() -> GatewayConfig {
    GatewayConfig {
        platform: "spin".into(),
        region: variables::get("gateway_region").unwrap_or_else(|_| "unknown".into()),
    }
}

fn request_id() -> String {
    Uuid::new_v4().to_string()
}

fn json_ok(body: &impl serde::Serialize, rid: &str, cfg: &GatewayConfig) -> Response {
    json_resp(200, body, rid, cfg)
}

fn json_resp(status: u16, body: &impl serde::Serialize, rid: &str, cfg: &GatewayConfig) -> Response {
    let bytes = serde_json::to_vec(body).unwrap_or_default();
    Response::builder()
        .status(status)
        .header("content-type", "application/json")
        .header("x-gateway-platform", &cfg.platform)
        .header("x-gateway-region", &cfg.region)
        .header("x-gateway-request-id", rid)
        .body(bytes)
        .build()
}

fn error_resp(err: &GatewayError, rid: &str, cfg: &GatewayConfig) -> Response {
    json_resp(err.status_code(), &err.to_error_body(), rid, cfg)
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

#[http_component]
async fn handle(req: Request) -> Response {
    let mut router = Router::new();
    router.get("/gateway/health", handle_health);
    router.post("/gateway/echo", handle_echo);
    router.post("/gateway/mock-classify", handle_mock_classify);
    router.post_async("/api/clip/classify", handle_proxy);
    router.post_async("/api/clap/classify", handle_proxy);
    router.any("/*", handle_not_found);
    router.handle_async(req).await
}

// ---------------------------------------------------------------------------
// Gateway-only handlers
// ---------------------------------------------------------------------------

fn handle_health(_req: Request, _params: Params) -> Result<impl IntoResponse> {
    let cfg = config();
    let rid = request_id();
    Ok(json_ok(&handlers::health(&cfg), &rid, &cfg))
}

fn handle_echo(req: Request, _params: Params) -> Result<impl IntoResponse> {
    let cfg = config();
    let rid = request_id();

    let echo_req: EchoRequest = match serde_json::from_slice(req.body()) {
        Ok(r) => r,
        Err(e) => {
            let err = GatewayError::BadRequest(format!("Invalid JSON: {e}"));
            return Ok(error_resp(&err, &rid, &cfg));
        }
    };

    if echo_req.labels.is_empty() || echo_req.labels.len() > 1000 {
        let err = GatewayError::BadRequest("labels must contain 1-1000 items".into());
        return Ok(error_resp(&err, &rid, &cfg));
    }
    if echo_req.nonce.len() > 256 {
        let err = GatewayError::BadRequest("nonce must be <=256 characters".into());
        return Ok(error_resp(&err, &rid, &cfg));
    }

    Ok(json_ok(&handlers::echo(&echo_req, &cfg, &rid), &rid, &cfg))
}

fn handle_mock_classify(req: Request, _params: Params) -> Result<impl IntoResponse> {
    let cfg = config();
    let rid = request_id();

    let body: EchoRequest = match serde_json::from_slice(req.body()) {
        Ok(r) => r,
        Err(e) => {
            let err = GatewayError::BadRequest(format!("Invalid JSON: {e}"));
            return Ok(error_resp(&err, &rid, &cfg));
        }
    };

    if body.labels.is_empty() || body.labels.len() > 1000 {
        let err = GatewayError::BadRequest("labels must contain 1-1000 items".into());
        return Ok(error_resp(&err, &rid, &cfg));
    }

    Ok(json_ok(&handlers::mock_classify(&body.labels), &rid, &cfg))
}

// ---------------------------------------------------------------------------
// Proxy handlers (forward to inference service)
// ---------------------------------------------------------------------------

async fn handle_proxy(req: Request, _params: Params) -> Result<impl IntoResponse> {
    let cfg = config();
    let rid = request_id();

    let inference_url = match variables::get("inference_url") {
        Ok(url) => url,
        Err(_) => {
            let err = GatewayError::InternalError("INFERENCE_URL not configured".into());
            return Ok(error_resp(&err, &rid, &cfg));
        }
    };

    let upstream_path = req.path().to_string();
    let upstream_uri = format!(
        "{}{}",
        inference_url.trim_end_matches('/'),
        upstream_path
    );

    let content_type = req
        .header("content-type")
        .and_then(|v| v.as_str())
        .unwrap_or("application/octet-stream")
        .to_string();

    let fwd_request_id = req
        .header("x-request-id")
        .and_then(|v| v.as_str())
        .unwrap_or(&rid)
        .to_string();

    let body = req.into_body();

    let outbound = Request::post(&upstream_uri, body)
        .header("content-type", &content_type)
        .header("x-request-id", &fwd_request_id)
        .build();

    let upstream_resp = match spin_sdk::http::send(outbound).await {
        Ok(resp) => resp,
        Err(_) => {
            let err =
                GatewayError::UpstreamUnreachable("Failed to reach inference service".into());
            return Ok(error_resp(&err, &rid, &cfg));
        }
    };

    let status = *upstream_resp.status();
    let resp_body = upstream_resp.into_body();

    let body_preview = String::from_utf8_lossy(&resp_body[..resp_body.len().min(256)]);
    if let Err(err) = map_upstream_status(status, &body_preview) {
        return Ok(error_resp(&err, &rid, &cfg));
    }

    Ok(Response::builder()
        .status(200)
        .header("content-type", "application/json")
        .header("x-gateway-platform", &cfg.platform)
        .header("x-gateway-region", &cfg.region)
        .header("x-gateway-request-id", &rid)
        .body(resp_body)
        .build())
}

// ---------------------------------------------------------------------------
// Catch-all
// ---------------------------------------------------------------------------

fn handle_not_found(_req: Request, _params: Params) -> Result<impl IntoResponse> {
    let cfg = config();
    let rid = request_id();
    let err = GatewayError::BadRequest("Not found".into());
    Ok(error_resp(&err, &rid, &cfg))
}
