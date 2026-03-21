//! Common utilities for Rust command-line tools
//!
//! Provides shared functionality:
//! - Logging setup
//! - JSON output helpers
//! - CLI argument helpers
//! - Error handling

pub mod output;
pub mod logging;
pub mod cli;

pub use output::*;
pub use logging::*;
pub use cli::*;
