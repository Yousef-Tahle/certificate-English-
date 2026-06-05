import pyodbc


def get_connection():
    conn = pyodbc.connect(
        "DRIVER={SQL Server};"
        "SERVER=DESKTOP-MST84DP;"
        "DATABASE=EnglishCertDB;"
        "Trusted_Connection=yes;"
    )
    return conn
