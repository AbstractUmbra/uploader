use std::fs;
use warp::Filter;
use serde_derive::Deserialize;
use std::collections::HashMap;

#[derive(Deserialize)]
struct Config {
    users: HashMap<String, String>,
    limitations: HashMap<String, u32>,
}

fn config() -> Config {
    let raw_toml = fs::read_to_string("config.toml").unwrap();

    let config: Config = toml::from_str(&raw_toml).unwrap();

    return config;
}


#[tokio::main]
async fn main() {
    let current_config: Config = config();
    println!("{}", current_config.users["Umbra"]);
    println!("{}", current_config.limitations["Images"]);

    let hello = warp::path!("hello" / String)
        .map(|name| format!("Hello, {}!", name));

    warp::serve(hello)
        .run(([0, 0, 0, 0], 3090))
        .await;
}