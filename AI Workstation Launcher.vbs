Set WshShell = CreateObject("WScript.Shell")
Set FileSystem = CreateObject("Scripting.FileSystemObject")
WshShell.CurrentDirectory = FileSystem.GetParentFolderName(WScript.ScriptFullName)
WshShell.Run "cmd /c python -m app.tray", 0, False