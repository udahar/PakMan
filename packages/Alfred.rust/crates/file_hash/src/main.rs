#!/usr/bin/env rust
//! File Hash Generator - Generate MD5, SHA256 hashes for files

use anyhow::Result;
use clap::Parser;
use md5::{Digest, Md5};
use sha2::Sha256;
use std::fs::File;
use std::io::{BufReader, Read};
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Files to hash
    #[arg(required = true)]
    files: Vec<PathBuf>,

    /// Hash algorithm (md5, sha256, both)
    #[arg(short, long, default_value = "both")]
    algorithm: String,

    /// Recursive directory scan
    #[arg(short, long)]
    recursive: bool,
}

fn compute_hash(path: &PathBuf, algorithm: &str) -> Result<(Option<String>, Option<String>)> {
    let file = File::open(path)?;
    let mut reader = BufReader::new(file);
    let mut buffer = [0u8; 8192];

    let mut md5_hash = None;
    let mut sha256_hash = None;

    if algorithm == "md5" || algorithm == "both" {
        let mut hasher = Md5::new();
        let mut file = File::open(path)?;
        while let Ok(n) = file.read(&mut buffer) {
            if n == 0 {
                break;
            }
            hasher.update(&buffer[..n]);
        }
        md5_hash = Some(hex::encode(hasher.finalize()));
    }

    if algorithm == "sha256" || algorithm == "both" {
        let mut hasher = Sha256::new();
        let mut file = File::open(path)?;
        while let Ok(n) = file.read(&mut buffer) {
            if n == 0 {
                break;
            }
            hasher.update(&buffer[..n]);
        }
        sha256_hash = Some(hex::encode(hasher.finalize()));
    }

    Ok((md5_hash, sha256_hash))
}

fn main() -> Result<()> {
    let args = Args::parse();

    let mut files_to_hash = Vec::new();

    for file_path in &args.files {
        if file_path.is_dir() && args.recursive {
            for entry in walkdir::WalkDir::new(file_path)
                .into_iter()
                .filter_map(|e| e.ok())
                .filter(|e| e.file_type().is_file())
            {
                files_to_hash.push(entry.path().to_path_buf());
            }
        } else {
            files_to_hash.push(file_path.clone());
        }
    }

    for file_path in &files_to_hash {
        match compute_hash(file_path, &args.algorithm) {
            Ok((md5, sha256)) => {
                if args.algorithm == "md5" || args.algorithm == "both" {
                    if let Some(hash) = md5 {
                        println!("MD5({}) = {}", file_path.display(), hash);
                    }
                }
                if args.algorithm == "sha256" || args.algorithm == "both" {
                    if let Some(hash) = sha256 {
                        println!("SHA256({}) = {}", file_path.display(), hash);
                    }
                }
            }
            Err(e) => {
                eprintln!("Error hashing {}: {}", file_path.display(), e);
            }
        }
    }

    Ok(())
}
