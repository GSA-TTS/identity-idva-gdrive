from gdrive.sheets.builders import FormulaBuilder, PivotTableBuilder
from gdrive.sheets.types import (
    SortOrderEnum,
    FilterTypeEnum,
    FormulaEnum,
    UserEnteredValue,
    SummarizeFunctionEnum,
    StringLiteral,
)


class IDVAPivotDirector:
    def clicks(self, col_dict: dict) -> dict:
        builder = PivotTableBuilder(0, col_dict)
        builder.add_row("eventName", sortOrder=SortOrderEnum.ASCENDING)
        builder.add_row("eventCount", sortOrder=SortOrderEnum.ASCENDING)
        builder.add_value("eventCount", SummarizeFunctionEnum.SUM)
        return builder.render()

    def facebook(self, col_dict: dict) -> dict:
        builder = PivotTableBuilder(0, col_dict)
        builder.add_row("eventName", SortOrderEnum.ASCENDING, show_totals=False)
        builder.add_row("firstUserMedium", SortOrderEnum.ASCENDING)
        builder.add_row("firstUserSource", SortOrderEnum.ASCENDING)
        builder.add_row(
            "firstUserCampaignName", SortOrderEnum.ASCENDING, show_totals=False
        )

        builder.add_value("eventCount", SummarizeFunctionEnum.SUM)

        # =OR(regexmatch(firstUserSource,"facebook"),regexmatch(firstUserSource,"fb.com"), regexmatch(firstUserMedium,"fb"))
        facebook = FormulaBuilder(
            FormulaEnum.OR,
            [
                FormulaBuilder(
                    FormulaEnum.REGEX_MATCH,
                    ["firstUserSource", StringLiteral("facebook")],
                ),
                FormulaBuilder(
                    FormulaEnum.REGEX_MATCH,
                    ["firstUserSource", StringLiteral("fb.com")],
                ),
                FormulaBuilder(
                    FormulaEnum.REGEX_MATCH, ["firstUserMedium", StringLiteral("fb")]
                ),
            ],
        )

        # =OR(regexmatch(eventName,"session_start"),regexmatch(eventName,"first_visit"))
        sessions = FormulaBuilder(
            FormulaEnum.OR,
            [
                FormulaBuilder(
                    FormulaEnum.REGEX_MATCH,
                    ["eventName", StringLiteral("session_start")],
                ),
                FormulaBuilder(
                    FormulaEnum.REGEX_MATCH, ["eventName", StringLiteral("first_visit")]
                ),
            ],
        )

        builder.add_filter(
            "firstUserSource",
            FilterTypeEnum.CUSTOM,
            [UserEnteredValue(facebook.render())],
        )
        builder.add_filter(
            "eventName", FilterTypeEnum.CUSTOM, [UserEnteredValue(sessions.render())]
        )

        return builder.render()

    def craigslist(self, col_dict: dict) -> dict:
        builder = PivotTableBuilder(0, col_dict)
        builder.add_row("eventName", SortOrderEnum.ASCENDING, show_totals=False)
        builder.add_row("firstUserMedium", SortOrderEnum.ASCENDING)
        builder.add_row("firstUserSource", SortOrderEnum.ASCENDING)
        builder.add_value("eventCount", SummarizeFunctionEnum.SUM)

        # =OR(regexmatch(firstUserSource,"craigslist"), regexmatch(firstUserMedium,"cl"))
        craigslist = FormulaBuilder(
            FormulaEnum.OR,
            [
                FormulaBuilder(
                    FormulaEnum.REGEX_MATCH,
                    ["firstUserSource", StringLiteral("craigslist")],
                ),
                FormulaBuilder(
                    FormulaEnum.REGEX_MATCH, ["firstUserMedium", StringLiteral("cl")]
                ),
            ],
        )

        # =OR(regexmatch(eventName,"session_start"),regexmatch(eventName,"first_visit"))
        sessions = FormulaBuilder(
            FormulaEnum.OR,
            [
                FormulaBuilder(
                    FormulaEnum.REGEX_MATCH,
                    ["eventName", StringLiteral("session_start")],
                ),
                FormulaBuilder(
                    FormulaEnum.REGEX_MATCH, ["eventName", StringLiteral("first_visit")]
                ),
            ],
        )

        builder.add_filter(
            "firstUserSource",
            FilterTypeEnum.CUSTOM,
            values=[UserEnteredValue(craigslist.render())],
        )
        builder.add_filter(
            "eventName",
            FilterTypeEnum.CUSTOM,
            values=[UserEnteredValue(sessions.render())],
        )

        return builder.render()

    def reddit(self, col_dict: dict) -> dict:
        builder = PivotTableBuilder(0, col_dict)
        builder.add_row("eventName", SortOrderEnum.ASCENDING, show_totals=False)
        builder.add_row("firstUserMedium", SortOrderEnum.ASCENDING)
        builder.add_row("firstUserSource", SortOrderEnum.ASCENDING)
        builder.add_value("eventCount", SummarizeFunctionEnum.SUM)

        # =OR(regexmatch(firstUserSource,"reddit"),regexmatch(firstUserSource,"redd.it"), regexmatch(firstUserMedium,"rd"))
        reddit = FormulaBuilder(
            FormulaEnum.OR,
            [
                FormulaBuilder(
                    FormulaEnum.REGEX_MATCH,
                    ["firstUserSource", StringLiteral("reddit")],
                ),
                FormulaBuilder(
                    FormulaEnum.REGEX_MATCH,
                    ["firstUserSource", StringLiteral("redd.it")],
                ),
                FormulaBuilder(
                    FormulaEnum.REGEX_MATCH, ["firstUserMedium", StringLiteral("rd")]
                ),
            ],
        )

        # =OR(regexmatch(eventName,"session_start"),regexmatch(eventName,"first_visit"))
        sessions = FormulaBuilder(
            FormulaEnum.OR,
            [
                FormulaBuilder(
                    FormulaEnum.REGEX_MATCH,
                    ["eventName", StringLiteral("session_start")],
                ),
                FormulaBuilder(
                    FormulaEnum.REGEX_MATCH, ["eventName", StringLiteral("first_visit")]
                ),
            ],
        )

        builder.add_filter(
            "firstUserSource",
            FilterTypeEnum.CUSTOM,
            values=[UserEnteredValue(reddit.render())],
        )
        builder.add_filter(
            "eventName",
            FilterTypeEnum.CUSTOM,
            values=[UserEnteredValue(sessions.render())],
        )

        return builder.render()

    def twitter_x(self, col_dict: dict) -> dict:
        builder = PivotTableBuilder(0, col_dict)
        builder.add_row("eventName", SortOrderEnum.ASCENDING, show_totals=False)
        builder.add_row("firstUserMedium", SortOrderEnum.ASCENDING)
        builder.add_row("firstUserSource", SortOrderEnum.ASCENDING)
        builder.add_value("eventCount", SummarizeFunctionEnum.SUM)

        # =OR(regexmatch(firstUserSource,"twitter"),regexmatch(firstUserSource,"x.com"), regexmatch(firstUserMedium,"tx"))

        twitter = FormulaBuilder(
            FormulaEnum.OR,
            [
                FormulaBuilder(
                    FormulaEnum.REGEX_MATCH,
                    ["firstUserSource", StringLiteral("twitter")],
                ),
                FormulaBuilder(
                    FormulaEnum.REGEX_MATCH, ["firstUserSource", StringLiteral("x.com")]
                ),
                FormulaBuilder(
                    FormulaEnum.REGEX_MATCH, ["firstUserMedium", StringLiteral("tx")]
                ),
            ],
        )

        sessions = FormulaBuilder(
            FormulaEnum.OR,
            [
                FormulaBuilder(
                    FormulaEnum.REGEX_MATCH,
                    ["eventName", StringLiteral("session_start")],
                ),
                FormulaBuilder(
                    FormulaEnum.REGEX_MATCH, ["eventName", StringLiteral("first_visit")]
                ),
            ],
        )

        builder.add_filter(
            "firstUserSource",
            FilterTypeEnum.CUSTOM,
            values=[UserEnteredValue(twitter.render())],
        )
        builder.add_filter(
            "eventName",
            FilterTypeEnum.CUSTOM,
            values=[UserEnteredValue(sessions.render())],
        )

        return builder.render()

    def linkedin(self, col_dict: dict) -> dict:
        builder = PivotTableBuilder(0, col_dict)
        builder.add_row("eventName", SortOrderEnum.ASCENDING, show_totals=False)
        builder.add_row("firstUserMedium", SortOrderEnum.ASCENDING)
        builder.add_row("firstUserSource", SortOrderEnum.ASCENDING)
        builder.add_value("eventCount", SummarizeFunctionEnum.SUM)

        # =OR(regexmatch(firstUserSource,"linkedin.com"),regexmatch(firstUserSource,"lnkd.in"), regexmatch(firstUserMedium,"ln"))
        linkedin = FormulaBuilder(
            FormulaEnum.OR,
            [
                FormulaBuilder(
                    FormulaEnum.REGEX_MATCH,
                    ["firstUserSource", StringLiteral("linkedin.com")],
                ),
                FormulaBuilder(
                    FormulaEnum.REGEX_MATCH,
                    ["firstUserSource", StringLiteral("lnkd.in")],
                ),
                FormulaBuilder(
                    FormulaEnum.REGEX_MATCH, ["firstUserMedium", StringLiteral("ln")]
                ),
            ],
        )

        sessions = FormulaBuilder(
            FormulaEnum.OR,
            [
                FormulaBuilder(
                    FormulaEnum.REGEX_MATCH,
                    ["eventName", StringLiteral("session_start")],
                ),
                FormulaBuilder(
                    FormulaEnum.REGEX_MATCH, ["eventName", StringLiteral("first_visit")]
                ),
            ],
        )

        builder.add_filter(
            "firstUserSource",
            FilterTypeEnum.CUSTOM,
            values=[UserEnteredValue(linkedin.render())],
        )
        builder.add_filter(
            "eventName",
            FilterTypeEnum.CUSTOM,
            values=[UserEnteredValue(sessions.render())],
        )

        return builder.render()
