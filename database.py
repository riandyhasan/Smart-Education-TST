import pymysql
import socket
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv('SQL_URL') 
engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# def connect_unix_socket() -> sqlalchemy.engine.base.Engine:
#     # Note: Saving credentials in environment variables is convenient, but not
#     # secure - consider a more secure solution such as
#     # Cloud Secret Manager (https://cloud.google.com/secret-manager) to help
#     # keep secrets safe.
#     db_user = os.getenv("DB_USER")  # e.g. 'my-database-user'
#     db_pass = os.getenv("DB_PASS")  # e.g. 'my-database-password'
#     db_name = os.getenv("DB_NAME")  # e.g. 'my-database'
#     unix_socket_path = os.getenv("INSTANCE_UNIX_SOCKET")  # e.g. '/cloudsql/project:region:instance'
#     s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

#     pool = sqlalchemy.create_engine(
#         # Equivalent URL:
#         # mysql+pymysql://<db_user>:<db_pass>@/<db_name>?unix_socket=<socket_path>/<cloud_sql_instance_name>
#         sqlalchemy.engine.url.URL.create(
#             drivername="mysql+pymysql",
#             username=db_user,
#             password=db_pass,
#             database=db_name,
#             query={"unix_socket": unix_socket_path},
#         ),
#         # ...
#     )
#     return pool
# engine = connect_unix_socket()
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()