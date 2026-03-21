#!/usr/bin/env rust
//! Ping - Simple network ping utility

use anyhow::Result;
use clap::Parser;
use std::net::TcpStream;
use std::time::Duration;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Host to ping
    #[arg(required = true)]
    host: String,

    /// Port to check (default: 80 for HTTP)
    #[arg(short, long, default_value = "80")]
    port: u16,

    /// Number of pings
    #[arg(short, long, default_value = "4")]
    count: usize,

    /// Timeout in seconds
    #[arg(short, long, default_value = "2")]
    timeout: u64,
}

fn ping(host: &str, port: u16, timeout: Duration) -> Option<Duration> {
    let start = std::time::Instant::now();
    match TcpStream::connect_timeout(&format!("{}:{}", host, port).parse().ok()?, timeout) {
        Ok(_) => Some(start.elapsed()),
        Err(_) => None,
    }
}

fn main() -> Result<()> {
    let args = Args::parse();
    let timeout = Duration::from_secs(args.timeout);

    println!("Pinging {}:{} ({} pings)", args.host, args.port, args.count);
    println!();

    let mut success = 0;
    let mut total_time = Duration::from_secs(0);

    for i in 1..=args.count {
        if let Some(time) = ping(&args.host, args.port, timeout) {
            println!("Reply from {}: time={:?} (#{})", args.host, time, i);
            success += 1;
            total_time += time;
        } else {
            println!("Request timed out (#{}).", i);
        }
        
        if i < args.count {
            std::thread::sleep(Duration::from_secs(1));
        }
    }

    println!();
    println!("Statistics:");
    println!("  Sent: {}, Received: {}, Lost: {}", args.count, success, args.count - success);
    if success > 0 {
        println!("  Average: {:?}", total_time / success as u32);
    }

    Ok(())
}
