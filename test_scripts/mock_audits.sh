
# Instantiate audits
echo "Instantiating Audits"
echo "================================================================================"

curl -X 'POST' \
  'http://127.0.0.1:8080/register_audit/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"data":{"admin_jid":"audit_admin_a@foxhole","bond":100,"name":"Demo Project A"},"id":"3da800ea-5aad-4800-a279-2a6ceb49f535","meta":{"oracleRequest":{"callbackAddr":"0xDFe2ee9C0ba4c9cC646A2b9d491E4127da206fB3","callbackFunctionId":"0xe532f6d1","cancelExpiration":"1653696875","data":"0x646e616d656950726f6a65637420416961646d696e5f6a69647561756469745f61646d696e5f6240666f78686f6c6564626f6e641864","dataVersion":"1","payment":"100000000000000000","requestId":"0x8b3b536f3e60d8973215aae27d27f6aada169154a600b23f591bd88c0b9ebeea","requester":"0xDFe2ee9C0ba4c9cC646A2b9d491E4127da206fB3","specId":"0x3364613830306561356161643438303061323739326136636562343966353335"}}}'
