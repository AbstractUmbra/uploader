use rand::seq::SliceRandom;
use rand::{distributions::Alphanumeric, Rng};

use crate::models::responses::{AudioUploadResponse, ImageUploadResponse};
use crate::models::User;
use crate::models::{AudioUpload, FileUpload};
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

#[post("/dickpic", data = "<upload>")]
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

    let path = user.save_base_path.join("images").join(filename.clone());

    let mut url = user
        .response_urls
        .choose(&mut rand::thread_rng())
        .expect("Unable to source a URL.")
        .to_owned();

    url.push_str(filename.as_str());

    let upload_data = ImageUploadResponse {
        image: url.to_owned(),
        delete: format!(
            "https://upload.umbra-is.gay/delete/{}?user_id={}",
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

#[post("/audio", data = "<upload>")]
pub(crate) async fn upload_audio(
    db: &DB,
    user: User,
    mut upload: Form<AudioUpload<'_>>,
) -> Json<AudioUploadResponse> {
    let deletion_id = generate_name();

    let content_type = upload
        .audio
        .content_type()
        .expect("No content type specified during the upload.");

    let file_ext = match content_type.extension() {
        Some(ext) => ext.as_str(),
        None => {
            if content_type.to_string().to_lowercase() == "audio/mp4" {
                "m4a"
            } else {
                "unknown"
            }
        }
    };

    let filename = format!("{}.{}", generate_name(), file_ext);

    db.insert_audio(
        user.id,
        &filename,
        upload.title.as_ref(),
        upload.author.as_ref(),
        deletion_id.clone(),
    )
    .await;

    let path = user.save_base_path.join("audio").join(filename.clone());

    let url = format!("https://audio.saikoro.moe/{}", filename.as_str());

    let upload_data = AudioUploadResponse {
        url: url.to_owned(),
        title: upload.title.clone(),
        author: upload.author.clone(),
        delete: format!(
            "https://upload.umbra-is.gay/delete/{}?user_id={}",
            deletion_id, user.id
        ),
        r#type: content_type.to_string(),
        size: upload.audio.len(),
    };

    upload
        .audio
        .persist_to(path)
        .await
        .expect("Unable to write file to destination.");

    Json(upload_data)
}
