use std::path::PathBuf;

use crate::config::{Config, UserConfig};
use rocket::{
    http::Status,
    request::{FromRequest, Outcome, Request},
    serde::{Deserialize, Serialize},
};

#[derive(Debug, Eq, PartialEq, PartialOrd, Ord)]
pub(crate) enum UserError {}

#[derive(Clone, Serialize, Deserialize)]
#[serde(crate = "rocket::serde")]
pub(crate) struct User {
    pub name: String,
    pub id: i16,
    pub token: String,
    pub response_urls: Vec<String>,
    pub save_base_path: PathBuf,
}

#[rocket::async_trait]
impl<'r> FromRequest<'r> for User {
    type Error = &'r UserError;

    async fn from_request(req: &'r Request<'_>) -> Outcome<Self, Self::Error> {
        let config = req
            .rocket()
            .state::<Config>()
            .expect("Unable to get config state.");

        let token = req
            .headers()
            .get_one("Authorization")
            .expect("No authorization header present.")
            .replace("Bearer ", "");

        let user = config
            .users
            .iter()
            .find(|u| *u.token == *token)
            .cloned()
            .map(User::from);

        match user {
            None => Outcome::Forward(Status::Unauthorized),
            Some(u) => Outcome::Success(u),
        }
    }
}

impl From<UserConfig> for User {
    fn from(value: UserConfig) -> User {
        let mut path = PathBuf::from("/etc/uploaded/");
        path.push(&value.name);

        User {
            name: value.name,
            id: value.id,
            token: value.token,
            response_urls: value.response_urls,
            save_base_path: path,
        }
    }
}
