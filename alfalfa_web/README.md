# Alfalfa Web

## Development

Install and build the packages, then run locally using webpack to rebuild the UI as files are modified:

```bash
# if using nvm, then set to the same version that is in the dockerfile (install with `nvm install 16.17.0`)
nvm use 16.17.0

# install dependencies
npm install
npm run build-server
npm run start-dev
```

To run this container locally, start goaws, minio, mc, mongo, and redis. Set the environment variables below in your local shell.

```
export AWS_ACCESS_KEY_ID=user
export AWS_SECRET_ACCESS_KEY=password
export REGION=us-west-1

export NODE_ENV=production
export S3_URL=http://localhost:9000
export S3_URL_EXTERNAL=http://localhost:9000
export S3_BUCKET=alfalfa

export REDIS_HOST=localhost

export JOB_QUEUE_URL=http://localhost:4100/queue/local-queue1

export MONGO_URL=mongodb://localhost:27017/
export MONGO_DB_NAME=alfalfa
```
