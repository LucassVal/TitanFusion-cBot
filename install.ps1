# Titan Pro - One-Line Installer
# Inspired by ChrisTitusTech's WinUtil
# Usage: irm https://raw.githubusercontent.com/LucassVal/TitanFusion-cBot/main/install.ps1 | iex

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   🚀 TITAN PRO - HYBRID GPU TRADING SYSTEM" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$repo = "LucassVal/TitanFusion-cBot"
$branch = "main"
$installPath = "$env:USERPROFILE\TitanPro"

# Check if already installed
if (Test-Path $installPath) {
    Write-Host "⚠️  Titan Pro already installed at: $installPath" -ForegroundColor Yellow
    $update = Read-Host "Update to latest version? (y/n)"
    
    if ($update -ne 'y') {
        Write-Host "Installation cancelled." -ForegroundColor Red
        exit
    }
    
    Write-Host "🔄 Updating..." -ForegroundColor Green
    Remove-Item -Recurse -Force $installPath
}

# Create directory
Write-Host "📁 Creating installation directory..." -ForegroundColor Green
New-Item -ItemType Directory -Path $installPath -Force | Out-Null

# Download repository
Write-Host "📥 Downloading Titan Pro from GitHub..." -ForegroundColor Green
$zipUrl = "https://github.com/$repo/archive/refs/heads/$branch.zip"
$zipPath = "$env:TEMP\TitanPro.zip"

try {
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing
    Write-Host "✅ Download complete!" -ForegroundColor Green
} catch {
    Write-Host "❌ Download failed: $_" -ForegroundColor Red
    exit 1
}

# Extract
Write-Host "📦 Extracting files..." -ForegroundColor Green
Expand-Archive -Path $zipPath -DestinationPath "$env:TEMP\TitanProExtract" -Force

# Move files
$extractedFolder = Get-ChildItem "$env:TEMP\TitanProExtract" | Select-Object -First 1
Copy-Item "$($extractedFolder.FullName)\*" -Destination $installPath -Recurse -Force

# Cleanup
Remove-Item $zipPath -Force
Remove-Item "$env:TEMP\TitanProExtract" -Recurse -Force

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   ✅ INSTALLATION COMPLETE!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Installed at: $installPath" -ForegroundColor Yellow
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Install Python 3.12: https://www.python.org/downloads/"
Write-Host "   2. Install dependencies:"
Write-Host "      cd '$installPath\Titan pro'"
Write-Host "      pip install pandas pandas_ta numpy pyopencl websockets"
Write-Host ""
Write-Host "   3. Run Titan Pro:"
Write-Host "      python launcher.py"
Write-Host ""
Write-Host "📖 Documentation: https://github.com/$repo" -ForegroundColor Cyan
Write-Host ""

# Ask to open folder
$openFolder = Read-Host "Open installation folder? (y/n)"
if ($openFolder -eq 'y') {
    explorer $installPath
}

# Ask to create desktop shortcut
$createShortcut = Read-Host "Create desktop shortcut? (y/n)"
if ($createShortcut -eq 'y') {
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Titan Pro.lnk")
    $Shortcut.TargetPath = "python.exe"
    $Shortcut.Arguments = "`"$installPath\Titan pro\launcher.py`""
    $Shortcut.WorkingDirectory = "$installPath\Titan pro"
    $Shortcut.IconLocation = "python.exe"
    $Shortcut.Description = "Titan Pro Trading System"
    $Shortcut.Save()
    
    Write-Host "✅ Desktop shortcut created!" -ForegroundColor Green
}

Write-Host ""
Write-Host "🎉 Ready to trade! Launch with: python '$installPath\Titan pro\launcher.py'" -ForegroundColor Yellow
Write-Host ""
