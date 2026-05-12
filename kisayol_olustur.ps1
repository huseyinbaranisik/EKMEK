# Ekmek AI Asistan - Masaüstü Kısayol Oluşturma Betiği
# Bu betik, uygulama için masaüstünde bir kısayol oluşturur.

$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath('Desktop')
$Shortcut = $WshShell.CreateShortcut("$DesktopPath\Ekmek AI.lnk")

# Çalıştırılacak hedef (npm start)
$Shortcut.TargetPath = "npm.cmd"
$Shortcut.Arguments = "start"
$Shortcut.WorkingDirectory = "$PSScriptRoot"
$Shortcut.WindowStyle = 7 # Minimize edilmiş başlat
$Shortcut.IconLocation = "$PSScriptRoot\icon.png"
$Shortcut.Description = "Ekmek AI Asistanı Başlat"

$Shortcut.Save()

Write-Host "Kısayol başarıyla masaüstüne oluşturuldu!" -ForegroundColor Green
