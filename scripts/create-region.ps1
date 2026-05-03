[CmdletBinding()]
param (
    [Parameter(Mandatory=$true)]
    [string] $title,
    [switch] $echo

)

$title_length       =   $title.Length
if ($title_length % 2 -eq 1) {
    $title          +=  " "
    $title_length   +=  1
}

$editor_length      =   80
$half               =   $editor_length / 2
$padding            =   1
$region_decorator   =   "="
$begin_region       =   "#region "
$end_region         =   "#endregion "
$begin_n            =   $begin_region.Length


$gen    = $title_length / 2
$left_pad = $half - ($padding + $gen + $begin_n)
$right_pad = $half - ($padding + $gen)

# https://www.reddit.com/r/PowerShell/comments/7a39p9/comment/dp6r93m
$region_text = New-Object System.Text.StringBuilder

# top_line
[void]$region_text.Append($begin_region)
[void]$region_text.Append($region_decorator * ($left_pad))
[void]$region_text.Append(" " * $padding  + $title + " " * $padding)
[void]$region_text.Append($region_decorator * $right_pad)

# bottom_line
[void]$region_text.Append("`n")
[void]$region_text.Append($end_region)
[void]$region_text.Append($region_decorator * ($editor_length - $end_region.Length))

$str = $region_text.ToString() 
if ($echo) {
    Write-Host $str
} else {
    $str | Set-Clipboard 
}
