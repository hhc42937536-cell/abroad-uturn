param(
  [string]$OutputPath = "assets/rich-menu.png"
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Drawing

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$fullOutput = Join-Path $root $OutputPath
$outputDir = Split-Path $fullOutput -Parent
if (-not (Test-Path $outputDir)) {
  New-Item -ItemType Directory -Path $outputDir | Out-Null
}

$width = 2500
$height = 1686
$cols = 3
$rows = 3
$cellW = [int]($width / $cols)
$cellH = [int]($height / $rows)

$bitmap = New-Object System.Drawing.Bitmap $width, $height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit

$bgTop = [System.Drawing.Color]::FromArgb(22, 34, 62)
$bgMid = [System.Drawing.Color]::FromArgb(19, 63, 103)
$bgBottom = [System.Drawing.Color]::FromArgb(24, 25, 47)
$border = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(150, 180, 196, 216)), 2
$white = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
$muted = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(155, 189, 218, 239))
$titleFont = New-Object System.Drawing.Font "Microsoft JhengHei UI", 74, ([System.Drawing.FontStyle]::Bold), ([System.Drawing.GraphicsUnit]::Pixel)
$subtitleFont = New-Object System.Drawing.Font "Microsoft JhengHei UI", 48, ([System.Drawing.FontStyle]::Bold), ([System.Drawing.GraphicsUnit]::Pixel)
$emojiFont = New-Object System.Drawing.Font "Segoe UI Emoji", 112, ([System.Drawing.FontStyle]::Regular), ([System.Drawing.GraphicsUnit]::Pixel)

function U([int[]]$codes) {
  return -join ($codes | ForEach-Object { [char]$_ })
}

function U32([int[]]$codes) {
  return -join ($codes | ForEach-Object {
    if ($_ -gt 0xFFFF) { [char]::ConvertFromUtf32($_) } else { [char]$_ }
  })
}

function C([int]$r, [int]$g, [int]$b) {
  return New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb($r, $g, $b))
}

function Draw-IconRow($graphics, $icons, $font, $x, $y, $width, $height) {
  $count = $icons.Count
  if ($count -eq 1) {
    Draw-CenteredText $graphics $icons[0].Text $font $icons[0].Brush $x $y $width $height
    return
  }

  $totalWidth = [single]($count * 150 + (($count - 1) * 45))
  $startX = [single]($x + (($width - $totalWidth) / 2))
  for ($i = 0; $i -lt $count; $i++) {
    $iconX = $startX + ($i * 195)
    Draw-CenteredText $graphics $icons[$i].Text $font $icons[$i].Brush $iconX $y 150 $height
  }
}

function Draw-CenteredText($graphics, $text, $font, $brush, $x, $y, $width, $height) {
  $format = New-Object System.Drawing.StringFormat
  $format.Alignment = [System.Drawing.StringAlignment]::Center
  $format.LineAlignment = [System.Drawing.StringAlignment]::Center
  $format.Trimming = [System.Drawing.StringTrimming]::EllipsisCharacter
  $rect = New-Object System.Drawing.RectangleF ([single]$x), ([single]$y), ([single]$width), ([single]$height)
  $graphics.DrawString($text, $font, $brush, $rect, $format)
  $format.Dispose()
}

