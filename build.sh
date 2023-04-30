# sam build && sam local invoke DownloadFilesFunction 
sam build && sam local invoke RunTradeFunction 
# sam sync --stack-name MoneyMachine --watch
# export SAM_CLI_TELEMETRY=0
# sam deploy