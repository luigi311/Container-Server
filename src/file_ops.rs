use std::fs::{create_dir_all, File};
use std::io::BufReader;
use std::path::Path;
use std::result::Result;
use std::collections::HashMap;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug)]
pub struct Data {
    pub apps: Vec<String>,
    pub authors: Vec<String>,
    pub folder_structure: HashMap<String, Vec<String>>,
}

pub fn read_json_from_file(file_path: &str) -> Result<Data, Box<dyn std::error::Error>> {
    let file = File::open(file_path)?;
    let reader = BufReader::new(file);
    let data: Data = serde_json::from_reader(reader)?;
    Ok(data)
}

pub fn copy_docker_compose_file(
    app: &str,
    author: &str,
    directory: &str,
    out_directory: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    let docker_compose_file = format!("{}/{}/{}/docker-compose.yml", directory, app, author);
    let out_docker_compose_file = format!("{}/{}/docker-compose.yml", out_directory, app);

    if Path::new(&docker_compose_file).exists() {
        create_dir_all(format!("{}/{}", out_directory, app))?;
        std::fs::copy(&docker_compose_file, &out_docker_compose_file)?;
        println!("Copied Docker Compose file to {}", out_docker_compose_file);
    } else {
        println!(
            "Docker Compose file does not exist for {} by {}",
            app, author
        );
    }

    Ok(())
}
