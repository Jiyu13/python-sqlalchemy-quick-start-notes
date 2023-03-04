from sqlalchemy import Column, create_engine, select
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.orm import relationship

# =============================== Declare Models ===================================
# 1. define module-level constructs that forms the structures we query from the db
#  declarative mapping, defines at once both a Python object model (class User),
#  as well as database metadata that describes real SQL tables that exist, or will exist,
#  in a particular database:
Base = declarative_base()


# 2. individual mapped classes (subclass of Base), a mapped class refers to a single particular db table
class User(Base):
    # =================table metadata==============================
    # 3. db table, table name : user_count
    __tablename__ = "user_account"

    # 4. declare Columns => all aspects of a db column
    # include datatype, server defaults, constraint info (membership with pk and fk)
    id = Column(Integer, primary_key=True)
    name = Column(String(30))
    fullname = Column(String)

    # 5. relationship() - link two classes => User.addresses link User and Address
    addresses = relationship(
        "Address", back_populates="user", cascade="all, delete-orphan"
    )

    # ======================================================

    # not require but useful for debugging
    def __repr__(self):
        return f"User(id={self.id!r}, name={self.name!r}, fullname={self.fullname!r})"


class Address(Base):

    __tablename__ = "address"
    id = Column(Integer, primary_key=True)
    email_address = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("user_account.id"), nullable=False)
    user = relationship("User", back_populates="addresses")

    def __repr__(self):
        return f"Address(id={self.id!r}, email_address={self.email_address!r})"


# ========================================= Create an Engine ================================================
# 6. Engine is a factory that can create new db connection,
# also holds onto connections insideof a Connection pool for fast reuse.
#  => can use a SQLite memeory only db for convenience:  engine = create_engine("sqlite:///:memory:")
#  => or create an engine that points for a local db file:  engine = create_engine("sqlite:///students.db")
# future=True, make sure using the lastest SQLAlchemy 2.0-style APIs
engine = create_engine("sqlite://", echo=True, future=True)


# ========================================= Emit CREATE TABLE DDL ================================================
# 7. generate our schema in target SQLite db, using Metadata.create_all()
Base.metadata.create_all(engine)

# ========================================= Create Objects and Persist ================================================
# to insert data in the db,

# 8. pass data to db using an object => Session, it makes use of Engine to interact with db
with Session(engine) as session:

    # 9. create instances to insert into db as data
    spongebob = User(
        name="spongebob",
        fullname="Spongebob Squarepants",
        addresses=[Address(email_address="spongebob@sqlalchemy.org")],
    )
    sandy = User(
        name="sandy",
        fullname="Sandy Cheeks",
        addresses=[
            Address(email_address="sandy@sqlalchemy.org"),
            Address(email_address="sandy@squirrelpower.org"),
        ],
    )
    patrick = User(name="patrick", fullname="Patrick Star")

    # 10. add multiple objects at once
    session.add_all([spongebob, sandy, patrick])

    # 11. to flush any pending changes to db and commit() the current transaction.
    session.commit()


# ================================ Simple SELECT to load objects =======================================
# 12.
session = Session(engine)

# 13. select() to create a new Select obj
# Select.where() to add WHERE criteria,
# in_(): Columnoperators
stmt = select(User).where(User.name.in_(["spongebob", "sandy"]))

# 14. Session.scalars() return a ScalarResult obj that iterate through ORM obj we've selected
for user in session.scalars(stmt):
    print(user)

User(id=1, name='spongebob', fullname='Spongebob Squarepants')
User(id=2, name='sandy', fullname='Sandy Cheeks')

# ================================ SELECT with JOIN =======================================
#  15. Select.join() => create joins among multiple tables at once
stmt = (
    select(Address)
    .join(Address.user)
    .where(User.name == "sandy")
    .where(Address.email_address == "sandy@sqlalchemy.org")
)
sandy_address = session.scalars(stmt).one()
print(sandy_address)

# ================================ Make Changes =======================================
# 16.retrieve a row we want to update
stmt = select(User).where(User.name == "patrick")
# 17. select only one data that matches the criteria
patrick = session.scalars(stmt).one()

# 18. add new email address to "patrick"
patrick.addresses.append(Address(email_address="patrickstar@sqlalchemy.org"))

# 19. change email_addresses associated with sandy
sandy_address.email_address = "sandy_cheeks@sqlalchemy.org"

session.commit()

# ================================ Some Deletes =======================================
# method 1:
# 20. get the obj by pk, then call remove()
sandy.addresses.get(User, 2)
sandy.addresses.remove(sandy_address)

# method 2:
# 21. use Session.flush()
session.flush()

# ================================ Delete An Instance =======================================
# 22. For a top-level delete of an object by itself, we use the Session.delete() method
# it doesn't perform the deletion, but it sets up the obj to be deleted on the next flush,
session.delete(patrick)

# 23. illustrate the rows being deleted, here’s the commit:
session.commit()
