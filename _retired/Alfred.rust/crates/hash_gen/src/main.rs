#!/usr/bin/env rust
//! Hash Generator - Generate MD5, SHA256, SHA512 hashes

use anyhow::Result;
use clap::Parser;
use md5::{Digest, Md5};
use sha2::{Sha256, Sha512};

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Input string to hash
    #[arg(required = true)]
    input: String,

    /// Hash algorithm (md5, sha256, sha512, all)
    #[arg(short, long, default_value = "all")]
    algorithm: String,
}

fn main() -> Result<()> {
    let args = Args::parse();

    let input = args.input.as_bytes();

    if args.algorithm == "md5" || args.algorithm == "all" {
        let mut hasher = Md5::new();
        hasher.update(input);
        let hash = hex::encode(hasher.finalize());
        println!("MD5:    {}", hash);
    }

    if args.algorithm == "sha256" || args.algorithm == "all" {
        let mut hasher = Sha256::new();
        hasher.update(input);
        let hash = hex::encode(hasher.finalize());
        println!("SHA256: {}", hash);
    }

    if args.algorithm == "sha512" || args.algorithm == "all" {
        let mut hasher = Sha512::new();
        hasher.update(input);
        let hash = hex::encode(hasher.finalize());
        println!("SHA512: {}", hash);
    }

    Ok(())
}
