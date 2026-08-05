[Setup]
AppName=VideoToMP3
AppVersion=1.0.0
DefaultDirName={autopf}\VideoToMP3
DefaultGroupName=VideoToMP3
OutputDir=dist
OutputBaseFilename=VideoToMP3-Setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\VideoToMP3.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\VideoToMP3"; Filename: "{app}\VideoToMP3.exe"
Name: "{autodesktop}\VideoToMP3"; Filename: "{app}\VideoToMP3.exe"

[Run]
Filename: "{app}\VideoToMP3.exe"; Description: "Ejecutar VideoToMP3"; Flags: nowait postinstall skipifsilent
