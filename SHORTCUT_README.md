# Create a Windows Shortcut

## Manual

1. Right-click the desktop and choose **New → Shortcut**.
2. Set the target to the repository's `AI Workstation Launcher.vbs` file.
3. Name the shortcut `AI Workstation`.

## PowerShell

Run this command from the project root:

```powershell
$WshShell = New-Object -ComObject WScript.Shell
$ProjectRoot = (Get-Location).Path
$Shortcut = $WshShell.CreateShortcut("$([Environment]::GetFolderPath('Desktop'))\AI Workstation.lnk")
$Shortcut.TargetPath = Join-Path $ProjectRoot 'AI Workstation Launcher.vbs'
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.Description = 'AI Workstation Dashboard'
$Shortcut.Save()
```

The launcher starts the Windows tray process, scheduler, and Kindle server using the current repository location. Do not hard-code a personal drive or username into the shortcut.