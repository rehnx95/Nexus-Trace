# Submission Readiness

## Completed

- Deployment Dockerfiles for backend and frontend.
- Docker Compose stack with Neo4j, backend, frontend, volumes, and health checks.
- Restricted backend CORS configuration.
- Environment templates for local, Docker, and optional LLM settings.
- Docker Compose validation added to CI.
- README deployment walkthrough.
- Gold-dev metrics: entity, NER, and relation F1 all `1.0000`.
- Resolution dev metrics: false-auto-merges `0`, auto-plus-review recall `1.0000`.
- Full backend suite passes with 34 tests.

## Deployment Validation

Docker Engine was unavailable in the current Windows environment, so a live
`docker compose up` build could not be run here. CI validates `docker compose config`
on an Ubuntu runner; an operator should run the live stack before external submission.

## External Submission Items

- Run `docker compose up --build` on a Docker-capable machine.
- Capture frontend screenshots and demo workflow video.
- Record architecture and data-flow diagrams in the final presentation.
- Run a real-provider LLM smoke test without storing credentials in the repository.
- Locked-test verification remains explicitly gated and was not inspected or run.
- Review hosting domain values and set production `CORS_ORIGINS`.
