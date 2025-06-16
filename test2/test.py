import mysql.connector

try:
    conn = mysql.connector.connect(
        host="dev-flexibleserver.mysql.database.azure.com",
        user="FonteynDb@dev-flexibleserver",
        password="Admin@123",
        database="hrm",
        ssl_ca="/app/BaltimoreCyberTrustRoot.crt.pem"
    )
    print("Connected!")
    conn.close()
except Exception as e:
    print("Error:", e)
