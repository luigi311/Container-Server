mod args;
mod data;
mod download;
mod file_ops;
mod matcher;

use args::Args;
use download::{download_file, extract_zip};
use file_ops::{Data, read_json_from_file};
use matcher::handle_app_author;

use clap::Parser;
use dotenvy::dotenv;
use std::fs::{remove_dir_all, remove_file};
use std::path::Path;

type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;

fn main() -> Result<()> {
    let args: Args = Args::parse();

    // load environment variables from .env file
    dotenv().ok();

    let docker_compose: String =
        std::env::var("TEMPLATES_FOLDER").unwrap_or("Docker_Compose".to_string());
    let output_directory: String =
        std::env::var("DOCKER_COMPOSE_FOLDER").unwrap_or(".".to_string());

    if !Path::new(&docker_compose).exists() || args.update {
        if Path::new(&docker_compose).exists() {
            println!("Removing existing Docker Compose folder");
            remove_dir_all(&docker_compose)?;
        }

        let docker_compose_url: &str = "https://github.com/luigi311/Container-Server-Templates/releases/download/latest/Docker_Compose.zip";
        let docker_compose_zip: &str = "Docker_Compose.zip";

        download_file(docker_compose_url, docker_compose_zip)?;
        extract_zip(docker_compose_zip, &docker_compose)?;
        println!("Downloaded and extracted Docker Compose");
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

    handle_app_author(
        args.app,
        args.author,
        &data,
        &docker_compose,
        output_directory.as_str(),
    )?;

    Ok(())
}
