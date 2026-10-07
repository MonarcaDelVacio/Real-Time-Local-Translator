; Inno Setup script for the packaged desktop application.
; Models are intentionally not embedded here until the final package size and licensing are validated.

#define MyAppName "Real-Time Local Translator"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "MonarcaDelVacio"

[Setup]
AppId={{A8D0B7E1-4A95-4D6E-9E5A-RTLTRANSLATOR01}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Real-Time Local Translator
DisableProgramGroupPage=yes
OutputBaseFilename=RealTimeLocalTranslatorSetup

[Files]
Source: "..\dist\RealTimeLocalTranslator\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{autodesktop}\Real-Time Local Translator"; Filename: "{app}\RealTimeLocalTranslator.exe"
Name: "{autoprograms}\Real-Time Local Translator"; Filename: "{app}\RealTimeLocalTranslator.exe"
