use std::path::Path;

use rocket::http::Status;
use rocket_db_pools::sqlx::Row;

use crate::DB;

#[get("/<deletion_id>?<user_id>")]
pub(crate) async fn delete_upload(db: &DB, deletion_id: String, user_id: i16) -> Status {
    let record = db
        .remove_upload(user_id, deletion_id)
        .await
        .and_then(|r| r.try_get::<String, usize>(0));

    match record {
        Ok(filename) => {
            let path = Path::new("/etc/uploaded/images").join(filename);
            match std::fs::remove_file(path) {
                Ok(_) => Status::Ok,
                Err(_) => Status::ServiceUnavailable,
            }
        }
        Err(_) => Status::NotFound,
    }
}
