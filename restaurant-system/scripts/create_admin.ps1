Param(
    [string]$Username = 'bootstrap_admin',
    [string]$Password = 'AdminS3cret!'
)

# Activate virtualenv if present
if (Test-Path -Path '.\.venv\Scripts\Activate.ps1') {
    . .\.venv\Scripts\Activate.ps1
}

# Run the python helper
python .\scripts\create_admin.py $Username $Password

Write-Host "create_admin finished"