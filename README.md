# KOMIZ LNCrawl Hostless Wrapper v2

Fixes Hostless read-only `/data` errors by using writable `/tmp/lncrawl-data`.

Environment variables for the first test:
- `TZ=Asia/Jakarta`
- `LNCRAWL_DATA_PATH=/tmp/lncrawl-data` (optional; already the image default in v2)

Persistent backup can be added later using Supabase Storage.
Never commit secrets to GitHub.
