`sitebuild.toml` configures the docs-site static site builder. Under the
`[build.content_types]` table it currently builds markdown and html sources and leaves
rst disabled. Add asciidoc as a supported source type by setting `asciidoc = true` in
that same table. Do not change the markdown, html, or rst settings, and do not touch any
other section of the file.
