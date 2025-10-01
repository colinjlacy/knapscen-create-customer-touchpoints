# Customer Touchpoints Creation Script

This Python script creates a new touchpoints record for a corporate customer in the MySQL database and publishes an event to NATS for downstream processing.

## Features

- ✅ Looks up corporate customer by name in the database
- ✅ Creates a new touchpoints record with empty date fields
- ✅ Publishes a `touchpoints-created` event to NATS
- ✅ Comprehensive error handling and logging
- ✅ Environment variable configuration
- ✅ Async/await support for NATS operations

## Database Schema

The script works with the following database tables:

- `corporate_customers` - Stores company information and subscription tiers
- `touchpoints` - Tracks CRM activities for each corporate customer

The touchpoints table has the following structure:
- `id` (UUID, Primary Key)
- `customer_id` (UUID, Foreign Key to corporate_customers)
- `welcome_outreach` (DATE, NULL)
- `technical_onboarding` (DATE, NULL)
- `follow_up_call` (DATE, NULL)
- `feedback_session` (DATE, NULL)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

## Prerequisites

1. Python 3.7+
2. MySQL database with the schema from `database_schema.sql`
3. NATS server running
4. Required Python packages (see requirements.txt)

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your environment variables (copy from `env.example`):
```bash
cp env.example .env
# Edit .env with your actual values
```

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DB_HOST` | MySQL database host | Yes | - |
| `DB_PORT` | MySQL database port | No | 3306 |
| `DB_NAME` | Database name | Yes | - |
| `DB_USER` | Database username | Yes | - |
| `DB_PASSWORD` | Database password | Yes | - |
| `NATS_URL` | NATS server URL | Yes | - |
| `NATS_SUBJECT` | NATS subject for publishing events | No | touchpoints-created |
| `NATS_USER` | NATS username for authentication | Yes | - |
| `NATS_PASSWORD` | NATS password for authentication | Yes | - |
| `CUSTOMER_NAME` | Name of corporate customer | Yes | - |

## Usage

### Command Line

```bash
python create_touchpoints.py
```

### Programmatic Usage

```python
import asyncio
from create_touchpoints import TouchpointsCreator

async def main():
    creator = TouchpointsCreator()
    success = await creator.create_touchpoints_for_customer()
    print(f"Success: {success}")

asyncio.run(main())
```

### Example Script

Run the example script to see it in action:

```bash
python run_example.py
```

## NATS Event

When a touchpoints record is created, the script publishes an event to the `touchpoints-created` subject with the following payload:

```json
{
  "event_type": "touchpoints-created",
  "timestamp": "2024-01-15T10:30:00Z",
  "touchpoints_id": "123e4567-e89b-12d3-a456-426614174000",
  "customer": {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "name": "TechCorp Solutions",
    "subscription_tier": "far-out",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-15T10:30:00"
  },
  "touchpoints": {
    "welcome_outreach": null,
    "technical_onboarding": null,
    "follow_up_call": null,
    "feedback_session": null
  },
  "next_actions": [
    "Schedule welcome outreach",
    "Plan technical onboarding session",
    "Set up follow-up call",
    "Arrange feedback session"
  ]
}
```

## Error Handling

The script includes comprehensive error handling for:

- Missing environment variables
- Database connection failures
- Customer not found
- Touchpoints creation failures
- NATS connection issues
- Event publishing failures

All errors are logged with appropriate detail levels.

## Logging

The script uses Python's built-in logging module with the following levels:

- `INFO`: General information about the process
- `ERROR`: Error conditions that prevent completion
- `WARNING`: Warning conditions (not currently used)

## Database Requirements

Make sure your MySQL database has:

1. The schema from `database_schema.sql` applied
2. At least one corporate customer record
3. Proper permissions for the database user

## NATS Requirements

Ensure your NATS server is:

1. Running and accessible at the configured URL
2. Configured to accept connections
3. Has the `touchpoints-created` subject available for publishing

## Troubleshooting

### Common Issues

1. **Customer not found**: Verify the customer name exists in the `corporate_customers` table
2. **Database connection failed**: Check database credentials and connectivity
3. **NATS connection failed**: Verify NATS server is running and accessible
4. **Missing environment variables**: Ensure all required variables are set

### Debug Mode

To enable more verbose logging, modify the logging level in the script:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Docker Usage

### Building the Image

```bash
# Build the Docker image
docker build -t touchpoints-creator .

# Run the container with environment variables
docker run --rm \
  -e DB_HOST=your-db-host \
  -e DB_NAME=your-db-name \
  -e DB_USER=your-db-user \
  -e DB_PASSWORD=your-db-password \
  -e NATS_URL=your-nats-url \
  -e NATS_USER=your-nats-user \
  -e NATS_PASSWORD=your-nats-password \
  -e CUSTOMER_NAME="Your Customer Name" \
  touchpoints-creator
```

### Using Docker Compose

For local development and testing, use the provided `docker-compose.yml`:

```bash
# Start all services (MySQL, NATS, and the touchpoints creator)
docker-compose up -d

# View logs
docker-compose logs -f touchpoints-creator

# Stop all services
docker-compose down
```

The docker-compose setup includes:
- MySQL 8.0 with the database schema automatically loaded
- NATS server with JetStream enabled
- The touchpoints creator service

### Multi-Architecture Images

The GitHub Actions workflow automatically builds and pushes multi-architecture images to GitHub Container Registry (GHCR):

- **AMD64** (x86_64)
- **ARM64** (Apple Silicon, ARM-based servers)

Images are available at: `ghcr.io/your-username/knapscen-create-customer-touchpoints`

### Image Tags

- `latest` - Latest version from main branch
- `v1.0.0` - Semantic version tags
- `main` - Latest from main branch
- `develop` - Latest from develop branch

## GitHub Actions

The repository includes a comprehensive CI/CD pipeline that:

1. **Builds multi-architecture Docker images** for AMD64 and ARM64
2. **Pushes to GitHub Container Registry** (GHCR)
3. **Runs security scans** using Trivy
4. **Generates build attestations** for supply chain security
5. **Triggers on**:
   - Push to main/develop branches
   - Pull requests to main
   - Version tags (v*)

### Required Permissions

The workflow includes the necessary GitHub permissions:
- `contents: read` - Read repository contents
- `packages: write` - Push to GHCR
- `id-token: write` - Generate OIDC tokens for authentication
- `security-events: write` - Upload security scan results

## License

This project is licensed under the same terms as the main project.