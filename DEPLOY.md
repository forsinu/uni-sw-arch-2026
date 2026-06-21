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

# Generate local HTTPS certificates, build and start the container
./deploy.sh
```

## Notes
The frontend deploy script generates a local self-signed certificate on the host and Docker Compose mounts it into the container. The frontend is served over HTTPS at `https://localhost:4200`.

The generated frontend certificate is stored in `Frontend/certs/`, which is ignored by git. 

The communication between the frontend and the backend uses HTTP instead of HTTPS because web browsers strictly enforce the use of certificates signed by a legitimate Certificate Authority (CA). However, an HTTPS endpoint for the backend is still available using a self-signed certificate generated at startup for the *.docker.localhost domain.