# KOMIZ LNCrawl Hostless Wrapper

Runs the official LNCrawl container on Hostless, binds to Hostless' runtime PORT,
and optionally persists /data by backing it up to a private Supabase Storage bucket.

Recommended environment variables:
- TZ=Asia/Jakarta
- DATABASE_URL=<Supabase Session Pooler URL>

For /data backup:
- SUPABASE_URL=https://<project-ref>.supabase.co
- SUPABASE_SECRET_KEY=<server-side secret/service-role key>
- LNCRAWL_BACKUP_BUCKET=lncrawl-backup
- LNCRAWL_BACKUP_OBJECT=server/data.tar.gz
- BACKUP_INTERVAL_SECONDS=900

Never commit secrets to GitHub.
Use only novel content you have permission to access and serve.
