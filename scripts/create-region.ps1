$title = Get-Clipboard
$editor_length = 80
$region_decorator = "="
$padding = 1
$begin_region = "#region "
$end_region = "#endregion "

$repetition = [Math]::Truncate(($editor_length - ($title.Length + 2 * $padding)) / 2)

# https://www.reddit.com/r/PowerShell/comments/7a39p9/comment/dp6r93m
$region_text = New-Object System.Text.StringBuilder

#top_line
[void]$region_text.Append($begin_region)
[void]$region_text.Append($region_decorator * ($repetition - $begin_region.Length))
[void]$region_text.Append(" $title ")
[void]$region_text.Append($region_decorator * $repetition)

#bottom_line
[void]$region_text.Append("`n")
[void]$region_text.Append($end_region)
[void]$region_text.Append($region_decorator * ($editor_length - $end_region.Length))

$region_text.ToString() | Set-Clipboard 