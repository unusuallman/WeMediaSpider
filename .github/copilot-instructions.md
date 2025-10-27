# AI Coding Agent Instructions for WeMediaSpider

## Project Overview
WeMediaSpider is a Python-based tool for scraping content from multiple platforms, with a primary focus on WeChat public accounts. It supports functionalities like login automation, content scraping, and data storage in various formats (CSV, SQLite, MySQL, PostgreSQL). The project is modular, with clear separation of concerns across components.

### Key Components
- **`main.py`**: Entry point for command-line operations.
- **`scheduled_spider.py`**: Script for periodic scraping tasks using the `schedule` library.
- **`spider/`**: Core directory containing submodules:
  - **`db/`**: Database-related logic, including factory methods and ORM models.
  - **`log/`**: Logging utilities.
  - **`wechat/`**: WeChat-specific scraping logic, including login, scraping, and utility functions.

### Data Flow
1. **Login**: Uses Selenium to authenticate with WeChat and retrieve cookies.
2. **Scraping**: Fetches public account articles based on user input or predefined schedules.
3. **Storage**: Saves data in CSV or database (SQLite, MySQL, PostgreSQL).

## Developer Workflows

### Running the Project
- **Command-line interface**:
  ```bash
  python main.py wechat login
  python main.py wechat search "公众号名称" -o output.json
  ```
- **Scheduled scraping**:
  ```bash
  python scheduled_spider.py
  ```
  Modify `CONFIG` in `scheduled_spider.py` for custom schedules.

### Database Setup
- Default: SQLite (no additional setup required).
- For MySQL/PostgreSQL:
  Install dependencies:
  ```bash
  pip install pymysql psycopg2
  ```
  Update database configuration in `spider/db/factory.py`.

### Testing
- No explicit test framework is integrated. Add tests under a `tests/` directory if needed.

## Project-Specific Conventions

### Code Organization
- **Modular Design**: Each submodule in `spider/` handles a specific responsibility (e.g., `db/` for database, `wechat/` for WeChat scraping).
- **Factory Pattern**: Used in `spider/db/factory.py` for creating database instances.
- **ORM**: SQLAlchemy is used for database interactions.

### Logging
- Use `loguru` for logging. Configure log levels and output in `spider/log/utils.py`.

### Configuration
- Default configurations are hardcoded in scripts (e.g., `CONFIG` in `scheduled_spider.py`).
- Modify these directly or refactor to use environment variables for better flexibility.

## Integration Points
- **Selenium**: Automates browser interactions for WeChat login.
- **SQLAlchemy**: Provides ORM for database operations.
- **schedule**: Manages periodic scraping tasks.

## Examples

### Adding a New Scraping Platform
1. Create a new submodule under `spider/` (e.g., `spider/weibo/`).
2. Implement platform-specific logic (e.g., login, scraping).
3. Update `main.py` and `scheduled_spider.py` to include the new platform.

### Extending Database Support
1. Add a new database type in `spider/db/factory.py`.
2. Implement connection logic and ORM models.
3. Test with sample data.

## Notes for AI Agents
- Follow the modular structure when adding new features.
- Ensure compatibility with Python 3.12+.
- Maintain existing logging and database patterns.
- Avoid hardcoding sensitive data (e.g., credentials). Use environment variables or configuration files.

## References
- **`README.md`**: Comprehensive guide to project setup and usage.
- **`spider/`**: Core logic for scraping, logging, and database operations.