# exit-stack-container

Async lifecycle management with declarative dependency injection for Python 3.13+.

Automatically initialize and cleanup application resources (database connections, caches, clients) when your app starts and stops using async context manager pattern.

## Installation

```bash
pip install exit-stack-container
```

## Quick Start

```python
from msgspec import Struct
from msgspec_settings import BaseSettings

from exit_stack_container import AsyncExitStackContainer, BaseResources, Dependency, on_exit


class Database:
    def __init__(self, host: str, port: int):
        print(f"Database connected to {host}:{port}")

    def close(self):
        print("Database connection closed")


@on_exit(lambda db: db.close)
def create_database(*, host: str, port: int) -> Database:
    return Database(host=host, port=port)


class DatabaseSettings(Struct, frozen=True):
    host: str = "localhost"
    port: int = 5432

class AppSettings(BaseSettings):
    database: DatabaseSettings

class AppResources(BaseResources[AppSettings]):
    database: Database

class AppContainer(AsyncExitStackContainer[AppSettings, AppResources]):
    _settings: AppSettings = AppSettings()

    database: Dependency = Dependency(
        create_database,
        host=_settings.database.host,
        port=_settings.database.port,
    )


# Use with async context manager - automatic init and cleanup
async def main():
    async with AppContainer() as resources:
        # resources.database is ready to use
        # cleanup happens automatically on exit
        pass
```

## Features

- **Declarative DI** — Define dependencies with type-safe descriptors
- **Async lifecycle** — Automatic resource initialization and cleanup via async context manager
- **Topological sorting** — Dependencies resolved in correct order automatically
- **Circular detection** — Prevents circular dependency issues at runtime
- **Single active context** — Container cannot be re-entered before exiting

## License

MIT
