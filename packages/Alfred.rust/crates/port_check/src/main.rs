#!/usr/bin/env rust
//! Port Checker - Check if ports are open/in use

use anyhow::Result;
use clap::Parser;
use std::net::TcpListener;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Ports to check
    #[arg(required = true)]
    ports: Vec<u16>,

    /// Host to check (default: localhost)
    #[arg(short, long, default_value = "127.0.0.1")]
    host: String,

    /// Timeout in seconds
    #[arg(short, long, default_value = "1")]
    timeout: u64,
}

fn check_port(host: &str, port: u16, timeout: u64) -> bool {
    let addr = format!("{}:{}", host, port);
    
    // Try to bind - if it fails, port is in use
    match TcpListener::bind(&addr) {
        Ok(_) => true,   // Port is available
        Err(_) => false, // Port is in use
    }
}

fn main() -> Result<()> {
    let args = Args::parse();

    println!("Checking ports on {} (timeout: {}s)\n", args.host, args.timeout);
    println!("{:<10} {:<15} {}", "Port", "Status", "Service");
    println!("{}", "-".repeat(40));

    for port in &args.ports {
        let available = check_port(&args.host, *port, args.timeout);
        let status = if available { "AVAILABLE" } else { "IN USE" };
        let service = get_service_name(*port);
        
        println!("{:<10} {:<15} {}", port, status, service);
    }

    Ok(())
}

fn get_service_name(port: u16) -> &'static str {
    match port {
        80 => "HTTP",
        443 => "HTTPS",
        22 => "SSH",
        21 => "FTP",
        25 => "SMTP",
        53 => "DNS",
        110 => "POP3",
        143 => "IMAP",
        3306 => "MySQL",
        5432 => "PostgreSQL",
        6379 => "Redis",
        27017 => "MongoDB",
        8080 => "HTTP-Alt",
        11434 => "Ollama",
        _ => "Unknown",
    }
}
