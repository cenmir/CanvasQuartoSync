# TODO

## Comment highlighting on math/KaTeX content

Kalle is implementing a working version of this in his quarto viewer.


## Module Structure enhancements

- **Accept Canvas changes**: When Canvas is newer, the "↓ Review" button opens the diff editor — but there's no one-click "accept Canvas version" to overwrite the local file. Could add an "Accept Canvas" button in the diff view or in the Module Structure panel.
- **Sync status persistence**: Currently sync direction is based on comparing `updated_at` (Canvas) vs `mtime` (local). After a sync, the local mtime updates but the Canvas `updated_at` might not match exactly. Consider writing a `last_synced` timestamp to the sync map for more accurate tracking.
- **Quiz import**: The `--import-item` flow doesn't yet handle Quiz items (classic or new). Needs question fetching and QMD generation.
- **Module creation**: Local-only modules (orphan section) can't be synced yet because there's no corresponding Canvas module. Add a "Create Module on Canvas" action.
