# Runtime backup and staged recovery

The settings backup endpoint now produces an encrypted `.jbackup` using a
SQLite online snapshot. It includes committed WAL data; the snapshot is built
in memory and does not create an unencrypted temporary database. Snapshotting
has a bounded progress deadline and runs in the synchronous endpoint thread.
No empty database is created as a success fallback.

Configure `JAVO_ENCRYPTION_KEY` with a securely generated persistent secret of
at least 32 characters before using POST `/api/settings/backup`. Retain this
secret in the owner's password manager/recovery storage. The key is not
included in the archive or settings response. The current service derives its
Fernet encryption key from that configured high-entropy secret; this is not a
password-stretching scheme and should not be used with a human-chosen password.
Windows OS-backed key storage and a complete recovery wizard remain pending.

GET `/api/settings/backups` labels encrypted archives and preserved legacy
plaintext `.db` backups distinctly. Older files are not deleted or converted
automatically. The archive currently covers the runtime SQLite database, not
an atomic backup of every media folder, scheduler store, model or OS key.

Live POST `/api/settings/restore` returns 409: copying a backup over a database
with active service connections is unsafe. The recovery agent similarly
reports `blocked` rather than fabricating successful restoration.

For offline recovery, stop all Javo processes, keep the existing data intact,
and use `BackupService.restore_backup` with the same retained encryption key
and a new empty staging directory. Verify the staged SQLite integrity and
expected records before planning an offline replacement. A verified automatic
installation/migration command is not implemented yet; staging is not a claim
that the running app has been restored.

Restore authenticates the encrypted archive, checks any saved checksum, rejects
path traversal, drive/absolute paths, links, special files and duplicate names,
and validates the complete member list before writing content. It refuses
nonempty staging directories and applies file-count/expanded-size limits.
Keep staging and existing owner data separate while reviewing recovery.

Real temporary-SQLite tests cover committed WAL data, decryption with the same
key in a new service object, exact restored records, SQLite integrity, wrong
keys, corrupted ciphertext, archive paths/links, preserved existing files and
blocked live restore. This is not an end-user Windows installer recovery test.
