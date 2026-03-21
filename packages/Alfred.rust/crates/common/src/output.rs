//! Output formatting utilities
//!
//! Provides consistent JSON and text output across all tools.

use serde::Serialize;

/// Print data as JSON to stdout
pub fn print_json<T: Serialize>(data: &T) -> Result<(), serde_json::Error> {
    let output = serde_json::to_string_pretty(data)?;
    println!("{}", output);
    Ok(())
}

/// Print data as compact JSON to stdout
pub fn print_json_compact<T: Serialize>(data: &T) -> Result<(), serde_json::Error> {
    let output = serde_json::to_string(data)?;
    println!("{}", output);
    Ok(())
}

/// Print a success message
pub fn print_success(message: &str) {
    eprintln!("✓ {}", message);
}

/// Print an error message
pub fn print_error(message: &str) {
    eprintln!("✗ Error: {}", message);
}

/// Print a warning message
pub fn print_warning(message: &str) {
    eprintln!("⚠ Warning: {}", message);
}

/// Standard output wrapper for tool results
#[derive(Serialize)]
pub struct ToolOutput<T: Serialize> {
    pub success: bool,
    pub data: Option<T>,
    pub error: Option<String>,
}

impl<T: Serialize> ToolOutput<T> {
    pub fn success(data: T) -> Self {
        Self {
            success: true,
            data: Some(data),
            error: None,
        }
    }

    pub fn error(message: String) -> Self {
        Self {
            success: false,
            data: None,
            error: Some(message),
        }
    }
}

/// Standard JSON output structure
#[derive(Serialize)]
pub struct JsonOutput {
    pub success: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
}

impl JsonOutput {
    pub fn success_json(data: serde_json::Value) -> Self {
        Self {
            success: true,
            data: Some(data),
            error: None,
        }
    }

    pub fn error_msg(message: String) -> Self {
        Self {
            success: false,
            data: None,
            error: Some(message),
        }
    }
}
