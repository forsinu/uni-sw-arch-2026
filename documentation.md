# Swimming Competition Management System - Architecture Documentation

## Overview

We have implemented a Distributed System with a Service-Based Architecture, designed to manage swimming competitions, athletes, federation members, and related operations. The system is composed of multiple independent services that communicate through a message broker and REST APIs.

### Technology Stack

Component      | Technology 
Frontend       | Angular 
Backend        | Python - FastAPI
Database       | PostgreSQL 
Message Broker | RabbitMQ 
Reverse Proxy  | NGINX
Authentication | JWT (Access Token + Refresh Token) 

## Architecture Overview

### Service-Based Architecture

The system is organized into a service-based architecture where each domain is managed by a specific, independent service running its own FastAPI instance, handling REST API requests on its own port, and managing a dedicated PostgreSQL database. Specifically, the AuthService handles user authentication, authorization, and security; the FederationService manages federation members, swimming pools, and teams; and the CompetitionService is responsible for swimming competitions, meetings, events, and results. To ensure seamless cooperation while maintaining this strict isolation, the services communicate with one another through the RabbitMQ message broker whenever data needs to be shared or synchronized.

### Database Strategy

A relational database (PostgreSQL) was chosen to ensure reliability and a normalized structure, strictly following the service-based architecture pattern. Within this model, each service operates with its own dedicated database containing only the tables relevant to its specific domain, with direct cross-database access strictly prohibited. Instead, data consistency across the different services is seamlessly maintained through event-driven communication powered by RabbitMQ.

## Backend Services

### 1. AuthService

Port: 8000  
Purpose: Central authentication and authorization service for the entire system

#### Key Responsibilities

- User account management (registration, creation, deactivation)
- Authentication and authorization
- JWT token generation and validation
- Session management through refresh tokens
- Security and cryptography operations
- Login attempt tracking and audit logging

### 2. FederationService

Port: 8001  
Purpose: Manages swimming federation structure, members, teams, and facilities

#### Key Responsibilities

- Federation member management (athletes, coaches, referees, team managers)
- Swimming team management
- Swimming pool facility management
- Member role and team assignments
- Inter-service communication through RabbitMQ


### 3. CompetitionService

Port: 8002  
Purpose: Manages swimming competitions, meetings, events, entries, and results

#### Key Responsibilities

- Swimming meeting (competition) management
- Swim event management
- Athlete entry management
- Competition result tracking
- Referee assignment
- Inter-service federation member validation


## Deployment

### Docker Compose Setup

All services are containerized and orchestrated with Docker Compose:

```bash
docker-compose up
```

### Services Running
- **AuthService**: http://localhost:8000
- **FederationService**: http://localhost:8001
- **CompetitionService**: http://localhost:8002
- **NGINX Proxy**: http://localhost:9000
- **PostgreSQL**: Multiple instances (one per service)
- **RabbitMQ**: http://localhost:15672 (Management UI)

### Configuration

Environment variables control:
- Database URLs and credentials
- JWT algorithm and key paths
- Token expiration times
- RabbitMQ connection parameters
- CORS origins
- Log levels

## API Documentation

Each service exposes interactive API documentation:

- **AuthService**: http://localhost:8000/docs
- **FederationService**: http://localhost:8001/docs
- **CompetitionService**: http://localhost:8002/docs



### Missing features

We were unable to implement the live race results feature however, the system's event-driven architecture is fully prepared to support this capability in the future; by leveraging RabbitMQ and integrating WebSockets.


