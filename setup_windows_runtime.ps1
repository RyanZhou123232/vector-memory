$ErrorActionPreference = 'Stop'
$runtimeRoot = Join-Path $PSScriptRoot '.runtime'
New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null
$runtimePackage = Join-Path $runtimeRoot 'vc_redist.x64.exe'
Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile $runtimePackage
$runtimeSignature = Get-AuthenticodeSignature -LiteralPath $runtimePackage
if ($runtimeSignature.Status -ne 'Valid' -or $runtimeSignature.SignerCertificate.Subject -notmatch 'O=Microsoft Corporation') {
    throw 'The runtime package does not have a valid Microsoft signature.'
}
# Read/extract the signed package. Do not execute an installer or change Windows.
& (Join-Path $PSScriptRoot '.venv\Scripts\python.exe') (Join-Path $PSScriptRoot 'extract_runtime.py')
if ($LASTEXITCODE -ne 0) { throw 'Runtime extraction failed.' }
$runtimeFiles = Get-ChildItem -LiteralPath (Join-Path $runtimeRoot 'dlls') -Filter '*.dll' -File
foreach ($runtimeFile in $runtimeFiles) {
    $runtimeDllSignature = Get-AuthenticodeSignature -LiteralPath $runtimeFile.FullName
    if ($runtimeDllSignature.Status -ne 'Valid' -or $runtimeDllSignature.SignerCertificate.Subject -notmatch 'O=Microsoft Corporation') {
        throw "Runtime DLL signature validation failed: $($runtimeFile.Name)"
    }
}
Write-Output 'Local signed Windows runtime prepared. System libraries were not changed.'
