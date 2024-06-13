use clap::Parser;

use reqwest::blocking::get;
use serde::{Deserialize, Serialize};
use zip::read::{ZipArchive, ZipFile};

use std::collections::HashMap;
use std::fs::{File, create_dir_all, remove_dir_all, remove_file};
use std::io::{self, BufReader};
use std::path::{Path, PathBuf};

use strsim::jaro_winkler;
use std::collections::BinaryHeap;
use std::cmp::Ordering;


#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Args {
    /// Specify the app name
    #[arg(long)]
    app: Option<String>,
    
    /// Specify the author name
    #[arg(long)]
    author: Option<String>,

    /// List all the apps
    /// This will list all the apps available in the Docker Compose folder
    #[arg(long)]
    list_apps: bool,

    /// List all the authors
    /// This will list all the authors available in the Docker Compose folder
    #[arg(long)]
    list_authors: bool,

    /// Update the Docker Compose folder
    /// This will download the latest docker compose folder from the github release
    #[arg(long)]
    update: bool,
}


#[derive(Serialize, Deserialize, Debug)]
struct Data {
    apps: Vec<String>,
    authors: Vec<String>,
    folder_structure: HashMap<String, Vec<String>>,
}

type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;

fn read_json_from_file(file_path: &str) -> Result<Data> {
    let file: File = File::open(file_path)?;
    let reader: BufReader<File> = BufReader::new(file);
    let data: Data = serde_json::from_reader(reader)?;
    Ok(data)
}

fn download_file(url: &str, file_path: &str) -> Result<()> {
    let body = get(url)?.bytes()?;

    println!("Downloaded {} bytes", body.len());

    std::fs::write(file_path, body)?;

    Ok(())
}

fn extract_zip(file_path: &str, destination: &str) -> Result<()> {
    let file: File = File::open(file_path)?;
    let mut archive: ZipArchive<File> = ZipArchive::new(file)?;

    for i in 0..archive.len() {
        let mut file: ZipFile = archive.by_index(i)?;
        let outpath: PathBuf = match file.enclosed_name() {
            Some(path) => Path::new(destination).join(path),
            None => continue,
        };

        if file.name().ends_with('/') {
            create_dir_all(&outpath)?;
        } else {
            if let Some(p) = outpath.parent() {
                if !p.exists() {
                    create_dir_all(p)?;
                }
            }
            let mut outfile: File = File::create(&outpath)?;
            io::copy(&mut file, &mut outfile)?;
        }

    }
    Ok(())
}


fn get_close_matches(word: &String, possibilities: &[String], cutoff: f64) -> Vec<String> {
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



    let mut heap = BinaryHeap::new();

    for possibility in possibilities {
        let score = jaro_winkler(word, possibility);
        if score >= cutoff {
            heap.push(ScoredStr { score, string: possibility.clone() });
        }
    }

    heap.into_sorted_vec().into_iter().map(|scored| scored.string).collect()
}

fn get_match(query: &String, items: &[String], item_type: &str) -> Option<String> {
    // Take into account case sensitivity
    let query: String = query.to_lowercase();

    // Check for exact match
    for item in items {
        if item.to_lowercase() == query {
            return Some(item.clone());
        }
    }
    
    let matches: Vec<String> = get_close_matches(&query, items, 0.75);
    if matches.len() == 0 {
        println!("No {} matches found for {}", &item_type, &query);
    } else if matches.len() == 1 {
        println!("Match found for {}: {}", &query, matches[0]);

        return Some(matches[0].clone());
    } else {
        println!("No exact match found for {}. Did you mean one of the following?", &query);
        for match_ in matches {
            println!("{}", match_);
        }
    }

    None
}

// Copy the Docker Compose file to the directory
fn copy_docker_compose_file(app: &str, author: &str, directory: &str, out_directory: &str) -> Result<()> {
    let docker_compose_file = format!("{}/{}/{}/docker-compose.yml", directory, app, author);
    let out_docker_compose_file = format!("{}/{}/docker-compose.yml", out_directory, app);

    if Path::new(&docker_compose_file).exists()  {
        // Create the output directory if it does not exist
        create_dir_all(format!("{}/{}", out_directory, app))?;

        std::fs::copy(docker_compose_file, &out_docker_compose_file)?;
        println!("Copied Docker Compose file to {}", out_docker_compose_file);
    } else {
        println!("Docker Compose file does not exist for {} by {}", app, author);
    }

    Ok(())
}

// Handle if the user provides an app and/or author
fn handle_app_author(app: Option<String>, author: Option<String>, data: &Data, directory: &str, out_directory: &str) -> Result<()> {

    // if app is provided, get the match
    if let Some(app) = app {
        let app_matched: Option<String> = get_match(&app, &data.apps, "app");

        if let Some(app_matched) = app_matched {
            let mut app_authors: Vec<String> = Vec::new();
            // Get the authors for the app from data.folder_structure[app]
            if let Some(authors) = data.folder_structure.get(&app_matched) {
                app_authors = authors.clone();
            }

            // if author is provided, get the match
            if let Some(author) = author {
                let author_matched: Option<String> = get_match(&author, &app_authors, "author");

                if let Some(author_matched) = author_matched {
            
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
        let author_matched: Option<String> = get_match(&author, &data.authors, "author");

        if let Some(author_matched) = author_matched {
            let mut author_apps: Vec<String> = Vec::new();
            // Get the apps for the author from data.folder_structure[*][author]
            for (app, authors) in &data.folder_structure {
                if authors.contains(&author_matched) {
                    author_apps.push(app.clone());
                }
            }

            println!("Apps by {}: ", author_matched);
            for app in author_apps {
                println!("{}", app);
            }
        }
    }

    Ok(())

}

fn main() -> Result<()> {
    let args = Args::parse();

    let docker_compose: String = "Docker_Compose".to_owned();
    
    // Check if the folder exists or if args.update is true
    if !Path::new(&docker_compose).exists() || args.update {

        // Remove the folder if it exists
        if Path::new(&docker_compose).exists() {
            println!("Removing existing Docker Compose folder");
            remove_dir_all(&docker_compose)?;
        }

        let docker_compose_url = "https://github.com/luigi311/Container-Server-Templates/releases/download/latest/Docker_Compose.zip";
        let docker_compose_zip = "Docker_Compose.zip";

        download_file(docker_compose_url, docker_compose_zip)?;
        extract_zip(docker_compose_zip, &docker_compose)?;

        println!("Downloaded and extracted Docker Compose");
        // Remove the zip file
        remove_file(docker_compose_zip)?;
    }

    let data: Data = read_json_from_file(&format!("{}/app_list.json", docker_compose))?;

    if args.list_apps {
        println!("Apps: ");
        for app in &data.apps {
            println!("{}", app);
        }
    }

    if args.list_authors {
        println!("Authors: ");
        for author in &data.authors {
            println!("{}", author);
        }
    }

    handle_app_author(args.app, args.author, &data, &docker_compose, "output")?;

    Ok(())
}
