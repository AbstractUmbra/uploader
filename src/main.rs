#[macro_use]
extern crate rocket;

mod config;
mod delete;
mod models;
mod upload;

use config::Config;
use delete::delete_upload;
use rocket_db_pools::sqlx::postgres::PgRow;
use upload::upload_file;

use figment::providers::Format;
use figment::{providers::Json, Figment};
use rocket_db_pools::{sqlx, Connection, Database};

#[derive(Database)]
#[database("postgres")]
pub(crate) struct DB(sqlx::PgPool);

impl DB {
    pub async fn insert_upload(&self, user_id: i16, filename: &String, deletion_id: String) {
        let mut conn = self
            .acquire()
            .await
            .expect("Unable to acquire database connection.");

        sqlx::query("INSERT INTO images (author, filename, deletion_id) VALUES ($1, $2, $3);")
            .bind(user_id)
            .bind(filename)
            .bind(deletion_id)
            .execute(&mut *conn)
            .await
            .expect("Unable to insert upload row.");
    }

    pub(crate) async fn remove_upload(
        &self,
        user_id: i16,
        deletion_id: String,
    ) -> Result<PgRow, rocket_db_pools::sqlx::Error> {
        let mut conn = self
            .acquire()
            .await
            .expect("Unable to acquire database connection.");

        sqlx::query("DELETE FROM images WHERE deletion_id = $1 AND author = $2 RETURNING filename;")
            .bind(deletion_id)
            .bind(user_id)
            .fetch_one(&mut *conn)
            .await
    }
}

#[get("/health")]
async fn healthcheck(mut db: Connection<DB>) -> rocket::http::Status {
    let result = sqlx::query("SELECT 1;").fetch_one(&mut **db).await.ok();

    match result {
        Some(_) => rocket::http::Status::Ok,
        None => unreachable!(),
    }
}

#[rocket::main]
async fn main() -> Result<(), rocket::Error> {
    let user_config: Config = Figment::new()
        .merge(Json::file("config.json"))
        .extract()
        .expect("Misconfigured configuration file.");

    let _ = rocket::build()
        .attach(DB::init())
        .manage(user_config)
        .mount("/", routes![healthcheck])
        .mount("/dickpic", routes![upload_file])
        .mount("/delete", routes![delete_upload])
        .launch()
        .await?;

    Ok(())
}
