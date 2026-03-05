use crate::types::{ErrorBody, ErrorDetail};

#[derive(Debug)]
pub enum GatewayError {
    BadRequest(String),
    UpstreamBadRequest(Option<u16>, String),
    UpstreamValidationError(Option<u16>, String),
    UpstreamError(Option<u16>, String),
    UpstreamUnreachable(String),
    UpstreamConnectTimeout(String),
    UpstreamReadTimeout(String),
    InternalError(String),
}

impl GatewayError {
    pub fn status_code(&self) -> u16 {
        match self {
            Self::BadRequest(_) => 400,
            Self::UpstreamBadRequest(_, _) => 400,
            Self::UpstreamValidationError(_, _) => 422,
            Self::UpstreamError(_, _) => 502,
            Self::UpstreamUnreachable(_) => 502,
            Self::UpstreamConnectTimeout(_) => 504,
            Self::UpstreamReadTimeout(_) => 504,
            Self::InternalError(_) => 500,
        }
    }

    pub fn error_code(&self) -> &str {
        match self {
            Self::BadRequest(_) => "BAD_REQUEST",
            Self::UpstreamBadRequest(_, _) => "UPSTREAM_BAD_REQUEST",
            Self::UpstreamValidationError(_, _) => "UPSTREAM_VALIDATION_ERROR",
            Self::UpstreamError(_, _) => "UPSTREAM_ERROR",
            Self::UpstreamUnreachable(_) => "UPSTREAM_UNREACHABLE",
            Self::UpstreamConnectTimeout(_) => "UPSTREAM_CONNECT_TIMEOUT",
            Self::UpstreamReadTimeout(_) => "UPSTREAM_READ_TIMEOUT",
            Self::InternalError(_) => "GATEWAY_INTERNAL_ERROR",
        }
    }

    pub fn message(&self) -> &str {
        match self {
            Self::BadRequest(m)
            | Self::UpstreamBadRequest(_, m)
            | Self::UpstreamValidationError(_, m)
            | Self::UpstreamError(_, m)
            | Self::UpstreamUnreachable(m)
            | Self::UpstreamConnectTimeout(m)
            | Self::UpstreamReadTimeout(m)
            | Self::InternalError(m) => m,
        }
    }

    pub fn upstream_status(&self) -> Option<u16> {
        match self {
            Self::UpstreamBadRequest(s, _)
            | Self::UpstreamValidationError(s, _)
            | Self::UpstreamError(s, _) => *s,
            _ => None,
        }
    }

    pub fn to_error_body(&self) -> ErrorBody {
        ErrorBody {
            error: ErrorDetail {
                code: self.error_code().to_string(),
                message: self.message().to_string(),
                upstream_status: self.upstream_status(),
            },
        }
    }
}

/// Map an upstream HTTP status code to a GatewayError.
/// Returns Ok(()) for 2xx status codes.
pub fn map_upstream_status(status: u16, body: &str) -> Result<(), GatewayError> {
    match status {
        200..=299 => Ok(()),
        400 => Err(GatewayError::UpstreamBadRequest(
            Some(status),
            body.to_string(),
        )),
        422 => Err(GatewayError::UpstreamValidationError(
            Some(status),
            body.to_string(),
        )),
        _ => Err(GatewayError::UpstreamError(
            Some(status),
            body.to_string(),
        )),
    }
}
