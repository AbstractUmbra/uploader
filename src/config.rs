use rocket::serde::Deserialize;

#[derive(Deserialize, Debug, Clone)]
#[serde(crate = "rocket::serde")]
pub(crate) struct UserConfig {
    pub name: String,
    pub id: i16,
    pub token: String,
    pub response_urls: Vec<String>,
}

#[derive(Deserialize, Debug, Clone)]
#[serde(crate = "rocket::serde")]
pub(crate) struct Config {
    pub users: Vec<UserConfig>,
}
