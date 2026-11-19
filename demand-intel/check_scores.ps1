$ErrorActionPreference = 'Stop'
Start-Sleep -Seconds 2
$raw = (Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8000/api/scores?product=sambal').Content
$j = $raw | ConvertFrom-Json
foreach ($s in $j.scores) {
    $b = $s.breakdown
    Write-Output ("{0,-18} composite={1,-6} search={2,-6} buying={3,-6} sat={4,-6} comp={5}" -f $s.state, $s.score, $b.search.score, $b.buying.score, $b.saturation.score, $b.competition.score)
}
