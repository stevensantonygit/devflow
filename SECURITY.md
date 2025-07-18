# Security Policy

## Supported Versions

Currently, only the latest version of DevFlow CLI is supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in DevFlow CLI, please report it responsibly:

### How to Report

1. **Do NOT** create a public GitHub issue for security vulnerabilities
2. Email the maintainer directly at [your-email] (replace with actual email)
3. Include detailed information about the vulnerability
4. Provide steps to reproduce the issue if possible

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fixes (optional)

### Response Timeline

- Initial response: Within 48 hours
- Status update: Within 1 week
- Fix timeline: Depends on severity, typically 1-4 weeks

### Security Considerations

DevFlow CLI is designed with security in mind:

- **Local Data Only**: All data is stored locally in SQLite database
- **No Network Requests**: Application doesn't send data over the network
- **File System Access**: Limited to user's home directory for data storage
- **No External Dependencies**: Uses only Python standard library
- **Input Validation**: User inputs are properly validated and sanitized

### Safe Usage

To use DevFlow CLI safely:

1. Only run from trusted sources
2. Review code before execution if downloaded from unofficial sources
3. Keep your Python installation up to date
4. Be cautious when using templates from untrusted sources

## Vulnerability Disclosure Timeline

1. Vulnerability reported
2. Acknowledgment sent to reporter
3. Investigation and verification
4. Fix developed and tested
5. Security advisory published (if applicable)
6. Fix released
7. Public disclosure (after fix is available)

Thank you for helping keep DevFlow CLI secure!
