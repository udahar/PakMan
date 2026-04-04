#!/usr/bin/env rust
//! Bookmark Manager - Save and manage bookmarks

use anyhow::Result;
use clap::{Parser, Subcommand};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(author, version, about = "Bookmark Manager")]
struct Args {
    /// Bookmarks file
    #[arg(short, long, default_value = "./bookmarks.json")]
    file: PathBuf,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Add a bookmark
    Add {
        /// URL
        #[arg(required = true)]
        url: String,
        /// Title/description
        #[arg(short, long)]
        title: Option<String>,
        /// Tags
        #[arg(short, long)]
        tag: Vec<String>,
    },
    /// List bookmarks
    List {
        /// Filter by tag
        #[arg(short, long)]
        tag: Option<String>,
    },
    /// Search bookmarks
    Search {
        /// Search query
        #[arg(required = true)]
        query: String,
    },
    /// Delete a bookmark
    Delete {
        /// Index to delete
        #[arg(required = true)]
        index: usize,
    },
}

#[derive(Serialize, Deserialize, Debug)]
struct Bookmark {
    url: String,
    title: Option<String>,
    tags: Vec<String>,
    created_at: String,
}

#[derive(Serialize, Deserialize, Default)]
struct BookmarkFile {
    bookmarks: Vec<Bookmark>,
}

fn load_bookmarks(path: &PathBuf) -> Result<BookmarkFile> {
    if path.exists() {
        let content = fs::read_to_string(path)?;
        Ok(serde_json::from_str(&content)?)
    } else {
        Ok(BookmarkFile::default())
    }
}

fn save_bookmarks(path: &PathBuf, data: &BookmarkFile) -> Result<()> {
    let content = serde_json::to_string_pretty(data)?;
    fs::write(path, content)?;
    Ok(())
}

fn main() -> Result<()> {
    let args = Args::parse();

    let mut bookmarks = load_bookmarks(&args.file)?;

    match args.command {
        Commands::Add { url, title, tag } => {
            let bookmark = Bookmark {
                url,
                title,
                tags: tag,
                created_at: chrono::Local::now().to_rfc3339(),
            };
            bookmarks.bookmarks.push(bookmark);
            save_bookmarks(&args.file, &bookmarks)?;
            println!("Bookmark added.");
        }
        Commands::List { tag } => {
            for (i, bm) in bookmarks.bookmarks.iter().enumerate() {
                if tag.as_ref().map_or(true, |t| bm.tags.contains(t)) {
                    println!("[{}] {}", i, bm.url);
                    if let Some(title) = &bm.title {
                        println!("    Title: {}", title);
                    }
                    if !bm.tags.is_empty() {
                        println!("    Tags: {}", bm.tags.join(", "));
                    }
                }
            }
        }
        Commands::Search { query } => {
            let query_lower = query.to_lowercase();
            for (i, bm) in bookmarks.bookmarks.iter().enumerate() {
                if bm.url.to_lowercase().contains(&query_lower)
                    || bm.title.as_ref().map_or(false, |t| t.to_lowercase().contains(&query_lower))
                    || bm.tags.iter().any(|t| t.to_lowercase().contains(&query_lower))
                {
                    println!("[{}] {}", i, bm.url);
                }
            }
        }
        Commands::Delete { index } => {
            if index < bookmarks.bookmarks.len() {
                let removed = bookmarks.bookmarks.remove(index);
                save_bookmarks(&args.file, &bookmarks)?;
                println!("Deleted: {}", removed.url);
            } else {
                eprintln!("Invalid index: {}", index);
            }
        }
    }

    Ok(())
}
