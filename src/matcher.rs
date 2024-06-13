use std::cmp::Ordering;
use std::collections::BinaryHeap;
use strsim::jaro_winkler;
use crate::file_ops::{Data, copy_docker_compose_file};


#[derive(PartialEq)]
struct ScoredStr {
    score: f64,
    string: String,
}

impl Eq for ScoredStr {}

impl Ord for ScoredStr {
    fn cmp(&self, other: &Self) -> Ordering {
        other.score.partial_cmp(&self.score).unwrap()
    }
}

impl PartialOrd for ScoredStr {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

fn get_close_matches(word: &str, possibilities: &[String], cutoff: f64) -> Vec<String> {
    let mut heap: BinaryHeap<ScoredStr> = BinaryHeap::new();

    for possibility in possibilities {
        let score = jaro_winkler(word, possibility);
        if score >= cutoff {
            heap.push(ScoredStr {
                score,
                string: possibility.clone(),
            });
        }
    }

    heap.into_sorted_vec()
        .into_iter()
        .map(|scored| scored.string)
        .collect()
}

fn get_match(query: &str, items: &[String], item_type: &str) -> Option<String> {
    let query = query.to_lowercase();

    if let Some(item) = items.iter().find(|&item| item.to_lowercase() == query) {
        return Some(item.clone());
    }

    let matches = get_close_matches(&query, items, 0.75);
    match matches.len() {
        0 => println!("No {} matches found for {}", item_type, query),
        1 => {
            println!("Match found for {}: {}", query, matches[0]);
            return Some(matches[0].clone());
        }
        _ => {
            println!(
                "No exact match found for {}. Did you mean one of the following?",
                query
            );
            for match_ in matches {
                println!("{}", match_);
            }
        }
    }

    None
}

pub fn handle_app_author(
    app: Option<String>,
    author: Option<String>,
    data: &Data,
    directory: &str,
    out_directory: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    if let Some(app) = app {
        if let Some(app_matched) = get_match(&app, &data.apps, "app") {
            let app_authors = data.folder_structure.get(&app_matched).unwrap();

            if let Some(author) = author {
                if let Some(author_matched) = get_match(&author, app_authors, "author") {
                    copy_docker_compose_file(&app_matched, &author_matched, directory, out_directory)?;
                }
            } else {
                println!("Authors for {}: ", app_matched);
                for author in app_authors {
                    println!("{}", author);
                }
            }
        }
    } else if let Some(author) = author {
        if let Some(author_matched) = get_match(&author, &data.authors, "author") {
            let author_apps: Vec<String> = data
                .folder_structure
                .iter()
                .filter_map(|(app, authors)| {
                    if authors.contains(&author_matched) {
                        Some(app.clone())
                    } else {
                        None
                    }
                })
                .collect();

            println!("Apps by {}: ", author_matched);
            for app in author_apps {
                println!("{}", app);
            }
        }
    }

    Ok(())
}
