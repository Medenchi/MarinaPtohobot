# `admin-login` Edge Function

Single function that authenticates Denis (`admin`) or Marina (`mama`) by password
and returns a JWT signed with the project's JWT Secret. RLS policies inspect the
custom `app_role` claim via `public.app_role()` (see
`supabase/migrations/0006_supabase_only.sql`).

## Setup

```bash
# 1) Install the CLI if you don't have it:
#    https://supabase.com/docs/guides/cli
# 2) Login: supabase login
# 3) Link to project (one-time):
supabase link --project-ref rxejhcpchzmbaovhvxso

# 4) Set the function secrets:
supabase secrets set \
  APP_ADMIN_PASSWORD=YourDenisPassword \
  APP_MAMA_PASSWORD=YourMarinaPassword \
  APP_JWT_SECRET="<paste the JWT Secret from Project Settings → API>"

# 5) Deploy. --no-verify-jwt lets unauthenticated requests hit the function
#    (the function itself does the password check).
supabase functions deploy admin-login --no-verify-jwt
```

## Usage

```http
POST https://rxejhcpchzmbaovhvxso.functions.supabase.co/admin-login
content-type: application/json

{ "role": "admin", "password": "..." }
```

Response on success:

```json
{ "token": "ey...", "role": "admin", "expires_at": 1779900000 }
```

The frontend stores this token and sends it as `Authorization: Bearer <token>`
to every Supabase REST/Storage request. The Postgres function `app_role()`
reads `app_role` out of the JWT claims, and RLS policies use that value to
permit or deny each operation.
