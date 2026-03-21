#!/usr/bin/env rust
//! Password Strength Checker

use anyhow::Result;
use clap::Parser;
use serde::Serialize;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Password to check (or - for stdin)
    #[arg(required = true)]
    password: String,

    /// Output as JSON
    #[arg(short, long)]
    json: bool,
}

#[derive(Serialize)]
struct PasswordReport {
    password: String,
    length: usize,
    score: u8,
    strength: String,
    has_uppercase: bool,
    has_lowercase: bool,
    has_digit: bool,
    has_special: bool,
    issues: Vec<String>,
    suggestions: Vec<String>,
}

fn check_password(password: &str) -> PasswordReport {
    let mut issues = Vec::new();
    let mut suggestions = Vec::new();
    let mut score = 0u8;

    let has_uppercase = password.chars().any(|c| c.is_ascii_uppercase());
    let has_lowercase = password.chars().any(|c| c.is_ascii_lowercase());
    let has_digit = password.chars().any(|c| c.is_ascii_digit());
    let has_special = password.chars().any(|c| !c.is_alphanumeric());
    let length = password.len();

    // Length scoring
    if length >= 8 {
        score += 1;
    }
    if length >= 12 {
        score += 1;
    }
    if length >= 16 {
        score += 1;
    }
    if length < 8 {
        issues.push("Password is too short (minimum 8 characters)".to_string());
        suggestions.push("Use at least 12 characters".to_string());
    }

    // Character variety scoring
    if has_uppercase {
        score += 1;
    } else {
        issues.push("Missing uppercase letters".to_string());
        suggestions.push("Add uppercase letters (A-Z)".to_string());
    }

    if has_lowercase {
        score += 1;
    } else {
        issues.push("Missing lowercase letters".to_string());
        suggestions.push("Add lowercase letters (a-z)".to_string());
    }

    if has_digit {
        score += 1;
    } else {
        issues.push("Missing digits".to_string());
        suggestions.push("Add numbers (0-9)".to_string());
    }

    if has_special {
        score += 1;
    } else {
        issues.push("Missing special characters".to_string());
        suggestions.push("Add special characters (!@#$%^&*)".to_string());
    }

    // Common patterns
    let common_patterns = ["password", "123456", "qwerty", "admin", "letmein"];
    let lower_pass = password.to_lowercase();
    for pattern in &common_patterns {
        if lower_pass.contains(pattern) {
            issues.push(format!("Contains common pattern: {}", pattern));
            suggestions.push("Avoid common passwords and patterns".to_string());
            score = score.saturating_sub(2);
        }
    }

    // Repeated characters
    if password.chars().collect::<Vec<_>>().windows(3).any(|w| w[0] == w[1] && w[1] == w[2]) {
        issues.push("Contains repeated characters".to_string());
        suggestions.push("Avoid repeated characters".to_string());
    }

    let strength = match score {
        0..=2 => "Very Weak".to_string(),
        3..=4 => "Weak".to_string(),
        5..=6 => "Moderate".to_string(),
        7..=8 => "Strong".to_string(),
        _ => "Very Strong".to_string(),
    };

    PasswordReport {
        password: "*".repeat(password.len()),
        length,
        score,
        strength,
        has_uppercase,
        has_lowercase,
        has_digit,
        has_special,
        issues,
        suggestions,
    }
}

fn main() -> Result<()> {
    let args = Args::parse();

    let password = if args.password == "-" {
        let mut buffer = String::new();
        std::io::stdin().read_line(&mut buffer)?;
        buffer.trim().to_string()
    } else {
        args.password
    };

    let report = check_password(&password);

    if args.json {
        println!("{}", serde_json::to_string_pretty(&report)?);
    } else {
        println!("Password Strength Report");
        println!("========================");
        println!("Length: {} characters", report.length);
        println!("Score: {}/10", report.score);
        println!("Strength: {}", report.strength);
        println!();
        println!("Character Types:");
        println!("  Uppercase: {}", if report.has_uppercase { "✓" } else { "✗" });
        println!("  Lowercase: {}", if report.has_lowercase { "✓" } else { "✗" });
        println!("  Digits: {}", if report.has_digit { "✓" } else { "✗" });
        println!("  Special: {}", if report.has_special { "✓" } else { "✗" });
        
        if !report.issues.is_empty() {
            println!("\nIssues:");
            for issue in &report.issues {
                println!("  • {}", issue);
            }
        }
        
        if !report.suggestions.is_empty() {
            println!("\nSuggestions:");
            for suggestion in &report.suggestions {
                println!("  • {}", suggestion);
            }
        }
    }

    Ok(())
}
