use reqwest::blocking::get;
use std::fs::File;
use std::io;
use zip::read::{ZipArchive, ZipFile};
use std::path::{Path, PathBuf};
use std::fs::create_dir_all;

type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;

pub fn download_file(url: &str, file_path: &str) -> Result<()> {
    let body = get(url)?.bytes()?;
    println!("Downloaded {} bytes", body.len());
    std::fs::write(file_path, body)?;
    Ok(())
}

pub fn extract_zip(file_path: &str, destination: &str) -> Result<()> {
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
