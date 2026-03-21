#!/usr/bin/env rust
//! Random Generator - Generate random strings, numbers, bytes

use anyhow::Result;
use clap::Parser;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Type of random data (string, number, bytes, password)
    #[arg(short, long, default_value = "string")]
    r#type: String,

    /// Length of output
    #[arg(short, long, default_value = "16")]
    length: usize,

    /// Minimum value (for numbers)
    #[arg(short, long)]
    min: Option<i64>,

    /// Maximum value (for numbers)
    #[arg(short, long)]
    max: Option<i64>,

    /// Include special characters (for passwords)
    #[arg(short, long)]
    special: bool,

    /// Count of items to generate
    #[arg(short, long, default_value = "1")]
    count: usize,
}

fn generate_random_bytes(len: usize) -> Vec<u8> {
    let mut bytes = Vec::with_capacity(len);
    let seed = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_nanos() as u64;

    for i in 0..len {
        bytes.push(((seed >> (i % 8) * 8) ^ (seed >> 32)) as u8);
    }
    bytes
}

fn generate_random_string(len: usize, special: bool) -> String {
    let chars = if special {
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    } else {
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    };

    let bytes = generate_random_bytes(len);
    bytes
        .iter()
        .map(|&b| chars.as_bytes()[b as usize % chars.len()] as char)
        .collect()
}

fn generate_password(len: usize) -> String {
    // Ensure at least one of each type
    let lowercase = "abcdefghijklmnopqrstuvwxyz";
    let uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    let digits = "0123456789";
    let special = "!@#$%^&*()_+-=[]{}|;:,.<>?";
    let all = format!("{}{}{}{}", lowercase, uppercase, digits, special);

    let mut password = String::with_capacity(len);
    
    // Add one of each required type
    let bytes = generate_random_bytes(4);
    password.push(lowercase.chars().nth(bytes[0] as usize % lowercase.len()).unwrap());
    password.push(uppercase.chars().nth(bytes[1] as usize % uppercase.len()).unwrap());
    password.push(digits.chars().nth(bytes[2] as usize % digits.len()).unwrap());
    password.push(special.chars().nth(bytes[3] as usize % special.len()).unwrap());

    // Fill the rest
    for i in 4..len {
        let byte = generate_random_bytes(1)[0];
        password.push(all.chars().nth(byte as usize % all.len()).unwrap());
    }

    // Shuffle (simple version)
    let mut chars: Vec<char> = password.chars().collect();
    for i in (1..chars.len()).rev() {
        let j = (generate_random_bytes(1)[0] as usize) % (i + 1);
        chars.swap(i, j);
    }

    chars.into_iter().collect()
}

fn main() -> Result<()> {
    let args = Args::parse();

    for _ in 0..args.count {
        match args.type.as_str() {
            "string" | "str" => {
                println!("{}", generate_random_string(args.length, args.special));
            }
            "password" | "pass" => {
                println!("{}", generate_password(args.length));
            }
            "number" | "num" => {
                let min = args.min.unwrap_or(0);
                let max = args.max.unwrap_or(100);
                let bytes = generate_random_bytes(8);
                let num = u64::from_be_bytes(bytes.try_into().unwrap());
                let range = (max - min + 1) as u64;
                let result = min + (num % range) as i64;
                println!("{}", result);
            }
            "bytes" => {
                let bytes = generate_random_bytes(args.length);
                println!("{:02x?}", bytes);
            }
            "hex" => {
                let bytes = generate_random_bytes(args.length / 2);
                println!("{}", hex::encode(bytes));
            }
            _ => {
                eprintln!("Unknown type: {}", args.type);
                eprintln!("Valid types: string, password, number, bytes, hex");
            }
        }
    }

    Ok(())
}
