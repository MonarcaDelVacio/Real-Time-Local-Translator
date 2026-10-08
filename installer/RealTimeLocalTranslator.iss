; Inno Setup script for the packaged desktop application.

#define MyAppName "Real-Time Local Translator"
#define MyAppVersion "0.3.1"
#define MyAppPublisher "MonarcaDelVacio"

[Setup]
AppId={{A8D0B7E1-4A95-4D6E-9E5A-RTLTRANSLATOR01}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Real-Time Local Translator
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir={#SourcePath}\..\dist\installer
OutputBaseFilename=RealTimeLocalTranslatorSetup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
UninstallDisplayIcon={app}\RealTimeLocalTranslator.exe

[Files]
Source: "..\dist\RealTimeLocalTranslator\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
Source: "..\redist\vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{autodesktop}\Real-Time Local Translator"; Filename: "{app}\RealTimeLocalTranslator.exe"
Name: "{autoprograms}\Real-Time Local Translator"; Filename: "{app}\RealTimeLocalTranslator.exe"

[Run]
Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/install /quiet /norestart"; StatusMsg: "Instalando componente Microsoft Visual C++ necesario…"; Flags: waituntilterminated
Filename: "{app}\RealTimeLocalTranslator.exe"; Description: "Iniciar Real-Time Local Translator"; Flags: nowait postinstall skipifsilent
