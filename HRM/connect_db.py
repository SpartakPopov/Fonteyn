# import mysql.connector
# from mysql.connector import Error
# import os
# from dotenv import load_dotenv

# load_dotenv()

# def get_connection():
#     try:
#         connection = mysql.connector.connect(
#             host=os.getenv("MYSQL_HOST"),
#             user=os.getenv("MYSQL_USER"),
#             password=os.getenv("MYSQL_PASSWORD"),
#             database=os.getenv("MYSQL_DATABASE"),
#             port=int(os.getenv("MYSQL_PORT", 3306))
#         )
#         if connection.is_connected():
#             return connection  
#     except Error as e:
#         print(f"Error connecting to MySQL database: {e}")
#         return None
