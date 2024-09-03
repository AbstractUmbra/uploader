use rocket::fs::TempFile;

#[derive(FromForm, Debug)]
pub(crate) struct FileUpload<'r> {
    pub file: TempFile<'r>,
}

#[derive(FromForm, Debug)]
pub(crate) struct AudioUpload<'r> {
    pub file: TempFile<'r>,
    pub title: Option<String>,
    pub author: Option<String>,
}
