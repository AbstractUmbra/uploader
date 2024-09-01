use rand::seq::SliceRandom;
use rand::{distributions::Alphanumeric, Rng}; // 0.7.2

use crate::models::responses::ImageUploadResponse;
use crate::models::FileUpload;
use crate::models::User;
use crate::DB;

use rocket::form::Form;
use rocket::serde::json::Json;

fn generate_name() -> String {
    rand::thread_rng()
        .sample_iter(&Alphanumeric)
        .take(20)
        .map(char::from)
        .collect()
}

#[post("/", data = "<upload>")]
pub(crate) async fn upload_file(
    db: &DB,
    user: User,
    mut upload: Form<FileUpload<'_>>,
) -> Json<ImageUploadResponse> {
    let deletion_id = generate_name();

    let content_type = upload
        .file
        .content_type()
        .expect("No content type specified during the upload.");

    let file_ext = content_type
        .extension()
        .expect("No provided file extension for this content type")
        .as_str();

    let filename = format!("{}.{}", generate_name(), file_ext);

    db.insert_upload(user.id, &filename, deletion_id.clone())
        .await;

    let mut path = user.save_path;
    path.push(filename.clone());

    let mut url = user
        .response_urls
        .choose(&mut rand::thread_rng())
        .expect("Unable to source a URL.")
        .to_owned();

    url.push_str(filename.as_str());

    let upload_data = ImageUploadResponse {
        image: url.to_owned(),
        delete: format!(
            "https://upload.umbra-is.gay/file/{}?user_id={}",
            deletion_id, user.id
        ),
        r#type: content_type.to_string(),
        size: upload.file.len(),
    };

    upload
        .file
        .persist_to(path)
        .await
        .expect("Unable to write file to destination.");

    Json(upload_data)
}
