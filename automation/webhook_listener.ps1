# Webhook receiver for Power Automate HTTP triggers
# This can be used to trigger automation workflows via HTTP requests

param(
    [int]$Port = 8080,
    [string]$SecretKey = "your-secret-key-here",
    [switch]$Verbose = $false
)

Add-Type -AssemblyName System.Web

function Start-WebhookListener {
    param([int]$Port)
    
    $listener = New-Object System.Net.HttpListener
    $listener.Prefixes.Add("http://localhost:$Port/")
    $listener.Start()
    
    Write-Host "🚀 Webhook listener started on http://localhost:$Port"
    Write-Host "📝 Available endpoints:"
    Write-Host "   POST /webhook/deploy    - Trigger deployment"
    Write-Host "   POST /webhook/backup    - Trigger backup"
    Write-Host "   POST /webhook/test      - Run tests"
    Write-Host "   POST /webhook/status    - Get status"
    Write-Host "   POST /webhook/restart   - Restart services"
    Write-Host "   GET  /health           - Health check"
    Write-Host "⌨️  Press Ctrl+C to stop"
    Write-Host ""
    
    try {
        while ($listener.IsListening) {
            $context = $listener.GetContext()
            $request = $context.Request
            $response = $context.Response
            
            try {
                Handle-Request -Request $request -Response $response
            }
            catch {
                Write-Host "❌ Error handling request: $($_.Exception.Message)" -ForegroundColor Red
                Send-ErrorResponse -Response $response -Message $_.Exception.Message
            }
        }
    }
    finally {
        $listener.Stop()
        Write-Host "🛑 Webhook listener stopped"
    }
}

function Handle-Request {
    param($Request, $Response)
    
    $url = $Request.Url.AbsolutePath
    $method = $Request.HttpMethod
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    Write-Host "[$timestamp] $method $url" -ForegroundColor Cyan
    
    # Health check endpoint
    if ($url -eq "/health" -and $method -eq "GET") {
        Send-JsonResponse -Response $Response -Data @{
            status = "healthy"
            timestamp = $timestamp
            uptime = (Get-Date) - (Get-Process -Id $PID).StartTime
        }
        return
    }
    
    # Webhook endpoints
    if ($url.StartsWith("/webhook/") -and $method -eq "POST") {
        $action = $url.Substring(9)  # Remove "/webhook/" prefix
        
        # Read request body
        $reader = New-Object System.IO.StreamReader($Request.InputStream)
        $requestBody = $reader.ReadToEnd()
        $reader.Close()
        
        # Parse JSON if present
        $payload = @{}
        if ($requestBody) {
            try {
                $payload = $requestBody | ConvertFrom-Json -AsHashtable
            }
            catch {
                Write-Host "⚠️  Invalid JSON in request body" -ForegroundColor Yellow
            }
        }
        
        # Validate secret key
        if ($payload.ContainsKey("secret") -and $payload.secret -eq $SecretKey) {
            Write-Host "✅ Secret key validated" -ForegroundColor Green
        } elseif ($SecretKey -ne "your-secret-key-here") {
            Send-ErrorResponse -Response $Response -Message "Invalid or missing secret key" -StatusCode 401
            return
        }
        
        # Execute action
        $result = Invoke-AutomationAction -Action $action -Payload $payload
        Send-JsonResponse -Response $Response -Data $result
        return
    }
    
    # 404 for unknown endpoints
    Send-ErrorResponse -Response $Response -Message "Endpoint not found" -StatusCode 404
}

function Invoke-AutomationAction {
    param($Action, $Payload)
    
    $validActions = @("deploy", "backup", "test", "status", "restart")
    
    if ($Action -notin $validActions) {
        return @{
            success = $false
            message = "Invalid action. Valid actions: $($validActions -join ', ')"
            timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        }
    }
    
    try {
        Write-Host "🔄 Executing action: $Action" -ForegroundColor Yellow
        
        # Get parameters from payload
        $environment = if ($Payload.ContainsKey("environment")) { $Payload.environment } else { "development" }
        $teamsWebhook = if ($Payload.ContainsKey("teams_webhook")) { $Payload.teams_webhook } else { "" }
        
        # Build PowerShell command
        $scriptPath = "C:\users\south\fortigate-dashboard\automation\power_automate_integration.ps1"
        $arguments = @(
            "-Action", $Action,
            "-Environment", $environment
        )
        
        if ($teamsWebhook) {
            $arguments += @("-TeamsWebhookUrl", $teamsWebhook)
        }
        
        if ($Verbose) {
            $arguments += "-Verbose"
        }
        
        # Execute the automation script
        $result = & powershell.exe -ExecutionPolicy Bypass -File $scriptPath @arguments 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            # Parse JSON result
            $parsedResult = $result | ConvertFrom-Json
            Write-Host "✅ Action completed successfully" -ForegroundColor Green
            return $parsedResult
        } else {
            Write-Host "❌ Action failed" -ForegroundColor Red
            return @{
                success = $false
                message = "Script execution failed: $result"
                timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            }
        }
    }
    catch {
        Write-Host "❌ Exception during action execution: $($_.Exception.Message)" -ForegroundColor Red
        return @{
            success = $false
            message = "Exception: $($_.Exception.Message)"
            timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        }
    }
}

function Send-JsonResponse {
    param($Response, $Data, [int]$StatusCode = 200)
    
    $json = $Data | ConvertTo-Json -Depth 5
    $buffer = [System.Text.Encoding]::UTF8.GetBytes($json)
    
    $Response.StatusCode = $StatusCode
    $Response.ContentType = "application/json"
    $Response.ContentLength64 = $buffer.Length
    $Response.OutputStream.Write($buffer, 0, $buffer.Length)
    $Response.OutputStream.Close()
}

function Send-ErrorResponse {
    param($Response, $Message, [int]$StatusCode = 500)
    
    $errorData = @{
        success = $false
        message = $Message
        timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }
    
    Send-JsonResponse -Response $Response -Data $errorData -StatusCode $StatusCode
}

# Main execution
Write-Host "🎯 FortiGate Dashboard Webhook Listener" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

if ($SecretKey -eq "your-secret-key-here") {
    Write-Host "⚠️  WARNING: Using default secret key. Please change it for security!" -ForegroundColor Yellow
}

Start-WebhookListener -Port $Port
