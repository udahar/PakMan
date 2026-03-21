//! Logging setup utilities

use tracing_subscriber::{fmt, prelude::*, EnvFilter};

/// Initialize logging with the given default level
pub fn init_logging(default_level: &str) {
    tracing_subscriber::registry()
        .with(fmt::layer())
        .with(EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new(default_level)))
        .init();
}

/// Initialize logging for CLI tools (quiet by default)
pub fn init_cli_logging(verbose: bool) {
    let level = if verbose { "debug" } else { "info" };
    init_logging(level);
}
