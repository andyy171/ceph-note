#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Config
ROOT = Path.cwd()
EXCLUDE_DIRS = {'images', '.git', '.github'}  # exclude images by default
FILE_GLOB = '**/*.md'
MIN_BASE64_LEN = 40   # long base64-ish strings to consider
MAX_SNIPPET_LEN = 160

# Patterns: tuple(name, compiled_regex, description)
PATTERNS = [
    ("PEM_PRIVATE_KEY", re.compile(r'-----BEGIN (?:RSA )?PRIVATE KEY-----', re.IGNORECASE),
     "Private key block (PEM)"),
    ("OPENSSH_PRIVATE_KEY", re.compile(r'-----BEGIN OPENSSH PRIVATE KEY-----', re.IGNORECASE),
     "OpenSSH private key block"),
    ("AWS_ACCESS_KEY_ID", re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
     "AWS Access Key ID (AKIA...)"),
    ("AWS_SECRET_KEY", re.compile(r'(?<![A-Za-z0-9/+=])[A-Za-z0-9/+/=]{40}(?![A-Za-z0-9/+/=])'),
     "Likely AWS Secret Access Key or similar 40-char secret"),
    ("JWT", re.compile(r'\b[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\b'),
     "Possible JWT (header.payload.signature)"),
    ("LONG_BASE64", re.compile(r'(?<![A-Za-z0-9/+=])[A-Za-z0-9/+/=]{' + str(MIN_BASE64_LEN) + r',}(?![A-Za-z0-9/+=])'),
     "Long base64-like string"),
    ("SSH_PEM_KEYLINE", re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----', re.IGNORECASE),
     "Private key block line"),
    ("SECRET_ASSIGN", re.compile(r'(?i)\b(secret|api[_-]?key|apikey|token|passwd|password|client_secret|access_secret)\b\s*[:=]\s*([^\s\'\"`]+)'),
     "Key/secret assigned in-line (secret = ... / token: ...)"),
    ("KEY_IN_NAME", re.compile(r'(?i)key[_-]?(id|secret)?\b'),
     "Filename or token containing 'key' (heuristic)"),
]

def redact(s: str, keep_front=4, keep_back=4) -> str:
    s = s.strip()
    if len(s) <= keep_front + keep_back + 4:
        # short -> mask middle
        if len(s) <= 8:
            return s[0:1] + '***' + s[-1:] if len(s) > 1 else '***'
        return s[0:2] + '***' + s[-2:]
    return s[:keep_front] + '...' + s[-keep_back:]

def is_excluded(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    return False

def scan_file(path: Path) -> List[Tuple[str,int,str]]:
    findings = []
    try:
        text = path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return findings
    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        # quick skip empty
        if not line.strip():
            continue
        for name, regex, desc in PATTERNS:
            for m in regex.finditer(line):
                raw = m.group(0)
                # redact to avoid printing full secret
                red = redact(raw)
                # keep snippet context
                snippet = line.strip()
                if len(snippet) > MAX_SNIPPET_LEN:
                    snippet = snippet[:MAX_SNIPPET_LEN] + '...'
                findings.append((name, i, red))
    return findings

def main():
    md_files = list(ROOT.glob(FILE_GLOB))
    md_files = [p for p in md_files if p.is_file() and not is_excluded(p)]
    total_findings = 0
    report = []
    for p in sorted(md_files):
        f = scan_file(p)
        if f:
            report.append((p, f))
            total_findings += len(f)

    if total_findings == 0:
        print("✅ No suspicious secrets found in markdown files scanned.")
        sys.exit(0)

    print("⚠️  Potential secrets detected in markdown files:")
    print()
    for p, items in report:
        print(f"File: {p}")
        for name, lineno, red in items:
            print(f"  - [{name}] line {lineno}: {red}")
        print()
    print("----")
    print(f"Total suspicious matches: {total_findings}")
    print()
    print("Guidance:")
    print("- If these are false positives (placeholders like 'your_keyring'), consider leaving a comment above them or use an obviously safe placeholder (e.g., YOUR_KEY_PLACEHOLDER).")
    print("- If these are real secrets, REMOVE them and rotate the secret in the real system.")
    sys.exit(1)

if __name__ == '__main__':
    main()

# EOF