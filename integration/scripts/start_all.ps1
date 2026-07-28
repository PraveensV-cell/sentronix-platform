Write-Host ""
Write-Host "========================================="
Write-Host " Starting Sentronix Backend Platform"
Write-Host "========================================="
Write-Host ""

docker compose up -d --build

Write-Host ""
Write-Host "All services started."
Write-Host ""
Write-Host "API Gateway : http://localhost:8000"
Write-Host "Swagger     : http://localhost:8000/docs"
