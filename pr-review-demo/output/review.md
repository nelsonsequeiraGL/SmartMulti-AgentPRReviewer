## AI PR Review

### Top Issues (top 3 by severity)

- **high** `src/api/users.py:5-6` — SQL Injection Risk
  - *Suggestion:* Use parameterized queries to safely include user input in SQL statements.

- **med** `src/api/users.py:8-9` — Inefficient Query Execution
  - *Suggestion:* Consider fetching all necessary data in a single query or using a JOIN to reduce the number of database calls.

- **med** `src/api/users.py:18-18` — Error Handling
  - *Suggestion:* Consider logging the exception or providing more specific error messages.


### Findings by File

**src/api/users.py**
- **high** `src/api/users.py:5-6` — SQL Injection Risk
- **med** `src/api/users.py:8-9` — Inefficient Query Execution
- **med** `src/api/users.py:18-18` — Error Handling


### Suggested Checklist

- [ ] Fix high-severity security issues
- [ ] Add validation / error handling
- [ ] Add pagination / batching
- [ ] Add tests