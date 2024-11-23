# Article revision format

Our revisions are currently encoded using free-form JSONB.

That might be changed in the future at some point; to keep some sane documentation for now, this file is used.

Each revision is an instance of `ArticleLogEntry`. Thus, all of them have the following shared fields:

- Article ID
- User ID
- Revision type
- Revision metadata (see below)
- Date
- Comment
- Revision index (within the article)

Supported revision types currently:

- `LogEntryType.Source`: source code change
- `LogEntryType.Title`: title change
- `LogEntryType.Name`: slug (URL, pageId) change
- `LogEntryType.Tags`: tag list change
- `LogEntryType.New`: formal revision that marks the creation of a page
- `LogEntryType.Parent`: parent page change
- `LogEntryType.FileAdded`: file added
- `LogEntryType.FileDeleted`: file deleted
- `LogEntryType.FileRenamed`: file renamed
- `LogEntryType.VotesDeleted`: votes deleted
- `LogEntryType.Wikidot`: wikidot revision; does nothing, cannot be reverted, contains comments (added for historical review)
- `LogEntryType.Revert`: revert revision

Each of them has special format of metadata field; these are detailed below.

## `LogEntryType.Source`

```json
{
  "version_id": int /* ArticleVersion ID */
}
```

## `LogEntryType.Title`

```json
{
  "title": string,
  "prev_title": string
}
```

## `LogEntryType.Name`

```json
{
  "name": string, /* full slug, including category */
  "prev_name": string /* full slug, including category */
}
```

## `LogEntryType.Tags`

```json
{
  "added_tags": [{
    "id": int, /* Tag ID */
    "name": string /* full slug, including category; used only for visuals */
  }],
  "removed_tags": [{
    "id": int, /* Tag ID */
    "name": string /* full slug, including category; used only for visuals */
  }]
}
```

## `LogEntryType.New`

These values are _usually_ not used, just present tracking.

This is because reverting revisions is done by undoing the change, and you can't undo the "new" revision.

```json
{
  "version_id": int, /* ArticleVersion ID */ 
  "title": string /* initial title of article */
}
```

## `LogEntryType.Parent`

```json
{
  "parent": string, /* full slug, including category; used only for visuals */
  "prev_parent": string, /* full slug, including category; used only for visuals */
  "parent_id": int, /* Article ID */
  "prev_parent_id": int /* Article ID */
}
```

## `LogEntryType.FileAdded`

```json
{
  "id": int, /* File ID */
  "name": string
}
```

## `LogEntryType.FileDeleted`

```json
{
  "id": int, /* File ID */
  "name": string
}
```

## `LogEntryType.FileRenamed`

```json
{
  "id": int, /* File ID */
  "name": string,
  "prev_name": string
}
```

## `LogEntryType.VotesDeleted`

The system stores votes that were present at the moment of deletion.

```json
{
  "rating_mode": string, /* Settings.RatingMode enum */
  "rating": int | float, /* sum or average, depending on rating mode */
  "votes_count": int,
  "popularity": float,
  "votes": [{
    "user_id": int, /* User ID */
    "vote": int | float, /* 1 or -1, or 0..5 float, depending on rating mode */
    "visual_group_id": int | null, /* VisualUserGroup ID */
    "date": string /* ISO 8601 datetime */
  }]
}
```

## `LogEntryType.Revert`

Note that metadata fields here are optional depending on specific revert subtypes.

```json
{
  "subtypes": [string], /* LogEntryType enum */
  "rev_number": int, /* revision index that was reverted to */
  /* present only for file-related subtypes */
  "files": {
    /* present if subtype has FileAdded */
    "added": [{
      "id": int, /* File ID */
      "name": string
    }],
    /* present if subtype has FileDeleted */
    "deleted": [{
      "id": int, /* File ID */
      "name": string
    }],
    /* present if subtype has FileRenamed */
    "renamed": [{
      "id": int, /* File ID */
      "name": string,
      "prev_name": string
    }]
  },
  /* present if subtype has Tags */
  "tags": {
    "added": [int], /* Tag ID */
    "removed": [int] /* Tag ID */
  },
  /* present if subtype has Source */
  "source": {
    "version_id": int /* ArticleVersion ID */
  },
  /* present if subtype has Title */
  "title": {
    "title": string,
    "prev_title": string
  },
  /* present if subtype has Name */
  "name": {
    "name": string, /* full slug, including category */
    "prev_name": string /* full slug, including category */
  },
  /* present if subtype has Parent */
  "parent": {
    "parent": string, /* full slug, including category; used only for visuals */
    "prev_parent": string, /* full slug, including category; used only for visuals */
    "parent_id": int, /* Article ID */
    "prev_parent_id": int /* Article ID */
  },
  /* present if subtype has Votes */
  "votes": {
    "rating_mode": string, /* Settings.RatingMode enum */
    "rating": int | float, /* sum or average, depending on rating mode */
    "votes_count": int,
    "popularity": float,
    "votes": [{
      "user_id": int, /* User ID */
      "vote": int | float, /* 1 or -1, or 0..5 float, depending on rating mode */
      "visual_group_id": int | null, /* VisualUserGroup ID */
      "date": string /* ISO 8601 datetime */
    }]
  }
}
```