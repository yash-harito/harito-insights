# Workspace Guidelines: Harito Insights

## Skill & Architecture
* **Primary Skill**: `.agents/skills/harito-insights/SKILL.md`
* **API Client**: Always use `HaritoClient` from `harito_client.py` for querying Harito API endpoints.
  * Do NOT create new one-off scripts with repetitive `requests.get` boilerplate.
  * `HaritoClient` automatically manages Bearer token loading, 0.25s rate-limit throttling, exponential backoff retries, and test-account filtering.

## Authentication
* Authentication uses the `TOKEN` variable from `.env`.
* **NEVER** output or print the Bearer token in the chat.
* If a 401 Unauthorized status is returned, notify the user that their token in `.env` is expired.

## File Organization Rules
To keep this repository clean and structured:
1. **Never write one-off scripts in the root directory**. Use the scratch directory or `archive/`.
2. **Output Reports (`reports/`)**: All exports (`.csv`, `.xlsx`, `.html`, `.md`) requested by the user must be saved in `reports/`.
3. **Data Dumps (`data/raw/`)**: Large API JSON payloads or cached dumps must be placed in `data/raw/`.
4. **Processed Data (`data/processed/`)**: Normalized or aggregated datasets go to `data/processed/`.
