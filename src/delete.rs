use std::fs::remove_file;
use std::path::Path;

use rocket::http::Status;
use rocket_db_pools::sqlx::Row;

use crate::DB;

#[get("/<deletion_id>?<user_id>")]
pub(crate) async fn delete_upload(db: &DB, deletion_id: String, user_id: i16) -> Status {
    let record = db.remove_upload(user_id, deletion_id).await;
    match record.try_get::<String, usize>(0) {
        Ok(filename) => {
            let path = Path::new("/etc/uploaded/images").join(filename);
            remove_file(path).expect("Unable to delete file.");
            Status::Ok
        }
        Err(_) => Status::NotFound,
    }
}
