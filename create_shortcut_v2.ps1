$WshShell = New-Object -comObject WScript.Shell
$Desktop = $WshShell.SpecialFolders.Item("Desktop")
$ShortcutPath = "$Desktop\TITAN FUSION QUANTUM.lnk"

# Usa USERPROFILE para evitar problemas de encoding com "Valério"
$BaseDir = "$env:USERPROFILE\Desktop\Titan pro"
$TargetPath = "$BaseDir\TitanFusion_Launcher.bat"
$IconPath = "c:\windows\system32\shell32.dll,15"

Write-Host "Target Path: $TargetPath"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetPath
$Shortcut.WorkingDirectory = $BaseDir
$Shortcut.IconLocation = $IconPath
$Shortcut.Description = "Iniciar Titan Fusion Quantum AI"
$Shortcut.Save()

Write-Host "Atalho recriado com sucesso apontando para: $TargetPath"
