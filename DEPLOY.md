# Deployment Guide

This document describes how to start the backend and frontend services for the project.

### Instructions to run Backend
```
#!/bin/bash
# Enter in Backend directory
cd Backend/

# Start the application
./deploy.sh start
```

## Instruction to run Frontend
```
#!/bin/bash
# Enter in Frontend directory
cd Frontend/

# Build and start the frontend container behind Traefik
./deploy.sh
```

## Notes
The frontend is served through Traefik over HTTPS at `https://app.docker.localhost`.

The frontend and backend share the same browser origin. Angular calls the backend with relative paths such as `/auth/api/v1`, `/fed/api/v1`, and `/comp/api/v1`, so requests go through Traefik instead of staying on the frontend container.

Because Traefik uses a local self-signed certificate for `*.docker.localhost`, visit `https://app.docker.localhost` once in your browser and accept the certificate warning.

## Architecture

The frontend is intentionally routed through Traefik instead of being accessed directly at `https://localhost:4200`. This keeps the browser origin the same for the Angular app and the backend APIs:

```
https://app.docker.localhost/       -> Angular frontend
https://app.docker.localhost/auth   -> Auth Service
https://app.docker.localhost/fed    -> Federation Service
https://app.docker.localhost/comp   -> Competition Service
```

This is a pragmatic local-development reverse-proxy setup. It avoids browser CORS and `localhost` confusion between the host machine, browser, and containers. It also matches the production-style pattern where a public proxy owns the HTTPS entrypoint and routes traffic by path.

The tradeoff is that frontend development now depends on Traefik being running, and this setup does not test a separate frontend/API origin. If production uses separate domains, explicit CORS rules should still be configured and tested.