$items = @(
  @{ Icons = @(@{ Text = (U32 0x1F680); Brush = (C 255 78 117) }, @{ Text = (U32 0x1F525); Brush = (C 255 125 43) }); Title = (U 0x8AAA,0x8D70,0x5C31,0x8D70); Subtitle = "1$(U 0x5206,0x9418,0x4E00,0x9375,0x51FA,0x767C)" },
  @{ Icons = @(@{ Text = (U32 0x2728); Brush = (C 255 215 70) }, @{ Text = (U32 0x1F30F); Brush = (C 30 175 225) }); Title = (U 0x5B8C,0x6574,0x51FA,0x570B,0x898F,0x5283); Subtitle = "8$(U 0x6B65,0x8A73,0x7D30,0x8A08,0x756B,0x66F8)" },
  @{ Icons = @(@{ Text = (U32 0x1F30F); Brush = (C 28 176 226) }, @{ Text = (U32 0x2708,0xFE0F); Brush = (C 132 205 255) }); Title = (U 0x63A2,0x7D22,0x6700,0x4FBF,0x5B9C); Subtitle = (U 0x6700,0x4F4E,0x50F9,0x76EE,0x7684,0x5730) },
  @{ Icons = @(@{ Text = (U32 0x1F687); Brush = (C 255 82 126) }, @{ Text = (U32 0x1F4B3); Brush = (C 32 190 240) }); Title = (U 0x7576,0x5730,0x4EA4,0x901A,0x653B,0x7565); Subtitle = "$(U 0x5730,0x9435,0x5361)/$(U 0x8DEF,0x7DDA)/App" },
  @{ Icons = @(@{ Text = (U32 0x1F3E8); Brush = (C 255 190 85) }, @{ Text = (U32 0x1F50D); Brush = (C 128 112 210) }); Title = (U 0x4F4F,0x5BBF,0x63A8,0x85A6); Subtitle = "$(U 0x98EF,0x5E97)/$(U 0x5340,0x57DF)$(U 0x63A8,0x85A6)" },
  @{ Icons = @(@{ Text = (U32 0x1F6C2); Brush = (C 43 193 235) }, @{ Text = (U32 0x1F9F3); Brush = (C 56 206 230) }); Title = (U 0x884C,0x524D,0x5FC5,0x77E5); Subtitle = "$(U 0x7C3D,0x8B49)/$(U 0x6D77,0x95DC)/$(U 0x532F,0x7387)/$(U 0x6253,0x5305)" },
  @{ Icons = @(@{ Text = (U32 0x1F525); Brush = (C 255 126 43) }, @{ Text = (U32 0x1F30F); Brush = (C 27 177 224) }); Title = (U 0x73FE,0x5728,0x6700,0x592F); Subtitle = "$(U 0x71B1,0x9580,0x73A9,0x6CD5)/$(U 0x5FC5,0x8CB7)" },
  @{ Icons = @(@{ Text = (U32 0x2B50); Brush = (C 255 214 68) }, @{ Text = (U32 0x1F3B5); Brush = (C 88 54 76) }); Title = (U 0x8FFD,0x661F,0x884C,0x7A0B,0x898F,0x5283); Subtitle = "$(U 0x6F14,0x5531,0x6703)/$(U 0x898B,0x9762,0x6703)" },
  @{ Icons = @(@{ Text = (U32 0x2699,0xFE0F); Brush = (C 190 184 215) }); Title = (U 0x8A2D,0x5B9A); Subtitle = "$(U 0x51FA,0x767C,0x5730)/$(U 0x8AAA,0x660E)" }
)

for ($row = 0; $row -lt $rows; $row++) {
  for ($col = 0; $col -lt $cols; $col++) {
    $index = $row * $cols + $col
    $x = $col * $cellW
    $y = $row * $cellH
    $rect = New-Object System.Drawing.Rectangle $x, $y, $cellW, $cellH
    $cellColor = if ($row -eq 0) { $bgTop } elseif ($row -eq 1) { $bgMid } else { $bgBottom }
    $graphics.FillRectangle((New-Object System.Drawing.SolidBrush $cellColor), $rect)
    $graphics.DrawRectangle($border, $rect)

    Draw-IconRow $graphics $items[$index].Icons $emojiFont $x ($y + 74) $cellW 135
    Draw-CenteredText $graphics $items[$index].Title $titleFont $white $x ($y + 270) $cellW 96
    Draw-CenteredText $graphics $items[$index].Subtitle $subtitleFont $muted $x ($y + 400) $cellW 68
  }
}

$bitmap.Save($fullOutput, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()
Write-Output "Generated $fullOutput"
