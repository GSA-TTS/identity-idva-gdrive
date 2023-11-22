import sqlalchemy as sqla
from sqlalchemy.ext import declarative

# pylint: disable=too-few-public-methods

Base = declarative.declarative_base()


class ResponseModel(Base):
    __tablename__ = "response"

    interaction_id = sqla.Column(sqla.String, primary_key=True)
    response_id = sqla.Column(sqla.String)
    survey_id = sqla.Column(sqla.String)
    session_id = sqla.Column(sqla.String)
    dist = sqla.Column(sqla.String)

    def as_list(self, index: str) -> list:
        return [
            index,
            self.interaction_id,
            self.response_id,
            self.survey_id,
            self.session_id,
            self.dist,
        ]


class ParticipantModel(Base):
    __tablename__ = "participant"

    id = sqla.Column(sqla.Integer, primary_key=True, index=True)
    survey_id = sqla.Column(sqla.String)
    response_id = sqla.Column(sqla.String)
    rules_consent_id = sqla.Column(sqla.String)
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
            self.survey_id,
            self.response_id,
            self.rules_consent_id,
            self.contact_id,
            self.time,
            self.date,
            self.ethnicity,
            self.gender,
            self.income,
            self.skin_tone,
        ]
