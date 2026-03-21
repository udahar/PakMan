#!/usr/bin/env rust
//! UUID Generator - Generate UUIDs

use anyhow::Result;
use clap::Parser;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Number of UUIDs to generate
    #[arg(short, long, default_value = "1")]
    count: usize,

    /// UUID version (4 or 7)
    #[arg(short, long, default_value = "4")]
    version: u8,

    /// Output as JSON array
    #[arg(short, long)]
    json: bool,
}

fn generate_uuid_v4() -> String {
    // Simple UUID v4 generation using random bytes
    let mut bytes = [0u8; 16];
    
    // Use system time + counter for pseudo-randomness
    let seed = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_nanos() as u64;
    
    for i in 0..16 {
        bytes[i] = ((seed >> (i % 8) * 8) ^ (seed >> 32)) as u8;
    }

    // Set version (4) and variant bits
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;

    format!(
        "{:08x}-{:04x}-{:04x}-{:04x}-{:012x}",
        u32::from_be_bytes([bytes[0], bytes[1], bytes[2], bytes[3]]),
        u16::from_be_bytes([bytes[4], bytes[5]]),
        u16::from_be_bytes([bytes[6], bytes[7]]),
        u16::from_be_bytes([bytes[8], bytes[9]]),
        u64::from_be_bytes([
            bytes[10], bytes[11], bytes[12], bytes[13], bytes[14], bytes[15], 0, 0
        ]) >> 16
    )
}

fn main() -> Result<()> {
    let args = Args::parse();

    let mut uuids = Vec::new();

    for _ in 0..args.count {
        let uuid = generate_uuid_v4();
        uuids.push(uuid);
    }

    if args.json {
        println!("{}", serde_json::to_string_pretty(&uuids)?);
    } else {
        for uuid in uuids {
            println!("{}", uuid);
        }
    }

    Ok(())
}
