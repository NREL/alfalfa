# Alfalfa Web

## Development

Install and build the packages

```bash
npm install

npm run build
```

To run this container locally, start goaws, minio, mc, mongo, and redis. Set the environment varialbes below in
your local shell.

```
export AWS_ACCESS_KEY_ID=user
export AWS_SECRET_ACCESS_KEY=password
export REGION=us-west-1

export NODE_ENV=production
export S3_URL=http://localhost:9000
export S3_URL_EXTERNAL=http://localhost:9000
export S3_BUCKET=alfalfa

export REDIS_HOST=localhost

export JOB_QUEUE_URL=http://localhost:4100/queue/local-queue

export MONGO_URL=mongodb://localhost:27017/
export MONGO_DB_NAME=alfalfa
```
