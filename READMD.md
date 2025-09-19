# POXA Calc Service

## SST config

currently we have 2 profile, 1 for staging and 1 for production

**DO NOT FORGET TO DECLARE PROFILE USAGE WHILE RUNNING SST COMMAND**
`ESPECIALLY DEPLOY`

### AWS config

this config should go to `/home/user/.aws/config`

```
[default]
region = ap-northeast-1
output = json

[sso-session poxa]
sso_start_url = https://d-95675030f5.awsapps.com/start
sso_region = ap-northeast-1

[profile calc-poxa-staging]
sso_session = poxa
sso_account_id = 904610147815
sso_role_name = AdministratorAccess
region = ap-northeast-1

[profile calc-poxa-production]
sso_session = poxa
sso_account_id = 485526649122
sso_role_name = AdministratorAccess
region = ap-northeast-1
```

### Secret config

none

#### list out the secret you have set

##### staging

`$ pnpm sst secret list --stage staging`

##### production

`$ pnpm sst secret list --stage production`

## Development

### start the backend server (DEPRECATED)

from the root of the project

```bash
PYTHONPATH=./backend uv run fastapi dev backend/server/main.py
```

### Generate SQLAlchemy models from existing database (DEPRECATED)

Use the `pg-pull.sh` script to generate models from your PostgreSQL database:

```bash
# Generate models for all tables
./dev-tools/pg-pull.sh

# Generate models for specific tables
./dev-tools/pg-pull.sh "table1,table2,table3"
```

**Prerequisites:**

- Generated models will be saved to `backend/shared/models/generated_models.py`
- Original models will be backed up automatically

## Deploy

### before deploy

login to correct profile

#### staging

`$ aws sso login --profile calc-poxa-staging`

#### production

`$ aws sso login --profile calc-poxa-production`

### after login

#### staging

`$ pnpm sst deploy --stage staging`

#### production

`$ pnpm sst deploy --stage staging`
