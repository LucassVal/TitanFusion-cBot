$WshShell = New-Object -comObject WScript.Shell
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "TITAN FUSION QUANTUM.lnk"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "c:\Users\Lucas Valério\Desktop\START_TITAN_QUANTUM.bat"
$Shortcut.WorkingDirectory = "c:\Users\Lucas Valério\Desktop\Titan pro"
$Shortcut.WindowStyle = 7 # Minimized (launcher) or 1 (Normal)
$Shortcut.Description = "Launch Titan Fusion Quantum AI"
# Usar icone de Chip/Processador do Windows (shell32.dll index 239 ou imageres.dll)
# shell32.dll, 239 = Chip
# imageres.dll, 98 = Chip Blue
$Shortcut.IconLocation = "shell32.dll, 239" 
$Shortcut.Save()
Write-Host "Shortcut created at $ShortcutPath"
