import re
import os
from pathlib import Path

# Thư mục quét
BASE_DIR = Path(".")
TARGET_EXT = [".md"]

# Regex phát hiện chuỗi nghi ngờ (JWT, key, secret)
PATTERNS = {
    "JWT": re.compile(r"\b[A-Za-z0-9-_]{20,}\.[A-Za-z0-9-_]{20,}\.[A-Za-z0-9-_]{10,}\b"),
    "SECRET_ASSIGN": re.compile(r"(secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9+/=_-]{8,}['\"]?", re.IGNORECASE),
    "KEY_IN_NAME": re.compile(r"(?<!your_)(?<!sample_)\b(key|token|password|secret)\b", re.IGNORECASE),
}

# Danh sách pattern hoặc từ khóa để *bỏ qua*
SAFE_WORDS = [
    "192.168.", "localhost", "example.com", "download.ceph.com", "your_keyring",
    "YOUR_KEY_PLACEHOLDER", "cephadm", "ceph-", "host", "cluster", "curl", "apt", "sudo"
]

def is_safe_line(line: str):
    line_lower = line.lower()
    return any(word in line_lower for word in SAFE_WORDS)

def scan_file(filepath):
    results = []
    with open(filepath, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if is_safe_line(line):
                continue
            for name, pattern in PATTERNS.items():
                if pattern.search(line):
                    results.append((i, name, line.strip()))
    return results

def main():
    all_findings = {}
    for path in BASE_DIR.rglob("*"):
        if path.suffix in TARGET_EXT:
            findings = scan_file(path)
            if findings:
                all_findings[str(path)] = findings

    if not all_findings:
        print("✅ No secrets found in markdown files.")
        return

    print("⚠️ Potential secrets detected:\n")
    for file, issues in all_findings.items():
        print(f"File: {file}")
        for line_num, tag, content in issues:
            print(f"  - [{tag}] line {line_num}: {content[:60]}")
        print()

    print("----")
    print("Guidance:")
    print("- Use placeholders like `YOUR_KEY_PLACEHOLDER` or `example_value`.")
    print("- Review flagged lines manually before pushing to remote.\n")

if __name__ == "__main__":
    main()

