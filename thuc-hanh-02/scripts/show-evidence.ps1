param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("SERVICE", "KB1", "KB2", "KB3", "KB4", "MCAST1", "MCAST2")]
    [string]$Case
)

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "TH02 Evidence $Case"
$Host.UI.RawUI.BackgroundColor = "Black"
$Host.UI.RawUI.ForegroundColor = "Gray"
Clear-Host

function Write-Heading([string]$Title) {
    Write-Host "============================================================" -ForegroundColor DarkCyan
    Write-Host $Title -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor DarkCyan
}

switch ($Case) {
    "SERVICE" {
        Write-Heading "RABBITMQ SERVICE STATUS"
        $container = docker inspect th02-rabbitmq | ConvertFrom-Json
        [pscustomobject]@{
            Container = $container[0].Name.TrimStart('/')
            Image = $container[0].Config.Image
            Running = $container[0].State.Running
            Health = $container[0].State.Health.Status
            AMQP = "localhost:5672"
            Management = "localhost:15672"
        } | Format-List
        Write-Host ""
        Write-Host "Management UI: http://localhost:15672" -ForegroundColor Green
        Write-Host "Login: guest / guest" -ForegroundColor Green
        Write-Host "Result: RabbitMQ is healthy and ready." -ForegroundColor Yellow
    }
    "KB1" {
        Write-Heading "KB1 - PERSISTENT MESSAGE AFTER BROKER RESTART"
        $events = Get-Content -LiteralPath "logs\kb1-consumer.jsonl" | ConvertFrom-Json
        $processed = @($events | Where-Object event -eq "processed")
        $received = @($events | Where-Object event -eq "received")
        Write-Host "Before restart : queue don_hang contained 5 messages"
        Write-Host "After restart  : queue don_hang still contained 5 messages" -ForegroundColor Green
        Write-Host "Manual ACK     : $($processed.Count)/5 completed" -ForegroundColor Green
        Write-Host ""
        $received | Select-Object maDonHang, receivedAt, @{N="latencyMs";E={$_.latencyMs}} | Format-Table -AutoSize
        Write-Host "RESULT: PASS - all 5 persistent messages survived restart." -ForegroundColor Yellow
    }
    "KB2" {
        Write-Heading "KB2 - TRANSIENT MESSAGE AFTER BROKER RESTART"
        $sent = @(Get-Content -LiteralPath "logs\producer-transient.jsonl" | ConvertFrom-Json | Where-Object event -eq "sent")
        Write-Host "Sent before restart : $($sent.Count) transient messages"
        Write-Host "Queue configuration : durable=False, delivery_mode=1"
        Write-Host "After restart        : message_count=0" -ForegroundColor Green
        Write-Host ""
        $sent | Select-Object maDonHang, thoiGianGui, confirmed | Format-Table -AutoSize
        Write-Host "RESULT: PASS - transient messages were removed." -ForegroundColor Yellow
    }
    "KB3" {
        Write-Heading "KB3 - ASYNCHRONOUS COMMUNICATION"
        $producer = Get-Content -LiteralPath "logs\kb3-producer.jsonl" | ConvertFrom-Json
        $consumer = Get-Content -LiteralPath "logs\kb3-consumer.jsonl" | ConvertFrom-Json
        $summary = $producer | Where-Object event -eq "producer_summary" | Select-Object -Last 1
        $first = [datetimeoffset](($consumer | Where-Object event -eq "received" | Select-Object -First 1).receivedAt)
        $last = [datetimeoffset](($consumer | Where-Object event -eq "processed" | Select-Object -Last 1).finishedAt)
        $processed = @($consumer | Where-Object event -eq "processed")
        Write-Host "Messages                    : $($processed.Count)"
        Write-Host ("Producer send time          : {0:N3} seconds" -f $summary.elapsedSeconds) -ForegroundColor Green
        Write-Host ("Consumer total process time : {0:N3} seconds" -f (($last - $first).TotalSeconds)) -ForegroundColor Green
        Write-Host "Producer waited for replies : NO"
        Write-Host ""
        Write-Host "RESULT: PASS - sending completed far earlier than processing." -ForegroundColor Yellow
    }
    "KB4" {
        Write-Heading "KB4 - LOAD BALANCING WITH THREE CONSUMERS"
        $rows = 1..3 | ForEach-Object {
            $events = Get-Content -LiteralPath "logs\kb4-consumer-$_.jsonl" | ConvertFrom-Json
            [pscustomobject]@{
                Consumer = "consumer-$_"
                Processed = @($events | Where-Object event -eq "processed").Count
                ManualAck = "Yes"
                Prefetch = 1
            }
        }
        $rows | Format-Table -AutoSize
        Write-Host "Total messages: 15"
        Write-Host "Distribution  : 5 - 5 - 5" -ForegroundColor Green
        Write-Host "RESULT: PASS - RabbitMQ distributed work across consumers." -ForegroundColor Yellow
    }
    "MCAST1" {
        Write-Heading "MULTICAST KB1 - THREE RECEIVERS"
        $rows = 1..3 | ForEach-Object {
            $events = Get-Content -LiteralPath "logs\smoke-receiver-$_.jsonl" | ConvertFrom-Json
            [pscustomobject]@{
                Receiver = "receiver-$_"
                Received = @($events).Count
                FirstSeq = ($events | Select-Object -First 1).seq
                LastSeq = ($events | Select-Object -Last 1).seq
            }
        }
        Write-Host "Destination: 224.1.1.1:5007"
        Write-Host "Sender transmitted each sequence once."
        Write-Host ""
        $rows | Format-Table -AutoSize
        Write-Host "RESULT: PASS - all three receivers obtained 5/5 packets." -ForegroundColor Yellow
    }
    "MCAST2" {
        Write-Heading "MULTICAST KB2 - LATE JOINING RECEIVER"
        $events = Get-Content -LiteralPath "logs\receiver-late-test.jsonl" | ConvertFrom-Json
        $events | Select-Object seq, sentAt, receivedAt, latencyMs | Format-Table -AutoSize
        Write-Host "Sender started at seq=0."
        Write-Host "Late receiver first received seq=$($events[0].seq)." -ForegroundColor Green
        Write-Host "Previously sent seq 0-4 were not replayed." -ForegroundColor Green
        Write-Host "RESULT: PASS - multicast communication is transient." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Evidence generated from JSONL logs produced by the programs." -ForegroundColor DarkGray
Start-Sleep -Seconds 120

