#!/usr/bin/env rust
//! DNS Lookup - Simple DNS resolver

use anyhow::Result;
use clap::Parser;
use std::net::ToSocketAddrs;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Domain to lookup
    #[arg(required = true)]
    domain: String,

    /// Output as JSON
    #[arg(short, long)]
    json: bool,
}

#[derive(serde::Serialize)]
struct DnsResult {
    domain: String,
    ips: Vec<String>,
}

fn main() -> Result<()> {
    let args = Args::parse();

    let ips: Vec<String> = match (&args.domain, 0).to_socket_addrs() {
        Ok(addrs) => addrs.map(|a| a.ip().to_string()).collect(),
        Err(e) => {
            eprintln!("DNS lookup failed: {}", e);
            Vec::new()
        }
    };

    let result = DnsResult {
        domain: args.domain.clone(),
        ips,
    };

    if args.json {
        println!("{}", serde_json::to_string_pretty(&result)?);
    } else {
        println!("DNS Lookup: {}", args.domain);
        println!("IP Addresses:");
        for ip in &result.ips {
            println!("  {}", ip);
        }
        if result.ips.is_empty() {
            println!("  (none found)");
        }
    }

    Ok(())
}
