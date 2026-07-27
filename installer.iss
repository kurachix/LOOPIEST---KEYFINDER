; ==============================================================================
; INNO SETUP SCRIPT - LOOPIEST KEYFINDER INSTALLER
; Desenvolvido por @kxrachi & @willalvxrez
; ==============================================================================

[Setup]
AppId={{8A2BE200-L8PI-KEYF-INDE-R00000000001}}
AppName=LOOPIEST KEYFINDER
AppVerName=LOOPIEST KEYFINDER
AppPublisher=@kxrachi & @willalvxrez
AppPublisherURL=https://www.instagram.com/l8piest/
AppSupportURL=https://www.instagram.com/l8piest/
AppUpdatesURL=https://www.instagram.com/l8piest/
DefaultDirName={autopf}\LOOPIEST KEYFINDER
DefaultGroupName=LOOPIEST KEYFINDER
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=Loopiest_Setup
SetupIconFile=assets\logo.ico
WizardSmallImageFile=assets\logo.bmp
UninstallDisplayIcon={app}\LOOPIEST_KEYFINDER.exe
UninstallDisplayName=LOOPIEST KEYFINDER
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho (Desktop)"; GroupDescription: "Atalhos adicionais:"; Flags: unchecked
Name: "startmenuicon"; Description: "Adicionar ao Menu Iniciar"; GroupDescription: "Atalhos adicionais:"
Name: "taskbaricon"; Description: "Fixar na Barra de Tarefas (Taskbar)"; GroupDescription: "Atalhos adicionais:"

[Files]
Source: "dist\LOOPIEST_KEYFINDER\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\LOOPIEST KEYFINDER"; Filename: "{app}\LOOPIEST_KEYFINDER.exe"; Tasks: startmenuicon
Name: "{autodesktop}\LOOPIEST KEYFINDER"; Filename: "{app}\LOOPIEST_KEYFINDER.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar\LOOPIEST KEYFINDER"; Filename: "{app}\LOOPIEST_KEYFINDER.exe"; Tasks: taskbaricon

[Run]
Filename: "{app}\LOOPIEST_KEYFINDER.exe"; Description: "Executar o LOOPIEST KEYFINDER agora"; Flags: nowait postinstall skipifsilent
Filename: "https://www.instagram.com/l8piest/"; Flags: shellexec postinstall

[Messages]
brazilianportuguese.FinishedHeadingLabel=Instalação Concluída com Sucesso!
brazilianportuguese.FinishedLabel=Obrigado pela compra do LOOPIEST KEYFINDER!%n%nSoftware e Loopiest desenvolvidos por @kxrachi e @willalvxrez.
