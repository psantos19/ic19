$tomorrow = (Get-Date).AddDays(1).ToString("yyyy-MM-dd")
Invoke-WebRequest -Method POST -Uri "http://localhost:8000/admin/generate?date_str=$tomorrow" | Out-Null
