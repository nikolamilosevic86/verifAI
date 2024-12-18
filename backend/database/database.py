import asyncpg
import json
import datetime

class Database:
    """
    Singleton class to handle the database for user page Login and chat sessions.
    """

    def __init__(self, dbname: str, user: str, password: str, host: str):
        self.sql_database = None
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host

    async def open(self):
        if self.sql_database is None or self.sql_database.is_closed():
            self.sql_database = await asyncpg.connect(user=self.user, password=self.password,
                                                      database=self.dbname, host=self.host)

    async def close(self):
        if self.sql_database:
            await self.sql_database.close()

    async def create_database(self):
        # Connect to 'postgres' database to create a new database
        conn = await asyncpg.connect(user=self.user, password=self.password,
                                     database='postgres', host=self.host)
        try:
            await conn.execute(f'CREATE DATABASE {self.dbname}')
            print(f"Database '{self.dbname}' created successfully")
        except asyncpg.exceptions.DuplicateDatabaseError:
            print(f"Database '{self.dbname}' already exists")
        finally:
            await conn.close()

    async def create_tables(self):
        await self.open()
        try:
            await self.sql_database.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    name VARCHAR(255),
                    surname VARCHAR(255),
                    username VARCHAR(255) PRIMARY KEY,
                    password VARCHAR(255),
                    api_token VARCHAR(255),
                    email VARCHAR(255)
                );

                CREATE TABLE IF NOT EXISTS user_questions (
                    username VARCHAR(255),
                    question TEXT,
                    question_date TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS web_sessions (
                    id SERIAL PRIMARY KEY,
                    state JSONB NOT NULL
                );
            ''')
            print("Tables created successfully")
        except Exception as e:
            print(f"An error occurred while creating tables: {e}")
        finally:
            await self.close()

    @classmethod
    async def initialize(cls, dbname: str, user: str, password: str, host: str):
        db = cls(dbname, user, password, host)
        print("Making database")
        await db.create_database()
        print("Making tables")
        await db.create_tables()
        return db

    async def get_user(self, username: str) -> dict:
        await self.open()
        row = await self.sql_database.fetchrow('SELECT * FROM users WHERE username=$1', username)
        await self.close()
        return row
    
    async def get_user_by_api_token(self, api_token: str) -> dict:
        await self.open()
        row = await self.sql_database.fetchrow('SELECT * FROM users WHERE api_token=$1', api_token)
        await self.close()
        return row

    async def verify_user(self, username: str) -> bool:
        await self.open()
        row = await self.sql_database.fetchval('SELECT EXISTS(SELECT 1 FROM users WHERE username=$1)', username)
        await self.close()
        return row

    async def insert_user(self, name:str, surname:str, username: str, email: str, password_hash: str, api_token:str):
        await self.open()
        await self.sql_database.execute('INSERT INTO users (name, surname, username, email, password, api_token) VALUES ($1, $2, $3, $4, $5, $6)',
                                        name, surname, username, email, password_hash, api_token)
        await self.close()

    async def change_password(self, username: str, password_hash: str):
        await self.open()
        await self.sql_database.execute('UPDATE users SET password=$1 WHERE username=$2',password_hash, username)
        await self.close()

    async def save_session(self, state):
        await self.open()
        result = await self.sql_database.fetchrow(
            'INSERT INTO web_sessions (state) VALUES ($1) RETURNING id',
            json.dumps(state)
        )
        print("Result = ",result)
        await self.close()
        return result['id']
    
    async def insert_question(self, username: str, question: str, current_timestamp: datetime):
        await self.open()
        await self.sql_database.execute(
            'INSERT INTO user_questions (username, question, question_date) VALUES ($1, $2, $3)', username, question, current_timestamp
        )
        await self.close()

 


    async def get_web_session(self, session_id):
        await self.open()
        query = 'SELECT state FROM web_sessions WHERE id=$1'
        row = await self.sql_database.fetchrow(query, session_id)
        await self.close()
        if row:
            # Convert JSON data to Python dict if necessary
            state = json.loads(row['state']) if row['state'] else {}
            return {
                'state': state,
            }
        else:
            return None