//! CLI argument helpers

use clap::Parser;

/// Common arguments for all tools
#[derive(Parser, Debug)]
pub struct CommonArgs {
    /// Output as JSON
    #[arg(short, long, global = true)]
    pub json: bool,

    /// Verbose output
    #[arg(short, long, global = true)]
    pub verbose: bool,

    /// Quiet mode
    #[arg(short, long, global = true)]
    pub quiet: bool,
}

/// Validate that a path exists
pub fn validate_path_exists(path: &str) -> Result<(), String> {
    if !std::path::Path::new(path).exists() {
        return Err(format!("Path does not exist: {}", path));
    }
    Ok(())
}

/// Parse a duration string (e.g., "5s", "10m", "1h")
pub fn parse_duration(s: &str) -> Result<std::time::Duration, String> {
    let s = s.trim();
    
    if s.ends_with('s') {
        let num: u64 = s[..s.len()-1].parse()
            .map_err(|_| format!("Invalid duration: {}", s))?;
        Ok(std::time::Duration::from_secs(num))
    } else if s.ends_with('m') {
        let num: u64 = s[..s.len()-1].parse()
            .map_err(|_| format!("Invalid duration: {}", s))?;
        Ok(std::time::Duration::from_secs(num * 60))
    } else if s.ends_with('h') {
        let num: u64 = s[..s.len()-1].parse()
            .map_err(|_| format!("Invalid duration: {}", s))?;
        Ok(std::time::Duration::from_secs(num * 3600))
    } else {
        let num: u64 = s.parse()
            .map_err(|_| format!("Invalid duration: {}", s))?;
        Ok(std::time::Duration::from_secs(num))
    }
}
