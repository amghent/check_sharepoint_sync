cd C:\PythonApps\check_sharepoint_sync

git config --global http.sslVerify false
git checkout main
git pull origin
git config --global http.sslVerify true