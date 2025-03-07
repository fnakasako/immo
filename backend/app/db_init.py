from app.core.database import Base, engine

def init_db():
    # Create all tables if they don't exist
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()