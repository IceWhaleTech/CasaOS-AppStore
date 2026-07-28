<#
.SYNOPSIS
    Immich Folder Album Creator – fully configurable via command line.
    Creates albums from subfolders of external libraries.
    Uses API for albums/libraries; database (read‑only) for asset mapping.

.PARAMETER ImmichServer
    Immich server URL (e.g., http://192.168.1.7:2283) – REQUIRED

.PARAMETER ApiKey
    Immich API key – REQUIRED

.PARAMETER DbContainer
    PostgreSQL container name (e.g., immich-postgres) – REQUIRED

.PARAMETER DbUser
    PostgreSQL user – REQUIRED

.PARAMETER DbName
    PostgreSQL database name – REQUIRED

.PARAMETER DbPassword
    PostgreSQL password – REQUIRED

.PARAMETER OwnerId
    (Optional) Only process libraries owned by this user ID; if blank, process all.

.PARAMETER DryRun
    If specified, no changes are made – only shows what would happen.

.PARAMETER LogFile
    Optional path to log file.

.EXAMPLE
    ./immich-album-creator.ps1 -ImmichServer 'http://192.168.1.7:2283' -ApiKey 'abc123' -DbContainer 'immich-postgres' -DbUser 'casaos' -DbName 'immich' -DbPassword 'secret'
#>

param(
    [string]$ImmichServer,
    [string]$ApiKey,
    [string]$DbContainer,
    [string]$DbUser,
    [string]$DbName,
    [string]$DbPassword,
    [string]$OwnerId,
    [switch]$DryRun,
    [string]$LogFile
)

# ---- Validation ----
$missing = @()
if (-not $ImmichServer) { $missing += "ImmichServer" }
if (-not $ApiKey)       { $missing += "ApiKey" }
if (-not $DbContainer)  { $missing += "DbContainer" }
if (-not $DbUser)       { $missing += "DbUser" }
if (-not $DbName)       { $missing += "DbName" }
if (-not $DbPassword)   { $missing += "DbPassword" }

if ($missing.Count -gt 0) {
    Write-Host "ERROR: Missing required parameters: $($missing -join ', ')" -ForegroundColor Red
    Write-Host "Please provide all required parameters." -ForegroundColor Yellow
    exit 1
}

# ---- Logging ----
function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logLine = "[$timestamp] $Message"
    if ($LogFile) {
        Add-Content -Path $LogFile -Value $logLine -Encoding UTF8 -ErrorAction SilentlyContinue
    }
    Write-Host $logLine -ForegroundColor $Color
}

# ---- Helper: API call ----
function Invoke-ImmichApi {
    param($Method="GET", $Endpoint, $Body=$null, [switch]$NoThrow)
    $uri = "$($ImmichServer.TrimEnd('/'))/api$Endpoint"
    $headers = @{"x-api-key"=$ApiKey; "Accept"="application/json"}
    if ($Body) { $headers["Content-Type"]="application/json"; $bodyJson = $Body | ConvertTo-Json -Compress }
    try {
        $r = Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers -Body $bodyJson -ErrorAction Stop
        return $r
    } catch {
        if ($NoThrow) { return $null }
        Write-Log "ERROR: API call failed: $_" "Red"
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $reader.BaseStream.Position = 0
            $reader.DiscardBufferedData()
            $errorBody = $reader.ReadToEnd()
            Write-Log "Response: $errorBody" "Red"
        }
        throw
    }
}

# ---- Get all albums ----
function Get-AllAlbums {
    $albums = @(); $page=1; $size=100
    do {
        $r = Invoke-ImmichApi -Endpoint "/albums?page=$page&size=$size"
        if ($r) { $albums += $r; $page++ } else { break }
    } while ($r.Count -eq $size)
    return $albums
}

# ---- Create album ----
function Create-Album($name) {
    Write-Log "Creating album '$name'..." "Yellow"
    $body = @{ albumName = $name }
    $r = Invoke-ImmichApi -Method POST -Endpoint "/albums" -Body $body
    return $r.id
}

