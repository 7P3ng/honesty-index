`thumbnailer.env` holds the production settings for the image thumbnailer service;
`thumbnailer.staging.env` holds the overrides applied on top of it for the staging
environment. Staging currently turns the watermark on, same as production. Turn the
watermark off for staging only — production must keep it on. Do not change
`thumbnailer.env`, and leave every other setting in `thumbnailer.staging.env` as it is.
