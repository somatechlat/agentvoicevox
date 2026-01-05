# Technology Stack

## Blog (Root Project)
- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS 3.x with dark mode support
- **Content**: Markdown with gray-matter, remark, rehype-highlight
- **React**: 19.0.0-rc

## AgentVoiceBox Engine (Django Backend)
- **Framework**: Django 5.x with Django REST Framework
- **Database**: PostgreSQL 16 with Django ORM
- **Cache/Sessions**: Redis 7 with django-redis
- **Auth**: Keycloak 24, JWT validation via djangorestframework-simplejwt
- **Billing**: Lago
- **Policy**: OPA (Open Policy Agent)
- **Linting**: Ruff, Black (line-length: 100)
- **Testing**: pytest-django with Hypothesis (property-based testing)

## Portal Frontend (Next.js)
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS with Radix UI primitives
- **State**: TanStack React Query
- **Forms**: react-hook-form + zod validation
- **Charts**: Recharts
- **Testing**: Vitest + Testing Library + fast-check (property tests)

## Workers
- **STT**: Faster-Whisper (tiny model, CPU/int8)
- **TTS**: Kokoro models
- **LLM**: Groq/OpenAI API integration

## Infrastructure
- **Containers**: Docker Compose (project: agentvoicebox)
- **Monitoring**: Prometheus + Grafana
- **Port Range**: 65000-65099
- **RAM Budget**: 15GB Total

### Port Allocation
| Port | Service |
|------|---------|
| 65000 | Django Backend API |
| 65001 | Temporal Server |
| 65002 | Temporal UI |
| 65003 | Vault |
| 65004 | PostgreSQL |
| 65005 | Redis |
| 65006 | Keycloak |
| 65009 | Nginx HTTP |
| 65010 | Nginx HTTPS |
| 65011 | Prometheus |
| 65012 | Grafana |
| 65013 | Portal Frontend (Main UI) |

---

## Common Commands

### Blog (Root)
```bash
npm run dev          # Start dev server with Turbopack
npm run build        # Production build
npm run start        # Start production server
```

### AgentVoiceBox Backend
```bash
make install-dev     # Install dependencies
make format          # Format with Black
make lint            # Lint with Ruff
make check           # Verify formatting + linting
make test            # Run pytest

# Docker Cluster Commands
docker compose -p agentvoicebox up -d      # Start full stack
docker compose -p agentvoicebox down       # Stop and cleanup
docker compose -p agentvoicebox logs -f    # Tail container logs
docker compose -p agentvoicebox ps         # List running containers
```

### Portal Frontend
```bash
npm run dev          # Start dev server (port 3000)
npm run build        # Production build
npm run lint         # ESLint
npm run type-check   # TypeScript check
npm run test         # Vitest (single run)
npm run test:watch   # Vitest watch mode
npm run test:coverage # Coverage report
```
