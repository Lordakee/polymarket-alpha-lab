# Preparation-only, read-only OS capability queries. No user directory scan.
# Never launch Claude, install tools, enable features, elevate, or change policy.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

function Get-ProbeHostFacts {
    $facts = [ordered]@{
        schema = 'claude-probe-host-preparation-v1'
        os_64bit = [Environment]::Is64BitOperatingSystem
        edition = 'unknown'
        sandbox_feature = 'unknown'
        virtualization_firmware = 'unknown'
        hypervisor_present = 'unknown'
        reads_failed = @()
        vendor_executed = $false
        feature_changed = $false
        global_tools_changed = $false
        activation_authorized = $false
    }
    try {
        $edition = (Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' -Name EditionID).EditionID
        # Report only recognized edition categories, not arbitrary registry data.
        if ($edition -in @('Professional','Enterprise','Education','ProfessionalEducation','ProfessionalWorkstation','Core','CoreSingleLanguage')) {
            $facts.edition = $edition
        }
    } catch { $facts.reads_failed += 'edition' }
    try {
        $f = @(Get-CimInstance -ClassName Win32_OptionalFeature -Filter "Name='Containers-DisposableClientVM'" -Property InstallState)
        if ($f.Count -eq 1) {
            switch ([int]$f[0].InstallState) {
                1 { $facts.sandbox_feature = 'enabled' }
                2 { $facts.sandbox_feature = 'disabled' }
                3 { $facts.sandbox_feature = 'absent' }
                default { $facts.sandbox_feature = 'unknown' }
            }
        }
    } catch { $facts.reads_failed += 'sandbox_feature' }
    try {
        $cpu = @(Get-CimInstance -ClassName Win32_Processor -Property VirtualizationFirmwareEnabled)
        if ($cpu.Count -gt 0 -and @($cpu | Where-Object { $null -eq $_.VirtualizationFirmwareEnabled }).Count -eq 0) {
            $facts.virtualization_firmware = (@($cpu | Where-Object { $_.VirtualizationFirmwareEnabled -ne $true }).Count -eq 0)
        }
    } catch { $facts.reads_failed += 'virtualization_firmware' }
    try {
        $cs = Get-CimInstance -ClassName Win32_ComputerSystem -Property HypervisorPresent
        if ($null -ne $cs.HypervisorPresent) { $facts.hypervisor_present = [bool]$cs.HypervisorPresent }
    } catch { $facts.reads_failed += 'hypervisor_present' }
    # Feature presence is NOT a guarantee of launchability, zero secrets or egress isolation.
    $facts['next_action'] = 'operator_decision_required'
    if ($facts.os_64bit -and $facts.sandbox_feature -eq 'enabled') {
        $facts.next_action = 'review_prepared_sandbox_smoke'
    }
    return $facts
}

# Dot sourcing for synthetic tests defines functions only; normal invocation emits JSON.
if ($MyInvocation.InvocationName -ne '.') {
    Get-ProbeHostFacts | ConvertTo-Json -Depth 4
}
