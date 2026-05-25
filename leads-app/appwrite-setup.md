# Appwrite Setup

Create one Appwrite Database for the leads app and set its ID in:

```env
APPWRITE_DATABASE_ID=<database-id>
```

The app defaults to these collection IDs. If you choose different IDs, set the matching environment variables.

```env
APPWRITE_USERS_COLLECTION_ID=leads_users
APPWRITE_MONITORS_COLLECTION_ID=leads_monitors
APPWRITE_SIGNALS_COLLECTION_ID=leads_signals
APPWRITE_LEAD_LAG_COLLECTION_ID=leads_lead_lag_history
```

## Project

- Endpoint: `https://aw.smartpiggies.cloud`
- Project ID: `6a14aeb7001912f0717c`
- Auth provider: Email/password

## Environment Variables

```env
NEXT_PUBLIC_APPWRITE_ENDPOINT=https://aw.smartpiggies.cloud
NEXT_PUBLIC_APPWRITE_PROJECT_ID=6a14aeb7001912f0717c
APPWRITE_DATABASE_ID=<database-id>
APPWRITE_API_KEY=<server-api-key>
NEXTAUTH_SECRET=<generate-with-openssl-rand-base64-32>
NEXTAUTH_URL=<site-url>
```

The API key must have read/write access to Databases and must only be configured server-side.

## Collections

### `leads_users`

Use the Appwrite Auth user ID as the document `$id`.

| Attribute | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `username` | string | yes | | Display/login name |
| `email` | email/string | yes | | Unique |
| `role` | string | yes | `member` | `admin` or `member` |
| `approved` | boolean | yes | `false` | Admin approval gate |
| `last_login` | datetime | no | | Nullable |

Recommended indexes:

- unique `email`
- key `role`
- key `approved`

Seed users:

| `$id` | username | email | role | approved |
| --- | --- | --- | --- | --- |
| `mikea_43fe80dfd9274` | `mike` | `mike@chinavol.com` | `admin` | `true` |
| `di_4123945bdaac4` | `di` | `xiaodi334@126.com` | `member` | `true` |

### `leads_monitors`

| Attribute | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `slug` | string | yes | | Unique Polymarket slug |
| `pm_question` | string | yes | | Polymarket question text |
| `ticker` | string | yes | | Equity ticker |
| `description` | string | no | | Nullable |
| `signal_thresh_pp` | float | yes | `2.0` | Probability move threshold |
| `cooldown_hrs` | float | yes | `6.0` | Cooldown after signal |
| `active` | boolean | yes | `true` | Dashboard filter |

Recommended indexes:

- unique `slug`
- key `ticker`
- key `active`

### `leads_signals`

| Attribute | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `monitor_id` | string | yes | | References `leads_monitors.$id` |
| `signal_ts` | datetime | yes | | Signal fired time |
| `pm_ts` | datetime | yes | | Polymarket event time |
| `pm_prob_before` | float | yes | | |
| `pm_prob_after` | float | yes | | |
| `pm_move_pp` | float | yes | | |
| `direction` | string | yes | | `UP` or `DOWN` |
| `predicted_eq_return_bps` | float | yes | | |
| `confidence` | string | yes | `MEDIUM` | `LOW`, `MEDIUM`, `HIGH` |
| `status` | string | yes | `active` | `active`, `pending`, `resolved` |
| `outcome_at_1h` | float | no | | Nullable |
| `outcome_at_4h` | float | no | | Nullable |
| `created_at` | datetime | yes | | |

Recommended indexes:

- key `monitor_id`
- key `status`
- key `signal_ts`

### `leads_lead_lag_history`

| Attribute | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `monitor_id` | string | yes | | References `leads_monitors.$id` |
| `lead_seconds` | integer | yes | | Seconds equity leads Polymarket |
| `lag_seconds` | integer | yes | | Seconds Polymarket leads equity |
| `correlation` | float | yes | | Rolling correlation |
| `computed_at` | datetime | yes | | Computation timestamp |

Recommended indexes:

- key `monitor_id`
- key `computed_at`

## Permissions

The current app performs database operations server-side with `APPWRITE_API_KEY`, so collection document permissions can be locked down. Recommended baseline:

- No public document read/write permissions.
- Server API key has database read/write.
- Users authenticate through Appwrite Auth and are authorized by `leads_users.role` and `leads_users.approved`.
