# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in AgentProbe, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please email **security@agentprobe.dev** with:

1. A description of the vulnerability
2. Steps to reproduce the issue
3. Potential impact assessment
4. Any suggested fixes (optional)

You can expect:
- **Acknowledgment** within 48 hours
- **Initial assessment** within 5 business days
- **Fix timeline** communicated within 10 business days

## Scope

The following are in scope:
- SQL injection in storage backends
- Path traversal in file operations
- PII leakage through trace storage or reporting
- Authentication/authorization bypass in the dashboard API
- Dependency vulnerabilities in direct dependencies

The following are out of scope:
- Vulnerabilities in agent code being tested (that's the user's responsibility)
- Issues requiring physical access to the machine
- Social engineering attacks

## Security Best Practices

When using AgentProbe:
- Store API keys in environment variables, never in config files or code
- Use the PII redactor before storing traces that may contain sensitive data
- Run the dashboard behind a reverse proxy with authentication in production
- Review trace data before sharing — it may contain agent inputs/outputs with sensitive content
