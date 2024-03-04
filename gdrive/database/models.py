import sqlalchemy as sqla
from sqlalchemy.ext import declarative

# pylint: disable=too-few-public-methods

Base = declarative.declarative_base()


class SkEventModel(Base):
    __tablename__ = "sk_events"

    id = sqla.Column(sqla.String, primary_key=True, index=True)
    interaction_id = sqla.Column(sqla.String)
    timestamp = sqla.Column(sqla.String)
    json_content = sqla.Column(sqla.JSON)

    def as_list(self, index: str) -> list:
        return [index, self.id, self.interaction_id, self.timestamp, self.json_content]


class EventOutcomeModel(Base):
    __tablename__ = "event_outcome"

    id = sqla.Column(sqla.String, primary_key=True, index=True)
    company_id = sqla.Column(sqla.String)
    connection_id = sqla.Column(sqla.String)
    connector_id = sqla.Column(sqla.String)
    flow_id = sqla.Column(sqla.String)
    flow_version_id = sqla.Column(sqla.String)
    event_id = sqla.Column(sqla.String)
    interaction_id = sqla.Column(sqla.String)
    name = sqla.Column(sqla.String)
    node_description = sqla.Column(sqla.String)
    node_title = sqla.Column(sqla.String)
    outcome_description = sqla.Column(sqla.String)
    outcome_status = sqla.Column(sqla.String)
    outcome_type = sqla.Column(sqla.String)
    should_continue_on_error = sqla.Column(sqla.String)
    template_precompile = sqla.Column(sqla.String)
    signal_id = sqla.Column(sqla.String)
    transition_id = sqla.Column(sqla.String)
    timestamp = sqla.Column(sqla.String)

    def as_list(self, index: str) -> list:
        return [
            index,
            self.id,
            self.company_id,
            self.connection_id,
            self.connector_id,
            self.flow_id,
            self.flow_version_id,
            self.event_id,
            self.interaction_id,
            self.name,
            self.node_description,
            self.node_title,
            self.outcome_description,
            self.outcome_status,
            self.outcome_type,
            self.should_continue_on_error,
            self.template_precompile,
            self.signal_id,
            self.transition_id,
            self.timestamp,
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
