#define MyAppName "ExpenseTracker"
#define MyAppVersion "1.0"
#define MyAppPublisher "Kavindu"
#define MyAppExeName "ExpenseTracker.exe"

[Setup]
AppId={{9C0D6E9F-0D79-4C4E-9D6B-3A0A6B0C8F11}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=output
OutputBaseFilename=ExpenseTrackerSetup
Compression=lzma
SolidCompression=yes

[Tasks]
Name: "desktopicon"; Description: "Create a Desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "dist\ExpenseTracker\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
