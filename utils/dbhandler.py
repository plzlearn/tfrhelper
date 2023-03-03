from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Initialize the database connection
engine = create_engine('sqlite:///builds.db')
Base = declarative_base()

class Build(Base):
    __tablename__ = 'builds'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    buildname = Column(String)
    role = Column(String)
    weapon1 = Column(String)
    weapon2 = Column(String)
    ability = Column(String)
    weight = Column(String)
    gearscore = Column(String)
    notes = Column(String)

    Base.metadata.create_all(engine)

    def to_dict(self):
        return {
            'id': self.id,
            'buildname': self.buildname,
            'role': self.role,
            'weapon1': self.weapon1,
            'weapon2': self.weapon2,
            'ability': self.ability,
            'weight': self.weight,
            'gearscore': self.gearscore,
            'notes': self.notes,
        }

Session = sessionmaker(bind=engine)

# Function to add a new build to the database
async def db_add_build(user_id, buildname, role, weapon1, weapon2, ability, weight, gearscore, notes):
    session = Session()
    build = Build(
        user_id=user_id,
        buildname=buildname,
        role=role,
        weapon1=weapon1,
        weapon2=weapon2,
        ability=ability,
        weight=weight,
        gearscore=gearscore,
        notes=notes
    )
    session.add(build)
    session.commit()
    return build.id

# Function to edit a field of a build in the database
async def db_edit_build(user_id, build_id, field, new_value):
    session = Session()
    build = session.query(Build).filter_by(user_id=user_id, id=build_id).first()
    setattr(build, field, new_value)
    session.commit()

# Function to remove a build from the database
async def db_remove_build(user_id, build_id):
    session = Session()
    build = session.query(Build).filter_by(user_id=user_id, id=build_id).first()
    session.delete(build)
    session.commit()

# Function to get a list of builds for a user from the database
async def db_get_user_builds(user_id):
    session = Session()
    builds = session.query(Build).filter_by(user_id=user_id).all()
    return [build.to_dict() for build in builds] 