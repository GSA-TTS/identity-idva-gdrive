import sqlalchemy as sqla
from sqlalchemy.ext import declarative

# pylint: disable=too-few-public-methods

Base = declarative.declarative_base()


class ParticipantModel(Base):
    __tablename__ = "participant"

    id = sqla.Column(sqla.Integer, primary_key=True, index=True)
    first = sqla.Column(sqla.String)
    last = sqla.Column(sqla.String)
    email = sqla.Column(sqla.String)
    response_id = sqla.Column(sqla.String)
    time = sqla.Column(sqla.String)
    date = sqla.Column(sqla.String)
    ethnicity = sqla.Column(sqla.String)
    race = sqla.Column(sqla.String)
    gender = sqla.Column(sqla.String)
    age = sqla.Column(sqla.String)
    income = sqla.Column(sqla.String)
    skin_tone = sqla.Column(sqla.String)

    def as_list(self, index: str) -> list:
        return [
            index,
            self.id,
            self.first,
            self.last,
            self.email,
            self.response_id,
            self.datetime,
            self.ethnicity,
            self.gender,
            self.income,
            self.skin_tone,
        ]
