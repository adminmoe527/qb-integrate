# QB Local App

A local Windows web app that sits on the same machine as QuickBooks Desktop Enterprise and gives you a browser-based UI to:

- Pull reports (P&L, Balance Sheet, A/R & A/P Aging, Inventory, Sales by Customer)
- Read customers, invoices, and items
- Create customers and invoices (with dry-run qbXML preview)
- Work with **multiple company files** (switch one at a time, or view combined reports across all)

Communication with QuickBooks uses the official **Intuit qbXML SDK** via the QBFC COM library. No internet connection or third-party account required.

## Install

1. Double-click **`QBLocalApp-Setup.exe`**. The installer is unsigned, so Windows SmartScreen will say *"Windows protected your PC — Unknown publisher"*. Click **More info → Run anyway**.
2. Click **Next → Install → Finish**. The installer:
   - Installs to `%LOCALAPPDATA%\QBLocalApp\` (per-user, no admin rights needed).
   - Unpacks embedded Python 3.11, installs dependencies from the bundled offline wheelhouse, and registers pywin32 COM helpers.
   - Creates Start Menu and Desktop shortcuts.
   - Launches the app, which opens your browser to the **Setup Wizard** at `http://localhost:8765/setup`.

## First-run Setup Wizard

The wizard walks you through:

1. **Welcome.**
2. **System check** — confirms the QuickBooks SDK is installed. If not, the wizard runs the bundled `QBSDK160.exe` silently for you.
3. **Detect version** — opens a harmless `HostQueryRq` probe to learn your QuickBooks Enterprise version and pick the matching qbXML version automatically.
4. **Pick folder** — enter the path to the folder that holds all your `.qbw` company files. The wizard scans it and registers each file.
5. **Authorize each file** — for each company file:
   1. Open QuickBooks as an **Admin** user in **single-user mode** and open the file.
   2. Click **Authorize** next to that file in the wizard.
   3. QuickBooks pops an "Application Certificate" dialog. Choose **"Yes, always; allow access even if QuickBooks is not running"** (this also enables future unattended runs).
   4. Repeat for the next file. You can switch QuickBooks back to multi-user mode once you've authorized all of them.
6. **Pick an integration user** (optional) — the QuickBooks user the app should act as when writing records.
7. **Smoke tests** — read 1 customer, run a small P&L, validate an invoice qbXML.
8. **Done** — the browser forwards to the Dashboard.

Re-run the wizard any time from **Settings → Re-run Setup Wizard** (useful after upgrading QuickBooks Enterprise 2025 → 2026).

## Daily use

Double-click the **QB Local App** Start Menu or Desktop shortcut. The launcher starts a tiny local web service and opens your browser to the Dashboard. Close the launcher window to stop the app.

- **Company switcher** in the top bar — switch the "active" file.
- **Dashboard** — at-a-glance tiles and recent-activity previews.
- **Reports** — pick a report + date range, run for the active company, or check *All companies* for a side-by-side combined view. Export to CSV or Excel.
- **Customers / Invoices** — searchable tables, create new records with **Dry run** preview.
- **Account Map** — map each company's chart-of-accounts names to a shared canonical set so combined reports can merge rows.
- **Settings** — change company folder, rescan, re-run wizard, view SDK info.

## Files & locations

| What | Where |
| --- | --- |
| App install | `%LOCALAPPDATA%\QBLocalApp\` |
| Config | `%LOCALAPPDATA%\QBLocalApp\config.toml` |
| Logs | `%LOCALAPPDATA%\QBLocalApp\logs\app.log` |
| Cache DB | `%LOCALAPPDATA%\QBLocalApp\cache.db` |
| Account map | `%LOCALAPPDATA%\QBLocalApp\account_map.toml` |

## Uninstall

**Settings → Add or Remove Programs → QB Local App → Uninstall**. Removes the app and all per-user data except the QuickBooks SDK itself (other apps may rely on it — uninstall it manually if you're sure).

## Troubleshooting

- **"QBFC not found"** — The Setup Wizard didn't install the SDK. Re-run the wizard and click **Install QuickBooks SDK**.
- **"Application has not accessed this QuickBooks company data file before"** — Run the wizard's Authorize step. QuickBooks must be in single-user mode with an Admin user logged in for that one step.
- **"Record in use"** when editing a customer/invoice — Another user has it open in QuickBooks. Try again in a moment.
- **Combined report numbers don't match individual runs** — Check your **Account Map**; unmapped accounts are excluded from combined totals and show a yellow banner.

## Running inside Parallels Desktop (macOS host)

Parallels is a fully supported host — the installer runs inside the Windows VM just like on a physical box. A few specifics:

- Install QuickBooks Desktop Enterprise **inside the VM**, not on the Mac side.
- **Keep company files on the VM's C: drive**, not on a Parallels Shared Folder pointing at your Mac filesystem. QuickBooks relies on real Windows file locking; shared-folder mounts can corrupt the `.ND` lock file.
- Recommended VM resources: 4 CPU cores, 8 GB RAM, Windows 10/11 Pro.
- On Apple Silicon Macs, Parallels runs Windows 11 ARM — QuickBooks Desktop Enterprise 2024+ and the QBFC16 COM library work under the built-in x64 emulation.
- Take a Parallels snapshot (`Actions → Take Snapshot`) before running the installer so you can roll back in seconds if anything misbehaves.
- You can use the app's UI from either the Windows browser inside the VM, or from your Mac browser at `http://<vm-ip>:8765` — but the service itself must run inside the VM.

## Developer build

Build from a clean Windows 10/11 machine (or the same Parallels VM you'll deploy to):

1. Install **Inno Setup 6** (https://jrsoftware.org/isinfo.php) and make sure `iscc.exe` is on PATH.
2. Install **Python 3.11 for Windows** (needed only to populate the offline wheelhouse).
3. Download Intuit's **QuickBooks SDK 16.0** (`QBSDK160.exe`) from <https://developer.intuit.com/app/developer/qbdesktop/docs/get-started/download-and-install-the-sdk> and drop it at `vendor\QBSDK160.exe` in the repo root.
4. From a PowerShell prompt at the repo root:
   ```powershell
   .\installer\build.ps1
   ```
   This downloads the embeddable Python runtime, downloads htmx, builds the offline wheelhouse via `pip download`, copies the `qb_app/` source, and runs Inno Setup. Output: `dist\QBLocalApp-Setup.exe`.
5. Copy the `.exe` to any target Windows machine (including the Parallels VM) and double-click to install.

## Roadmap (post-v1)

- Unattended / scheduled runs via Task Scheduler (`--headless` flag is already in place).
- Sync adapters (SQL Server, SaaS APIs, file drops).
- PyInstaller single-exe distribution.
- Code signing to eliminate the SmartScreen warning.