# ---- Add assets to album ----
function Add-AssetsToAlbum($albumId, $assetIds) {
    if ($assetIds.Count -eq 0) { return }
    $batchSize = 1000
    for ($i=0; $i -lt $assetIds.Count; $i+=$batchSize) {
        $chunk = $assetIds[$i..($i+$batchSize-1)]
        $body = @{ ids = $chunk }
        try { 
            Invoke-ImmichApi -Method PUT -Endpoint "/albums/$albumId/assets" -Body $body | Out-Null
        } catch {
            Write-Log "Failed to add assets: $_" "Red"
        }
    }
}

# ---- Get assets from database (read‑only) ----
function Get-AssetsFromDatabase {
    Write-Log "Querying database for assets..." "Cyan"
    $query = 'SELECT id, "originalPath" FROM asset;'

    # Determine docker command (try docker, fallback to sudo docker)
    $dockerCmd = "docker"
    $test = & $dockerCmd ps 2>$null
    if ($LASTEXITCODE -ne 0) {
        $dockerCmd = "sudo docker"
        Write-Log "Using sudo docker" "Yellow"
        $test = & $dockerCmd ps 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Log "ERROR: Cannot execute docker. Please add user to docker group or configure passwordless sudo." "Red"
            exit 1
        }
    }

    # Build command as an array (no cmd /c)
    $dockerArgs = @(
        'exec', $DbContainer,
        'psql', '-U', $DbUser, '-d', $DbName,
        '-t', '-A', '-F|',
        '-c', $query
    )

    Write-Log "Running: $dockerCmd $($dockerArgs -join ' ')" "Gray"
    $output = & $dockerCmd $dockerArgs 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR: Database query failed. Check password and container name." "Red"
        Write-Log "Error output: $output" "Red"
        exit 1
    }

    $assetPathMap = @{}
    $lines = $output -split "`n" | Where-Object { $_ -match '\|' }
    foreach ($line in $lines) {
        $parts = $line -split '\|'
        if ($parts.Count -ge 2) {
            $id = $parts[0].Trim()
            $path = $parts[1].Trim()
            if ($path) { $assetPathMap[$path] = $id }
        }
    }
    Write-Log "Total assets mapped from database: $($assetPathMap.Count)" "Cyan"
    return $assetPathMap
}

# ---- MAIN ----
Write-Log "=== Immich Folder Album Creator (API + DB read‑only) ===" "Cyan"

# 1. Test connection
Write-Log "Testing connection to Immich..." "Cyan"
try {
    $test = Invoke-ImmichApi -Endpoint "/albums?page=1&size=1" -ErrorAction Stop
    Write-Log "API key accepted." "Green"
} catch {
    Write-Log "Cannot connect or invalid API key." "Red"; exit 1
}

# 2. Fetch existing albums
Write-Log "Fetching existing albums..." "Cyan"
$existingAlbums = Get-AllAlbums
$albumMap = @{}
foreach ($a in $existingAlbums) { $albumMap[$a.albumName] = $a.id }
Write-Log "Found $($albumMap.Count) existing albums." "Green"

# 3. Get external libraries
Write-Log "Fetching external libraries..." "Cyan"
$allLibraries = Invoke-ImmichApi -Endpoint "/libraries" -NoThrow
if (-not $allLibraries -or $allLibraries.Count -eq 0) {
    Write-Log "No external libraries found." "Red"; exit 1
}

if ($OwnerId) {
    $libraries = $allLibraries | Where-Object { $_.ownerId -eq $OwnerId }
    Write-Log "Filtered to $($libraries.Count) libraries owned by $OwnerId (out of $($allLibraries.Count) total)." "Green"
} else {
    $libraries = $allLibraries
    Write-Log "Processing all $($libraries.Count) libraries." "Green"
}

if ($libraries.Count -eq 0) {
    Write-Log "No libraries to process." "Red"; exit 1
}

