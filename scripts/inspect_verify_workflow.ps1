[CmdletBinding()]
param(
    [Parameter()]
    [string]$Repository = "GunsPojoshe/coa-raid-intelligence-workbench",

    [Parameter()]
    [string]$Workflow = "verify.yml",

    [Parameter(Mandatory = $true)]
    [ValidatePattern("^[0-9a-fA-F]{40}$")]
    [string]$HeadSha,

    [Parameter()]
    [ValidateSet("push", "pull_request", "workflow_dispatch")]
    [string]$Event = "push",

    [Parameter()]
    [string]$OutputPath
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-GhApiJson {
    param([Parameter(Mandatory = $true)][string]$Endpoint)

    $raw = gh api `
        --method GET `
        -H "Accept: application/vnd.github+json" `
        -H "X-GitHub-Api-Version: 2022-11-28" `
        $Endpoint

    if ($LASTEXITCODE -ne 0) {
        throw "GitHub API request failed: $Endpoint"
    }

    if ([string]::IsNullOrWhiteSpace($raw)) {
        throw "GitHub API returned an empty response: $Endpoint"
    }

    return $raw | ConvertFrom-Json
}

function Get-SafeProperty {
    param(
        [Parameter()][AllowNull()][object]$Object,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter()][AllowNull()][object]$Default = $null
    )

    if ($null -eq $Object) {
        return $Default
    }

    if ($Object.PSObject.Properties.Name -contains $Name) {
        return $Object.$Name
    }

    return $Default
}

$response = Invoke-GhApiJson (
    "repos/$Repository/actions/workflows/$Workflow/runs" +
    "?head_sha=$([uri]::EscapeDataString($HeadSha))" +
    "&event=$([uri]::EscapeDataString($Event))" +
    "&per_page=100"
)

$candidates = @()
if ($response.PSObject.Properties.Name -contains "workflow_runs") {
    $candidates = @($response.workflow_runs)
}

$exactRuns = @()
foreach ($candidate in $candidates) {
    $candidateHead = Get-SafeProperty $candidate "head_sha"
    $candidateEvent = Get-SafeProperty $candidate "event"

    if ($candidateHead -eq $HeadSha -and $candidateEvent -eq $Event) {
        $exactRuns += $candidate
    }
}

$selected = @(
    $exactRuns |
        Sort-Object `
            -Property {
                Get-SafeProperty $_ "run_number" 0
            } `
            -Descending
) | Select-Object -First 1

$jobs = @()
if ($null -ne $selected) {
    $runId = Get-SafeProperty $selected "id"
    if ($null -ne $runId) {
        $jobsResponse = Invoke-GhApiJson (
            "repos/$Repository/actions/runs/$runId/jobs?per_page=100"
        )
        if ($jobsResponse.PSObject.Properties.Name -contains "jobs") {
            foreach ($job in @($jobsResponse.jobs)) {
                $jobs += [ordered]@{
                    id = Get-SafeProperty $job "id"
                    name = Get-SafeProperty $job "name"
                    status = Get-SafeProperty $job "status"
                    conclusion = Get-SafeProperty $job "conclusion"
                }
            }
        }
    }
}

$receipt = [ordered]@{
    schema_version = 1
    diagnostic_kind = "verify_workflow_exact_head"
    generated_at = (Get-Date).ToUniversalTime().ToString(
        "yyyy-MM-ddTHH:mm:ssZ"
    )
    repository = $Repository
    workflow = $Workflow
    exact_head = $HeadSha
    requested_event = $Event
    run_found = ($null -ne $selected)
    run = if ($null -eq $selected) {
        $null
    }
    else {
        [ordered]@{
            id = Get-SafeProperty $selected "id"
            run_number = Get-SafeProperty $selected "run_number"
            event = Get-SafeProperty $selected "event"
            status = Get-SafeProperty $selected "status"
            conclusion = Get-SafeProperty $selected "conclusion"
            head_sha = Get-SafeProperty $selected "head_sha"
            head_branch = Get-SafeProperty $selected "head_branch"
            html_url = Get-SafeProperty $selected "html_url"
        }
    }
    jobs = $jobs
}

$json = $receipt | ConvertTo-Json -Depth 20

if (-not [string]::IsNullOrWhiteSpace($OutputPath)) {
    $absoluteOutput = [System.IO.Path]::GetFullPath(
        (Join-Path (Get-Location) $OutputPath)
    )
    $outputDirectory = [System.IO.Path]::GetDirectoryName($absoluteOutput)
    [System.IO.Directory]::CreateDirectory($outputDirectory) | Out-Null
    [System.IO.File]::WriteAllText(
        $absoluteOutput,
        $json,
        [System.Text.UTF8Encoding]::new($false)
    )
}

Write-Output $json