from sqlalchemy import create_engine, text

# Change this line - use the direct database URL
DATABASE_URL = "sqlite:///./medical_llm_benchmark.db"

engine = create_engine(DATABASE_URL)

def upgrade():
    with engine.connect() as conn:
        # Create users table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR UNIQUE NOT NULL,
                name VARCHAR NOT NULL,
                hashed_password VARCHAR NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Add user_id to conversations table (if it exists)
        try:
            conn.execute(text("""
                ALTER TABLE conversations ADD COLUMN user_id INTEGER REFERENCES users(id)
            """))
            print("✅ Added user_id column to conversations table")
        except Exception as e:
            print(f"ℹ️  Column user_id might already exist: {e}")
        
        conn.commit()
        print("✅ Database migration completed!")

if __name__ == "__main__":
    upgrade()