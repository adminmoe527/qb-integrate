; Inno Setup script for QB Local App
; Build with: iscc installer\installer.iss
; Expects the following sibling folders (populated by build.ps1):
;   staging\python\        -- extracted python-3.11.x-embed-amd64
;   staging\wheels\        -- offline pip wheelhouse (pywin32, fastapi, ...)
;   staging\qb_app\        -- the qb_app source tree
;   staging\vendor\QBSDK160.exe  -- bundled Intuit SDK installer
;   staging\htmx.min.js    -- real htmx bundle (replaces the stub)

#define AppName "QB Local App"
#define AppVersion "0.1.1"
#define Publisher "QB Local App"
#define AppURL "https://example.invalid/qb-local-app"

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#Publisher}
AppPublisherURL={#AppURL}
DefaultDirName={localappdata}\QBLocalApp
DefaultGroupName={#AppName}
DisableDirPage=yes
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputBaseFilename=QBLocalApp-Setup
OutputDir=..\dist
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayName={#AppName}
SetupIconFile=
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\staging\python\*"; DestDir: "{app}\python"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\staging\wheels\*"; DestDir: "{app}\wheels"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\staging\qb_app\*"; DestDir: "{app}\qb_app"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\staging\vendor\QBSDK160.exe"; DestDir: "{app}\vendor"; Flags: ignoreversion
Source: "..\staging\htmx.min.js"; DestDir: "{app}\qb_app\app\static"; Flags: ignoreversion
Source: "..\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\python\pythonw.exe"; Parameters: "-m qb_app.launcher"; WorkingDir: "{app}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\python\pythonw.exe"; Parameters: "-m qb_app.launcher"; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"

[Tasks]
Name: "desktopicon"; Description: "Create a Desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
; 1) Enable 'site' in the embeddable distro so pip works
Filename: "{sys}\cmd.exe"; Parameters: "/C echo import site >> ""{app}\python\python311._pth"""; Flags: runhidden
; 2) Bootstrap pip
Filename: "{app}\python\python.exe"; Parameters: "-m ensurepip"; Flags: runhidden
; 3) Install dependencies from bundled wheelhouse (fully offline)
Filename: "{app}\python\python.exe"; Parameters: "-m pip install --no-index --find-links ""{app}\wheels"" -r ""{app}\requirements.txt"""; Flags: runhidden
; 4) Register pywin32 COM helpers
Filename: "{app}\python\python.exe"; Parameters: """{app}\python\Scripts\pywin32_postinstall.py"" -install"; Flags: runhidden skipifdoesntexist
; 5) Launch the app for first run (opens browser to /setup)
Filename: "{app}\python\pythonw.exe"; Parameters: "-m qb_app.launcher"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM pythonw.exe"; Flags: runhidden

[UninstallDelete]
Type: filesandordirs; Name: "{app}\python"
Type: filesandordirs; Name: "{app}\wheels"
Type: filesandordirs; Name: "{app}\vendor"
Type: filesandordirs; Name: "{app}\qb_app"

[Messages]
WelcomeLabel2=This will install {#AppName} version {#AppVersion} on your computer.%n%nThe installer is unsigned, so Windows SmartScreen may warn "Unknown publisher" — click "More info" then "Run anyway" to continue.
