#!/usr/bin/env rust
//! CSV Viewer - View CSV files as formatted tables

use anyhow::Result;
use clap::Parser;
use std::fs;
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// CSV file to view
    #[arg(required = true)]
    file: PathBuf,

    /// Delimiter (default: comma)
    #[arg(short, long, default_value = ",")]
    delimiter: String,

    /// Max rows to display (0 = all)
    #[arg(short, long, default_value = "0")]
    max_rows: usize,

    /// Output as JSON
    #[arg(short, long)]
    json: bool,
}

fn parse_csv(content: &str, delimiter: char) -> Vec<Vec<String>> {
    let mut rows = Vec::new();

    for line in content.lines() {
        if line.trim().is_empty() {
            continue;
        }

        let mut row = Vec::new();
        let mut current = String::new();
        let mut in_quotes = false;

        for c in line.chars() {
            match c {
                '"' => in_quotes = !in_quotes,
                c if c == delimiter && !in_quotes => {
                    row.push(current.trim().to_string());
                    current = String::new();
                }
                c => current.push(c),
            }
        }

        row.push(current.trim().to_string());
        rows.push(row);
    }

    rows
}

fn format_table(rows: &[Vec<String>]) -> String {
    if rows.is_empty() {
        return String::new();
    }

    // Calculate column widths
    let mut widths = vec![0; rows[0].len()];
    for row in rows {
        for (i, cell) in row.iter().enumerate() {
            if i < widths.len() {
                widths[i] = widths[i].max(cell.len());
            }
        }
    }

    // Format rows
    let mut output = String::new();

    // Header separator
    let separator: String = widths
        .iter()
        .map(|w| "-".repeat(*w + 2))
        .collect::<Vec<_>>()
        .join("+");

    for (row_idx, row) in rows.iter().enumerate() {
        if row_idx == 1 {
            output.push_str(&separator);
            output.push('\n');
        }

        let formatted: Vec<String> = row
            .iter()
            .enumerate()
            .map(|(i, cell)| format!(" {:<width$} ", cell, width = widths[i]))
            .collect();

        output.push_str(&formatted.join("|"));
        output.push('|');
        output.push('\n');
    }

    output
}

fn rows_to_json(rows: &[Vec<String>]) -> String {
    if rows.is_empty() {
        return "[]".to_string();
    }

    let headers = &rows[0];
    let mut json = String::from("[\n");

    for (i, row) in rows.iter().skip(1).enumerate() {
        json.push_str("  {");
        let pairs: Vec<String> = headers
            .iter()
            .enumerate()
            .map(|(j, header)| {
                let value = row.get(j).map(|s| s.as_str()).unwrap_or("");
                format!("\"{}\": \"{}\"", header, value)
            })
            .collect();
        json.push_str(&pairs.join(", "));
        json.push('}');

        if i < rows.len() - 2 {
            json.push(',');
        }
        json.push('\n');
    }

    json.push(']');
    json
}

fn main() -> Result<()> {
    let args = Args::parse();

    let content = fs::read_to_string(&args.file)?;
    let delimiter = args.delimiter.chars().next().unwrap_or(',');
    let rows = parse_csv(&content, delimiter);

    if rows.is_empty() {
        println!("Empty CSV file");
        return Ok(());
    }

    // Apply row limit
    let display_rows = if args.max_rows > 0 && rows.len() > args.max_rows {
        &rows[..args.max_rows]
    } else {
        &rows
    };

    if args.json {
        println!("{}", rows_to_json(display_rows));
    } else {
        let table = format_table(display_rows);
        println!("{}", table);

        if args.max_rows > 0 && rows.len() > args.max_rows {
            println!("... and {} more rows", rows.len() - args.max_rows);
        }

        println!("\nTotal: {} rows, {} columns", rows.len(), rows[0].len());
    }

    Ok(())
}
