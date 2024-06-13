use clap::Parser;

#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
pub struct Args {
    /// Specify the app name
    #[arg(long)]
    pub app: Option<String>,

    /// Specify the author name
    #[arg(long)]
    pub author: Option<String>,

    /// List all the apps
    #[arg(long)]
    pub list_apps: bool,

    /// List all the authors
    #[arg(long)]
    pub list_authors: bool,

    /// Update the Docker Compose folder
    #[arg(long)]
    pub update: bool,
}
