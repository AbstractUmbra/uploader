use rocket::serde::Serialize;

#[derive(Serialize)]
#[serde(crate = "rocket::serde")]
pub(crate) struct ImageUploadResponse {
    pub image: String,
    pub delete: String,
    pub r#type: String,
    pub size: u64,
}
