; Inno Setup script for the packaged desktop application.

#define MyAppName "Real-Time Local Translator"
#define MyAppVersion "0.2.0"
#define MyAppPublisher "MonarcaDelVacio"

[Setup]
AppId={{A8D0B7E1-4A95-4D6E-9E5A-RTLTRANSLATOR01}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Real-Time Local Translator
DisableProgramGroupPage=yes
OutputBaseFilename=RealTimeLocalTranslatorSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\RealTimeLocalTranslator.exe

[Files]
Source: "..\dist\RealTimeLocalTranslator\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{autodesktop}\Real-Time Local Translator"; Filename: "{app}\RealTimeLocalTranslator.exe"
Name: "{autoprograms}\Real-Time Local Translator"; Filename: "{app}\RealTimeLocalTranslator.exe"

[Run]
Filename: "{app}\RealTimeLocalTranslator.exe"; Description: "Iniciar Real-Time Local Translator"; Flags: nowait postinstall skipifsilent
