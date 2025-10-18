## Simple Resource Pack Server

Very simple Flask python server that hosts resource pack zip files and their sha1 code. Uniquely, the URL to the info page is also the download URL. Users can use that feature to find information about a resource pack they had configured.

## Mainline packs

Packs marked main are automatically navigated to when visiting the root domain, and are listed in the version selector. All other packs remain available, but only if you know the original slug for them. This way when a new version is uploaded to the server, people's old resource pack settings don't stop working.
