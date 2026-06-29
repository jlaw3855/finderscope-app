# * Stops Finderscope dev servers bound to the default backend/frontend ports.
param(
    [int]$BackendPort = $(if ($env:BACKEND_PORT) { [int]$env:BACKEND_PORT } else { 8000 }),
    [int]$FrontendPort = $(if ($env:FRONTEND_PORT) { [int]$env:FRONTEND_PORT } else { 5173 })
)

function Stop-PortListener {
    param(
        [int]$Port,
        [string]$Label
    )

    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $connections) {
        Write-Output "No listener on port $Port ($Label)"
        return
    }

    $processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($processId in $processIds) {
        Write-Output "Stopping port $Port ($Label): PID $processId"
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
}

function Stop-OrphanUvicornWorkers {
    $workers = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $_.CommandLine -and
            $_.CommandLine -like '*multiprocessing.spawn*spawn_main*'
        }

    foreach ($worker in $workers) {
        if ($worker.CommandLine -match 'parent_pid=(\d+)') {
            $parentId = [int]$Matches[1]
            $parent = Get-Process -Id $parentId -ErrorAction SilentlyContinue
            if (-not $parent) {
                Write-Output "Stopping orphan uvicorn worker (dead parent $parentId): PID $($worker.ProcessId)"
                Stop-Process -Id $worker.ProcessId -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

Stop-PortListener -Port $BackendPort -Label 'backend'
Stop-PortListener -Port $FrontendPort -Label 'frontend'
Stop-OrphanUvicornWorkers
