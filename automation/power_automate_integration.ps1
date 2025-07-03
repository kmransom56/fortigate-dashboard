# Power Automate Desktop Integration for FortiGate Dashboard
# This script can be called from Power Automate Desktop flows

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("deploy", "backup", "test", "status", "restart")]
    [string]$Action,
    
    [string]$Environment = "development",
    [string]$NotificationEmail = "",
    [string]$TeamsWebhookUrl = "",
    [switch]$Verbose = $false
)

# Configuration
$config = @{
    ProjectPath = "C:\users\south\fortigate-dashboard"
    BackupScript = "C:\users\south\Scripts\backup_fortigate_dashboard.ps1"
    LogPath = "C:\users\south\fortigate-dashboard\automation\logs"
    ProductionPath = "G:\My Drive\home\keith\fortigate-dashboard"
}

function Write-PADLog {
    param([string]$Message, [string]$Level = "INFO")
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    if ($Verbose) {
        Write-Host $logMessage
    }
    
    # Ensure log directory exists
    if (-not (Test-Path $config.LogPath)) {
        New-Item -ItemType Directory -Path $config.LogPath -Force | Out-Null
    }
    
    # Log to file
    $logFile = Join-Path $config.LogPath "power_automate_$(Get-Date -Format 'yyyy-MM-dd').log"
    $logMessage | Out-File -FilePath $logFile -Append -Encoding UTF8
    
    # Return for Power Automate Desktop
    return @{
        Timestamp = $timestamp
        Level = $Level
        Message = $Message
        Action = $Action
    }
}

function Send-TeamsNotification {
    param(
        [string]$WebhookUrl,
        [string]$Title,
        [string]$Message,
        [string]$Color = "0078D4"
    )
    
    if (-not $WebhookUrl) { return }
    
    $body = @{
        "@type" = "MessageCard"
        "@context" = "http://schema.org/extensions"
        "themeColor" = $Color
        "summary" = $Title
        "sections" = @(
            @{
                "activityTitle" = $Title
                "activitySubtitle" = "FortiGate Dashboard Automation"
                "activityImage" = "https://www.fortinet.com/etc/designs/fortinet-2016/images/logo-fortinet.png"
                "facts" = @(
                    @{
                        "name" = "Action"
                        "value" = $Action
                    },
                    @{
                        "name" = "Environment"
                        "value" = $Environment
                    },
                    @{
                        "name" = "Timestamp"
                        "value" = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
                    },
                    @{
                        "name" = "Computer"
                        "value" = $env:COMPUTERNAME
                    }
                )
                "markdown" = $true
                "text" = $Message
            }
        )
    }
    
    try {
        $jsonBody = $body | ConvertTo-Json -Depth 4
        Invoke-RestMethod -Uri $WebhookUrl -Method Post -Body $jsonBody -ContentType "application/json"
        Write-PADLog "Teams notification sent successfully"
    }
    catch {
        Write-PADLog "Failed to send Teams notification: $($_.Exception.Message)" "ERROR"
    }
}

