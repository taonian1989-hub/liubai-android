param([string]$ToolRoot,[string]$JsonJar)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
if(-not $ToolRoot){$ToolRoot=Join-Path $projectRoot 'work/toolchain'}
if(-not $JsonJar){$JsonJar=Join-Path $projectRoot 'work/test_dependencies/json.jar'}
$jdk=Get-ChildItem -LiteralPath (Join-Path $ToolRoot 'jdk') -Directory | Select-Object -First 1 -ExpandProperty FullName
$classes=Join-Path $projectRoot 'work/protocol_tests/classes'
New-Item -ItemType Directory -Path $classes -Force | Out-Null
$src=Join-Path $projectRoot 'app/src/main/java/io/liubai/assistant'
$files=@('ModelConfig.java','ModelHttpClient.java','SearchClient.java','LifePrompt.java') | ForEach-Object {Join-Path $src $_}
& (Join-Path $jdk 'bin/javac.exe') -encoding UTF-8 --add-modules jdk.httpserver -cp $JsonJar -d $classes @files (Join-Path $projectRoot 'tests/ModelHttpClientTest.java') (Join-Path $projectRoot 'tests/LifePromptTest.java')
if($LASTEXITCODE -ne 0){throw 'Protocol test compilation failed'}
foreach($name in @('ModelHttpClientTest','LifePromptTest')){
 & (Join-Path $jdk 'bin/java.exe') --add-modules jdk.httpserver -cp ($classes+';'+$JsonJar) ('io.liubai.assistant.'+$name)
 if($LASTEXITCODE -ne 0){throw ('Protocol tests failed: '+$name)}
}
