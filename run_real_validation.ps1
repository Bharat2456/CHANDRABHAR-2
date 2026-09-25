$ErrorActionPreference = "Stop"
$root = if ($args.Count -gt 0) { $args[0] } else { "C:\Users\<you>\ChandrayaanData\mission_data" }
python -m app.cli.main mission --root $root --out outputs\mission_validation
