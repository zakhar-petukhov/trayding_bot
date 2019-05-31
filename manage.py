from app import manager, db
from models import User


if __name__ == '__main__':
    manager.run()
    db.create_all()

