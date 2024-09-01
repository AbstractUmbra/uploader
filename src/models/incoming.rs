use rocket::fs::TempFile;

#[derive(FromForm, Debug)]
pub(crate) struct FileUpload<'r> {
    pub file: TempFile<'r>,
}