function Invoke-DeployAction {
    Write-PADLog "Starting deployment process"
    
    try {
        # 1. Create backup first
        Write-PADLog "Creating pre-deployment backup"
        & powershell.exe -ExecutionPolicy Bypass -File $config.BackupScript
        
        # 2. Run tests
        Write-PADLog "Running application tests"
        Push-Location $config.ProjectPath
        $testResult = & python -m pytest tests/ --tb=short 2>&1
        Pop-Location
        
        if ($LASTEXITCODE -ne 0) {
            throw "Tests failed: $testResult"
        }
        
        # 3. Deploy to production
        Write-PADLog "Deploying to production environment"
        $robocopyArgs = @(
            "`"$($config.ProjectPath)`"",
            "`"$($config.ProductionPath)`"",
            "/E", "/XO", "/R:3", "/W:10", "/NP",
            "/XD", "__pycache__", ".git", ".venv", "venv"
        )
        
        $result = & cmd /c "robocopy $($robocopyArgs -join ' ')" 2>&1
        
        if ($LASTEXITCODE -ge 8) {
            throw "Deployment failed with robocopy error: $LASTEXITCODE"
        }
        
        # 4. Restart services (if using Docker)
        if (Test-Path (Join-Path $config.ProductionPath "docker-compose.yml")) {
            Write-PADLog "Restarting Docker services"
            Push-Location $config.ProductionPath
            & docker-compose down
            & docker-compose up -d --build
            Pop-Location
        }
        
        Write-PADLog "Deployment completed successfully"
        
        Send-TeamsNotification -WebhookUrl $TeamsWebhookUrl -Title "Deployment Successful" -Message "FortiGate Dashboard deployed successfully to $Environment" -Color "00FF00"
        
        return @{ Success = $true; Message = "Deployment completed successfully" }
    }
    catch {
        $errorMsg = "Deployment failed: $($_.Exception.Message)"
        Write-PADLog $errorMsg "ERROR"
        Send-TeamsNotification -WebhookUrl $TeamsWebhookUrl -Title "Deployment Failed" -Message $errorMsg -Color "FF0000"
        return @{ Success = $false; Message = $errorMsg }
    }
}

function Invoke-BackupAction {
    Write-PADLog "Starting backup process"
    
    try {
        $result = & powershell.exe -ExecutionPolicy Bypass -File $config.BackupScript -Verbose:$Verbose
        
        Write-PADLog "Backup completed successfully"
        Send-TeamsNotification -WebhookUrl $TeamsWebhookUrl -Title "Backup Completed" -Message "FortiGate Dashboard backup created successfully"
        
        return @{ Success = $true; Message = "Backup completed successfully" }
    }
    catch {
        $errorMsg = "Backup failed: $($_.Exception.Message)"
        Write-PADLog $errorMsg "ERROR"
        return @{ Success = $false; Message = $errorMsg }
    }
}

function Invoke-TestAction {
    Write-PADLog "Running application tests"
    
    try {
        Push-Location $config.ProjectPath
        
        # Run Python tests
        $testResult = & python -m pytest tests/ --tb=short --json-report --json-report-file=test_results.json 2>&1
        $testExitCode = $LASTEXITCODE
        
        # Check if test results file exists
        $testResultsFile = Join-Path $config.ProjectPath "test_results.json"
        if (Test-Path $testResultsFile) {
            $testData = Get-Content $testResultsFile | ConvertFrom-Json
            $passedTests = $testData.summary.passed
            $failedTests = $testData.summary.failed
            $totalTests = $testData.summary.total
        } else {
            $passedTests = "Unknown"
            $failedTests = "Unknown"
            $totalTests = "Unknown"
        }
        
        Pop-Location
        
        $message = "Tests completed - Passed: $passedTests, Failed: $failedTests, Total: $totalTests"
        
        if ($testExitCode -eq 0) {
            Write-PADLog $message
            Send-TeamsNotification -WebhookUrl $TeamsWebhookUrl -Title "Tests Passed" -Message $message -Color "00FF00"
            return @{ Success = $true; Message = $message; TestResults = @{ Passed = $passedTests; Failed = $failedTests; Total = $totalTests } }
        } else {
            Write-PADLog "Tests failed: $testResult" "ERROR"
            Send-TeamsNotification -WebhookUrl $TeamsWebhookUrl -Title "Tests Failed" -Message $message -Color "FF0000"
            return @{ Success = $false; Message = $message; TestResults = @{ Passed = $passedTests; Failed = $failedTests; Total = $totalTests } }
        }
    }
    catch {
        $errorMsg = "Test execution failed: $($_.Exception.Message)"
        Write-PADLog $errorMsg "ERROR"
        return @{ Success = $false; Message = $errorMsg }
    }
}

