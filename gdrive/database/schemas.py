import pydantic


class TestBase(pydantic.BaseModel):
    test_content: str


class TestCreate(TestBase):
    """Create test model"""


class Test(TestBase):
    """Read letter model"""

    id: int

    class Config:
        """Config for the model"""

        orm_mode = True


class Count(pydantic.BaseModel):
    """count of tests content"""

    count: int


class ParticipantBase(pydantic.BaseModel):
    first: str
    last: str
    email: str
    response_id: str
    datetime: str
    ethnicity: str
    gender: str
    income: str
    skin_tone: str


class Participant(ParticipantBase):
    pass


class Participant(ParticipantBase):
    id: int

    class Config:
        orm_mode = True
