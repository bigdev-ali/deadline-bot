import aiosqlite
import os

DB_PATH=os.getenv("DB_PATH","deadlines.db") #name of the database SQLite creates it if it does not exist and so that it can be used by any host server.

async def init_db(): #initialise database
    async with aiosqlite.connect(DB_PATH) as db: #open a connect to that file
        await db.execute(""" CREATE TABLE IF NOT EXISTS deadlines ( id INTEGER PRIMARY KEY AUTOINCREMENT ,user_id INTEGER NOT NULL,
        title TEXT NOT NULL, due_at TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0, reminded_24h INTEGER NOT NULL DEFAULT 0, 
        reminded_3h INTEGER NOT NULL DEFAULT 0, reminded_1h INTEGER NOT NULL DEFAULT 0
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
    
async def mark_done(deadline_id, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE deadlines SET done = 1 " #changes row's done with deadline to 1 meaning completed.
            "WHERE id = ? AND user_id = ? AND done = 0",
            (deadline_id, user_id),
        )
        await db.commit()
        return cursor.rowcount > 0 #if rowcount is greater than 0 it means a row was updated and returns true otherwise false


async def delete_deadline(deadline_id, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM deadlines WHERE id = ? AND user_id = ?",
            (deadline_id, user_id),
        )
        await db.commit()
        return cursor.rowcount > 0 #if rowcount is greater than 0 it means a row was deleted and returns true otherwise false

async def get_pending_deadlines():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, user_id, title, due_at, "
            "reminded_24h, reminded_3h, reminded_1h "
            "FROM deadlines WHERE done = 0 AND reminded_1h = 0"
        )
        return await cursor.fetchall() #gets all deadlines which are not done and not reminded 1h before the deadline. This is used to send reminders to users.


FLAG_UPDATES = {
    "24h": "reminded_24h = 1",
    "3h": "reminded_24h = 1, reminded_3h = 1",
    "1h": "reminded_24h = 1, reminded_3h = 1, reminded_1h = 1",
} #this is a python dictionary that maps the reminder stage to the corresponding SQL update statement.


async def mark_reminded(deadline_id, stage):
    set_clause = FLAG_UPDATES[stage]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE deadlines SET {set_clause} WHERE id = ?",
            (deadline_id,),
        )
        await db.commit() 
#this updates the reminder flags for a specific deadline based on the stage of the reminder (24h, 3h, or 1h). It constructs the appropriate SQL update statement using the FLAG_UPDATES dictionary and executes it against the database.