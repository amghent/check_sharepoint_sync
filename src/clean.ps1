Get-ChildItem -Path "C:\PythonApps\check_sharepoint_sync\logs" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } | Remove-Item