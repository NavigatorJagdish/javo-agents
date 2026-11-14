# Project checkpoints and storage

Owner instruction, 14 November 2026: keep milestone backups on Google Drive,
keep usable source/final deliverables on GitHub, and reclaim unnecessary local storage.

- Make a dated checkpoint after meaningful work. Store source, build instructions,
  verification results and a SHA256 file manifest in an archive. Keep the private
  continuity document in its existing saved file; exclude it from Drive/source
  archives unless its export to the destination is specifically authorized.
- Exclude credentials, `.env` files, user databases, account data, logs, models,
  `node_modules`, caches and temporary files from source backups and GitHub.
  This is a source/development backup; it is not an encrypted user-data backup.
- Keep the Drive folder private. Upload source to an isolated rebuild branch in the
  owner's existing GitHub repository. Preserve upstream history and remote edits;
  never force-push the unrelated local snapshot over `main`.
- An uploaded checkpoint may contain unfinished work; label limitations and
  unexecuted tests. Only label an installer or final build usable after verification.
- Verify ZIP integrity and each manifest hash after extraction. After upload,
  compare Drive's checksum/size with the local archive. Verify the GitHub branch
  tree against intended file hashes before treating that upload as complete.
- Delete only specifically identified reproducible caches/temporary files after
  backup verification. Preserve source, `.git`, required installed dependencies,
  owner media/data and the latest local checkpoint. Keep cloud checkpoints until
  a separate retention decision authorizes removal.
- During active project work, use this policy at milestones. An unattended backup
  service or scheduled task has not been installed by this policy document.

Remote folder/branch identities, checksum receipts and cleanup measurements are
recorded in the private project continuity document and local transfer receipts.
