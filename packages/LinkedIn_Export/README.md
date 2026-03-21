# LinkedIn Network - Import and Query Your Network

Import LinkedIn connections into Qdrant for intelligent networking.

## Usage

```python
from linkedin_network import LinkedInImporter

importer = LinkedInImporter()

# Import connections
importer.import_connections("path/to/Connections.csv")

# Query your network
results = importer.find_by_role("recruiter")
results = importer.find_by_company("NVIDIA")
results = importer.find_by_skill("python")
```

## Features

- Import LinkedIn connections to Qdrant
- Search by role, company, or skill
- Find people for job opportunities

## Status

✅ Production Ready
