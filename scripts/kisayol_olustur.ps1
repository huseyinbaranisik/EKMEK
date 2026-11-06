# Ekmek AI Asistan - Masaüstü Kısayol Oluşturma Betiği
# Bu betik, uygulama için masaüstünde bir kısayol oluşturur.

$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath('Desktop')
$Shortcut = $WshShell.CreateShortcut("$DesktopPath\Ekmek AI.lnk")

$ProjectRoot = (Get-Item $PSScriptRoot).Parent.FullName

# Çalıştırılacak hedef (npm start yerine doğrudan electron exe'sini kullanıyoruz ki terminal açılmasın)
$Shortcut.TargetPath = "$ProjectRoot\node_modules\electron\dist\electron.exe"
$Shortcut.Arguments = "."
$Shortcut.WorkingDirectory = "$ProjectRoot"
$Shortcut.WindowStyle = 1 # Normal başlat
$Shortcut.IconLocation = "$ProjectRoot\assets\icon.png"
$Shortcut.Description = "Ekmek AI Asistanı Başlat"

$Shortcut.Save()

Write-Host "Kısayol başarıyla masaüstüne oluşturuldu!" -ForegroundColor Green
