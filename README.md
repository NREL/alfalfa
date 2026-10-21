# Alfalfa Virtual Building Service

Alfalfa is an open source web application forged in the melting pot of Building Energy Modeling (BEM), Building Controls, and Software Engineering domain expertise. Alfalfa transforms Building Energy Models (BEMs) into virtual buildings by providing industry standard building control interfaces for interacting with models as they run. From a software engineering perspective, Alfalfa leverages widely adopted open source products and is architected according to best practices for a robust, modular, and scalable architecture.

## User Documentation

Documentation resides in the [GitHub wiki](https://github.com/NatLabRockies/alfalfa/wiki)!

## Developer Documentation

We are currently working on increasing our developer documentation. See how to run the tests on the [GitHub wiki](https://github.com/NatLabRockies/alfalfa/wiki/Running-Tests). For releasing, see the wiki's [release instructions](https://github.com/NatLabRockies/alfalfa/wiki/Release-Instructions).

## Running Alfalfa Locally

Alfalfa runs as a Docker Compose stack (web, worker, MongoDB, Redis, and MinIO). Configuration is read from the `.env` file in the repository root. Requires Docker with the Compose plugin.

**Note for Apple Silicon (M1/M2/M3+) users:** Modelica FMUs typically only ship x86_64 (`binaries/linux64`) shared libraries, so a native arm64 `worker` will fail to load them with a misleading error such as:

```text
pyfmi.fmi.InvalidBinaryException: The FMU could not be loaded. Error loading the binary.
Could not load the FMU binary: .../binaries/linux64/<Model>.so: cannot open shared object file: No such file or directory
```

This is an architecture mismatch, not a missing file. `docker-compose.yml` does **not** pin `platform: linux/amd64` on the `worker` service (running everything under amd64 emulation by default would make the worker significantly slower for the common case, and most Apple Silicon users don't need FMU support). If you need to run Modelica FMUs on Apple Silicon, force amd64 yourself with `export DOCKER_DEFAULT_PLATFORM=linux/amd64` (or an explicit `--platform linux/amd64`) before running `docker compose up`, whether the worker image is pulled prebuilt from GHCR or built locally with `--build`.

### Production mode

Builds the optimized web bundle and runs the web service with `node build/index.js`:

```bash
docker compose up --build
```

The web application is served at [http://localhost/](http://localhost/) and the API docs at [http://localhost/docs](http://localhost/docs). MinIO is available at [http://localhost:9000](http://localhost:9000).

### Development mode

Mounts `alfalfa_web` and `alfalfa_worker` into the containers and runs them in watch mode so code changes reload automatically (webpack watch for the web, `watchmedo` for the worker):

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

### Optional historian (InfluxDB + Grafana)

```bash
HISTORIAN_ENABLE=true docker compose -f docker-compose.yml -f docker-compose.historian.yml up --build
```

Grafana is served at [http://localhost:3000](http://localhost:3000), with default login `admin` / `password` (set via `GF_SECURITY_ADMIN_USER` / `GF_SECURITY_ADMIN_PASSWORD` in `.env`). When enabled, a **Historian** button also appears in the Alfalfa web app's nav bar, opening Grafana in a new tab (it's hidden when the historian is disabled). The URL it links to is controlled by `GRAFANA_URL_EXTERNAL` in `.env` (defaults to `http://localhost:3000`) — update this if Grafana is reachable at a different host/port for your deployment.

To run development mode (live-reload) together with the historian stack, use `docker-compose.dev.historian.yml` instead of chaining all three files:

```bash
HISTORIAN_ENABLE=true docker compose -f docker-compose.yml -f docker-compose.dev.historian.yml up --build
```

### Stopping

```bash
docker compose down          # or: docker compose down -v to also remove volumes
```

# Related Repositories

## Docker Images

The Alfalfa docker images are published to the [GitHub Container Registry (GHCR)](https://ghcr.io) under the `natlabrockies` org for easy deployment via Helm or other docker services. The images include:

- [Alfalfa Web](https://github.com/orgs/NatLabRockies/packages/container/package/alfalfa%2Fweb) — `ghcr.io/natlabrockies/alfalfa/web`
- [Alfalfa Worker](https://github.com/orgs/NatLabRockies/packages/container/package/alfalfa%2Fworker) — `ghcr.io/natlabrockies/alfalfa/worker`
- [Alfalfa Grafana](https://github.com/orgs/NatLabRockies/packages/container/package/alfalfa%2Fgrafana) — `ghcr.io/natlabrockies/alfalfa/grafana`

Pull an image with:

```bash
docker pull ghcr.io/natlabrockies/alfalfa/web:latest
```

If the packages are private, authenticate first with a GitHub personal access token that has the `read:packages` scope:

```bash
echo "$GHCR_TOKEN" | docker login ghcr.io -u <github-username> --password-stdin
```

## Alfalfa Dependencies

The `alfalfa_worker` Docker image is built `FROM` a base image published by the separate [alfalfa-dependencies](https://github.com/NatLabRockies/alfalfa-dependencies) repository (`ghcr.io/natlabrockies/alfalfa-dependencies`). That repo owns the slow-to-compile, infrequently-changing native/scientific dependencies the worker needs — EnergyPlus, OpenStudio, and Modelica/FMU support (Assimulo, PyFMI, and SUNDIALS, including the legacy SUNDIALS 5.x runtime compatibility libraries some FMUs require) — so they're built once as a shared image rather than recompiled on every `alfalfa_worker` build.

The two repos are independent git repositories (no submodule/subtree link) connected only through the image tag referenced by `FROM` in [`alfalfa_worker/Dockerfile`](alfalfa_worker/Dockerfile), currently `main` (alfalfa-dependencies' default branch, rebuilt and republished by its CI on every push). During development that tag is sometimes a work-in-progress branch name from alfalfa-dependencies' CI instead; once merged to `main` (or a tagged release), `alfalfa_worker/Dockerfile` should be bumped back to `main` or the corresponding release tag. If a worker build/runtime issue looks like it belongs to EnergyPlus, OpenStudio, Assimulo/PyFMI, or SUNDIALS rather than alfalfa's own code, it likely needs to be fixed in alfalfa-dependencies instead.

## Python Notebooks

An [Alfalfa Python Notebook repository](https://github.com/NatLabRockies/alfalfa-notebooks) contains examples on how to interact with Alfalfa.

## Alfalfa Client

The Alfalfa Client is a Python library for making API calls to Alfalfa easier. The source code is available on [GitHub](https://github.com/NatLabRockies/alfalfa-client) and the package is released through [PyPi](https://pypi.org/project/alfalfa-client/).