function Invoke-StatusAction {
    Write-PADLog "Checking application status"
    
    try {
        $status = @{
            ProjectPath = $config.ProjectPath
            ProjectExists = Test-Path $config.ProjectPath
            GitRepository = Test-Path (Join-Path $config.ProjectPath ".git")
            VirtualEnv = Test-Path (Join-Path $config.ProjectPath ".venv")
            DockerCompose = Test-Path (Join-Path $config.ProjectPath "docker-compose.yml")
            LastBackup = "Unknown"
            DiskSpace = "Unknown"
        }
        
        # Get last backup info
        $backupRoot = "C:\users\south\backups\fortigate-dashboard"
        if (Test-Path $backupRoot) {
            $lastBackup = Get-ChildItem $backupRoot -Directory -Filter "backup_*" | Sort-Object CreationTime -Descending | Select-Object -First 1
            if ($lastBackup) {
                $status.LastBackup = $lastBackup.CreationTime.ToString("yyyy-MM-dd HH:mm:ss")
            }
        }
        
        # Get disk space
        $drive = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
        $freeSpaceGB = [math]::Round($drive.FreeSpace / 1GB, 2)
        $totalSpaceGB = [math]::Round($drive.Size / 1GB, 2)
        $status.DiskSpace = "$freeSpaceGB GB free of $totalSpaceGB GB total"
        
        Write-PADLog "Status check completed"
        
        $message = "Project Status - Exists: $($status.ProjectExists), Git: $($status.GitRepository), VEnv: $($status.VirtualEnv), Last Backup: $($status.LastBackup)"
        Send-TeamsNotification -WebhookUrl $TeamsWebhookUrl -Title "Status Check" -Message $message
        
        return @{ Success = $true; Message = "Status check completed"; Status = $status }
    }
    catch {
        $errorMsg = "Status check failed: $($_.Exception.Message)"
        Write-PADLog $errorMsg "ERROR"
        return @{ Success = $false; Message = $errorMsg }
    }
}

function Invoke-RestartAction {
    Write-PADLog "Restarting application services"
    
    try {
        Push-Location $config.ProjectPath
        
        # Stop any running uvicorn processes
        Get-Process | Where-Object { $_.ProcessName -like "*python*" -and $_.CommandLine -like "*uvicorn*" } | Stop-Process -Force
        
        # If using Docker
        if (Test-Path "docker-compose.yml") {
            & docker-compose down
            Start-Sleep -Seconds 5
            & docker-compose up -d
        }
        
        Pop-Location
        
        Write-PADLog "Application restart completed"
        Send-TeamsNotification -WebhookUrl $TeamsWebhookUrl -Title "Application Restarted" -Message "FortiGate Dashboard services restarted successfully"
        
        return @{ Success = $true; Message = "Application restart completed" }
    }
    catch {
        $errorMsg = "Restart failed: $($_.Exception.Message)"
        Write-PADLog $errorMsg "ERROR"
        return @{ Success = $false; Message = $errorMsg }
    }
}

# Main execution
try {
    Write-PADLog "Power Automate action started: $Action"
    
    $result = switch ($Action) {
        "deploy" { Invoke-DeployAction }
        "backup" { Invoke-BackupAction }
        "test" { Invoke-TestAction }
        "status" { Invoke-StatusAction }
        "restart" { Invoke-RestartAction }
        default { throw "Unknown action: $Action" }
    }
    
    # Output result for Power Automate Desktop
    $output = @{
        Action = $Action
        Success = $result.Success
        Message = $result.Message
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Environment = $Environment
    }
    
    if ($result.ContainsKey("TestResults")) {
        $output.TestResults = $result.TestResults
    }
    
    if ($result.ContainsKey("Status")) {
        $output.Status = $result.Status
    }
    
    $output | ConvertTo-Json -Depth 3
    
    Write-PADLog "Power Automate action completed: $Action"
}
catch {
    $errorMsg = "Power Automate action failed: $($_.Exception.Message)"
    Write-PADLog $errorMsg "ERROR"
    
    $errorOutput = @{
        Action = $Action
        Success = $false
        Message = $errorMsg
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Environment = $Environment
    }
    
    $errorOutput | ConvertTo-Json -Depth 3
    exit 1
}
