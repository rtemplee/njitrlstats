import sqlite3

def create_connection(db_file):
    """ Create connection to db

    Args:
        db_file: path to db file
        
    Returns:
        con: db connection
    """
    con = None
    
    try:
        con = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)
    
    return con

def execute_query(q, con):
    """ Execute query
    
    Args:
        q: query to be executed
        con: db connection
        
    Returns:
        1 if success,
        0 if failure
    """
    cur = con.cursor()
    
    try:
        cur.execute(q)
    except Exception as e:
        print(e)
        con.close()
        
        return 0

    con.commit()
    con.close()
    
    return 1



# execute_query('CREATE TABLE "12-20-23 vs MSU Game 1"(Score, Goals, Assists, Saves, Shots)', create_connection('ballchasing.db'))