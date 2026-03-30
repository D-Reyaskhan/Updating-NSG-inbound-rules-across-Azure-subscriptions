<div align="center">

<img src="https://img.shields.io/badge/Azure-NSG%20Automation-0078D4?style=for-the-badge&logo=microsoftazure&logoColor=white"/>
<img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge"/>
<img src="https://img.shields.io/badge/DRY--RUN-Safe%20by%20Default-orange?style=for-the-badge"/>

<br><br>

# 🛡️ NSG Inbound Rule — IP Range Replacement
### Automate IP changes across all Azure NSGs and Subscriptions with Python

<br>

> **Replaced 80 NSG Inbound Rules across multiple Azure subscriptions — zero manual portal clicks.**

</div>

---

## 📖 What Is This?

When an IP range changes in your infrastructure, updating it manually across **every NSG rule in every subscription** through the Azure Portal is tedious and error-prone.

This Python script automates the entire process:

- ✅ Scans **all subscriptions** automatically
- ✅ Finds **every NSG** across all resource groups
- ✅ Updates **only rules that contain the old IP** — nothing else is touched
- ✅ Handles both **single IP** and **IP list** rule formats
- ✅ **DRY RUN mode** — preview all changes safely before applying

---

## 🗂️ How It Works

```
🔐 Authenticate to Azure (DefaultAzureCredential)
        │
        ▼
📦 List all enabled Subscriptions
        │
        ▼
🔒 List all NSGs in each Subscription
        │
        ▼
📋 Read Inbound Rules of each NSG
        │
        ├─── 🟢 Rule has OLD IP?  →  Replace with NEW IP  →  Push to Azure
        │
        └─── 🔵 Rule has no match?  →  Skip completely, no changes
```

---

## ⚙️ Requirements

**Install dependencies:**

```bash
pip install azure-identity azure-mgmt-network azure-mgmt-subscription
```

| Package | Purpose |
|---|---|
| `azure-identity` | Handles authentication (az login, Managed Identity, Service Principal) |
| `azure-mgmt-network` | Reads and updates NSG rules |
| `azure-mgmt-subscription` | Lists all Azure subscriptions |

---

## 🔐 Authentication

This script uses `DefaultAzureCredential` — it **automatically detects** your auth method:

<table>
  <tr>
    <th>Environment</th>
    <th>Method</th>
    <th>How to Set Up</th>
  </tr>
  <tr>
    <td>🖥️ Local Machine</td>
    <td>Azure CLI</td>
    <td><code>az login</code> — run once in terminal</td>
  </tr>
  <tr>
    <td>🤖 Azure DevOps Pipeline</td>
    <td>Service Principal</td>
    <td>Set env vars below</td>
  </tr>
  <tr>
    <td>☁️ Azure VM / App</td>
    <td>Managed Identity</td>
    <td>Enable on the VM — no extra config needed</td>
  </tr>
</table>

**For Service Principal (pipelines), set these environment variables:**

```bash
AZURE_CLIENT_ID      = <your-app-id>
AZURE_CLIENT_SECRET  = <your-secret>
AZURE_TENANT_ID      = <your-tenant-id>
```

---

## 👤 Required Azure RBAC Role

> The account or Service Principal running this script must have the **Network Contributor** role.

```
Subscription → Access Control (IAM) → Add Role Assignment → Network Contributor
```

💡 Assign at **Management Group level** to cover all subscriptions with a single assignment.

---

## 🛠️ Configuration

Open `nsg_ip_replace.py` and set these **4 values** at the top:

```python
# ─────────────────────────────────────────────
# ✏️  CONFIGURE THESE BEFORE RUNNING
# ─────────────────────────────────────────────
OLD_IP_RANGE = "x.x.x.x/32"       # ← IP range to be replaced
NEW_IP_RANGE = "x.x.x.x/32"       # ← Replacement IP range
DRY_RUN      = True                # ← Keep True for safe preview first
TARGET_SUBSCRIPTION_NAME = None    # ← Set a name to target one sub only (None = all)
```

---

## 🚀 Usage

### 🔍 Step 1 — Dry Run (Always Start Here)

```bash
python nsg_ip_replace.py
```

With `DRY_RUN = True`, the script **only logs** what would change — nothing is modified in Azure.
Review the output and confirm the right rules are listed.

---

### ✅ Step 2 — Live Run (Apply Changes)

Once satisfied with the dry run output, set `DRY_RUN = False` and run again:

```python
DRY_RUN = False
```

```bash
python nsg_ip_replace.py
```

> ⚠️ **Only flip to `False` after reviewing the dry run output carefully.**

---

## 📊 Sample Output

```log
2025-03-30 10:00:01 [INFO] NSG IP Range Replacement Tool
2025-03-30 10:00:01 [INFO] OLD IP: x.x.x.x/32 → NEW IP: x.x.x.x/32

2025-03-30 10:00:03 [INFO] Subscription: Production-Sub
2025-03-30 10:00:04 [INFO]   NSG: prod-app-nsg
2025-03-30 10:00:05 [INFO]     Rule 'Allow-App-Inbound': UPDATED  ✅
2025-03-30 10:00:05 [INFO]     Rule 'Allow-Health-Probe': SKIPPED  ⏭️
2025-03-30 10:00:06 [INFO]   NSG: prod-db-nsg
2025-03-30 10:00:07 [INFO]     Rule 'Allow-SQL-Access': SKIPPED  ⏭️

2025-03-30 10:00:10 [INFO] ── Run Complete ──
2025-03-30 10:00:10 [INFO] Total NSGs scanned  : 12
2025-03-30 10:00:10 [INFO] Total rules updated : 80
2025-03-30 10:00:10 [INFO] Mode                : LIVE
```

---

## 💡 Key Design Decisions

| Decision | Why |
|---|---|
| `DRY_RUN = True` by default | Always safe to clone and run without accidental changes |
| Exact CIDR string match | Prevents partial matches from modifying unintended rules |
| Handles both prefix field formats | `source_address_prefix` (single) and `source_address_prefixes` (list) are both checked |
| `TARGET_SUBSCRIPTION_NAME` filter | Test safely on one subscription before running across all |
| Skipped rules are logged | Full visibility — you can see exactly what was and wasn't changed |

---

## 📁 Project Structure

```
📦 nsg-ip-replace/
 ┣ 📜 nsg_ip_replace.py   ← Main automation script
 ┗ 📄 README.md           ← This file
```

---

## 🤝 Contributing

Feel free to fork this repo, raise issues, or submit pull requests.
If this helped you, drop a ⭐ on the repo!

---

<div align="center">

**Built by [Reyas](https://www.linkedin.com/in/) — DevOps & Cloud Engineer**
<br>
*Automating infrastructure, one script at a time.*

![Azure](https://img.shields.io/badge/Azure-Cloud-0078D4?style=flat-square&logo=microsoftazure)
![Python](https://img.shields.io/badge/Python-Automation-3776AB?style=flat-square&logo=python)
![DevOps](https://img.shields.io/badge/DevOps-Engineer-FF6B35?style=flat-square)

</div>