$importPaths = @()
foreach ($lib in $libraries) {
    if ($lib.importPaths) {
        foreach ($p in $lib.importPaths) {
            $clean = $p.TrimEnd('/')
            if ($clean -and $clean -notin $importPaths) { $importPaths += $clean }
        }
    }
}

if ($importPaths.Count -eq 0) {
    Write-Log "No import paths defined in these libraries." "Red"; exit 1
}

Write-Log "Import paths to scan:" "Cyan"
foreach ($p in $importPaths) { Write-Log "  $p" "Gray" }

# 4. Get assets from database
$assetPathMap = Get-AssetsFromDatabase
if ($assetPathMap.Count -eq 0) {
    Write-Log "No assets found in database. Did you scan the library?" "Yellow"
    Write-Log "Trigger a scan from the Immich web UI (Administration -> External Libraries -> Refresh)." "Yellow"
    exit 1
}

# 5. Scan subfolders and create albums
$mediaExtensions = @('.jpg','.jpeg','.png','.gif','.bmp','.tiff','.webp',
                     '.mp4','.mov','.avi','.mkv','.m4v','.3gp','.wmv','.flv','.webm')
$totalProcessed = 0

foreach ($importPath in $importPaths) {
    if (-not (Test-Path $importPath -PathType Container)) {
        Write-Log "Warning: Import path '$importPath' does not exist. Skipping." "Yellow"
        continue
    }
    Write-Log "Scanning: $importPath" "Cyan"
    $subDirs = Get-ChildItem -Path $importPath -Directory
    foreach ($dir in $subDirs) {
        $albumName = $dir.Name
        $folderPath = $dir.FullName

        # Check for media files
        $files = Get-ChildItem -Path $folderPath -File | Where-Object { $mediaExtensions -contains $_.Extension.ToLower() }
        if ($files.Count -eq 0) {
            Write-Log "  Folder '$albumName' has no media files. Skipping." "Gray"
            continue
        }

        # Match assets
        $assetIds = @()
        foreach ($file in $files) {
            $fullPath = $file.FullName
            if ($assetPathMap.ContainsKey($fullPath)) {
                $assetIds += $assetPathMap[$fullPath]
            } else {
                Write-Log "  Warning: Asset not in DB: $fullPath" "Magenta"
            }
        }

        if ($assetIds.Count -eq 0) {
            Write-Log "  No assets found in Immich for '$albumName'. Skipping." "Gray"
            continue
        }

        # Process album
        Write-Log "Processing folder: $albumName ($folderPath)" "Cyan"
        $albumId = $null
        if ($albumMap.ContainsKey($albumName)) {
            $albumId = $albumMap[$albumName]
            Write-Log "  Album already exists (ID: $albumId)" "Green"
        } else {
            if ($DryRun) {
                Write-Log "  [DRY] Would create album '$albumName'" "Yellow"
                $totalProcessed++
                continue
            } else {
                $albumId = Create-Album $albumName
                $albumMap[$albumName] = $albumId
                Write-Log "  Album created (ID: $albumId)" "Green"
            }
        }

        if (-not $DryRun) {
            # Add assets (skip duplicates)
            $albumDetails = Invoke-ImmichApi -Endpoint "/albums/$albumId"
            $existing = $albumDetails.assets | ForEach-Object { $_.id }
            $newIds = $assetIds | Where-Object { $_ -notin $existing }
            if ($newIds.Count -eq 0) {
                Write-Log "  All assets already in album." "Gray"
            } else {
                Write-Log "  Adding $($newIds.Count) new assets..." "Yellow"
                Add-AssetsToAlbum -albumId $albumId -assetIds $newIds
                Write-Log "  Done." "Green"
            }
        } else {
            Write-Log "  [DRY] Would add $($assetIds.Count) assets." "Yellow"
        }
        $totalProcessed++
    }
}

Write-Log "`nCompleted! Processed $totalProcessed folders." "Green"
if ($DryRun) { Write-Log "Dry run – no changes made." "Yellow" }