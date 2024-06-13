use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Serialize, Deserialize, Debug)]
pub struct Data {
    pub apps: Vec<String>,
    pub authors: Vec<String>,
    pub folder_structure: HashMap<String, Vec<String>>,
}
