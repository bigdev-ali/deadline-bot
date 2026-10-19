import aiosqlite

DB_PATH="deadlines.db" #name of the database SQLite creates it if it does not exist

async def init_db(): #initialise database
    async with aiosqlite.connect(DB_PATH) as db: #open a connect to that file
        await db.execute(""" CREATE TABLE IF NOT EXISTS deadlines ( id INTEGER PRIMARY KEY AUTOINCREMENT ,user_id INTEGER NOT NULL,
        title TEXT NOT NULL, due_at TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0
        )
        """)#db execute runs one SQL command """" just lets SQL span multiple lines then table is created as well as columns
        await db.commit() #this saves the change to the disk
async def add_deadline(user_id,title,due_at):# await creation of a deadline with user_id,title and due_at
    async with aiosqlite.connect(DB_PATH) as db: #open a connection with deadlines.db
        cursor=await db.execute( #send SQL command but the difference is it storeed in cursor
            "INSERT INTO deadlines (user_id, title, due_at) VALUES(?,?,?)", #INSERT into deadlines means add row in deadlines table ?,?,? is the values going in and what we are filling
            (user_id, title, due_at), # after ?<?<? these values are filled
        ) #id and done are left out because id is auto-gen and done is default 0
        await db.commit() #write on disk 
        return cursor.lastrowid #return the row

async def get_deadlines(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor=await db.execute(
            "SELECT id, title, due_at FROM deadlines "
            "WHERE user_id= ? AND done= 0 ORDER BY due_at",
            (user_id,),
            #SELECT says give me columns from these tables
            #WHERE is basically like a filter
            #ORDER by is sorter function like sooner first
            #fetchall pulls every match possible
        )
        return await cursor.fetchall()
