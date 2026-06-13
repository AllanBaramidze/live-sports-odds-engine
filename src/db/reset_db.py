from src.db.database import Base, engine

print("Dropping existing tables...")
Base.metadata.drop_all(bind=engine)

print("Recreating tables with new schema...")
Base.metadata.create_all(bind=engine)

print("Database reset successful!")