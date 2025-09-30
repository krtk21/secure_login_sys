conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="K@rthik2147",
    database="vault"
)
cursor = conn.cursor(dictionary=True)
