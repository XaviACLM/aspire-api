from datetime import datetime as Datetime
import re


class AbstractLocale:

    @staticmethod
    def parse_currency(string: str) -> float:
        raise NotImplementedError()

    @staticmethod
    def format_currency(amount: float) -> str:
        raise NotImplementedError()

    @staticmethod
    def parse_date(string: str) -> Datetime:
        raise NotImplementedError()

    @staticmethod
    def format_date(amount: Datetime) -> str:
        raise NotImplementedError()


class EuropeLocale(AbstractLocale):

    currency_parser = re.compile(r"^(-?)€([\d.]+),(\d\d)$")

    @staticmethod
    def parse_currency(string: str) -> float:
        if string == "":
            return 0
        s, i, w = re.match(EuropeLocale.currency_parser, string).groups()
        return float("{}{}.{}".format(s, i.replace(".",""), w))

    @staticmethod
    def format_currency(amount: float) -> str:
        if amount == 0:
            return ""
        elif amount > 0:
            return "€{}".format(str(amount).replace(".", ","))
        else:
            return "-€{}".format(str(-amount).replace(".", ","))

    @staticmethod
    def parse_date(string: str) -> Datetime:
        try:
            return Datetime.strptime(string, "%d/%m/%Y")
        except ValueError:
            return Datetime.strptime(string, "%d/%m/%y")

    @staticmethod
    def format_date(date: Datetime) -> str:
        return date.strftime("%d/%m/%y")


class USLocale(AbstractLocale):

    currency_parser = re.compile(r"^(-?)\$([\d.]+),(\d\d)$")

    @staticmethod
    def parse_currency(string: str) -> float:
        if string == "":
            return 0
        s, i, w = re.match(USLocale.currency_parser, string).groups()
        return float("{}{}.{}".format(s, i.replace(".",""), w))

    @staticmethod
    def format_currency(amount: float) -> str:
        if amount == 0:
            return ""
        elif amount > 0:
            return "${}".format(str(amount).replace(".", ","))
        else:
            return "-${}".format(str(-amount).replace(".", ","))

    @staticmethod
    def parse_date(string: str) -> Datetime:
        try:
            return Datetime.strptime(string, "%m/%d/%Y")
        except ValueError:
            return Datetime.strptime(string, "%m/%d/%y")

    @staticmethod
    def format_date(date: Datetime) -> str:
        return date.strftime("%d/%m/%y")


class ChinaLocale(AbstractLocale):

    currency_parser = re.compile(r"^(-?)¥([\d.]+),(\d\d)$")

    @staticmethod
    def parse_currency(string: str) -> float:
        if string == "":
            return 0
        s, i, w = re.match(USLocale.currency_parser, string).groups()
        return float("{}{}.{}".format(s, i.replace(".",""), w))

    @staticmethod
    def format_currency(amount: float) -> str:

        if amount == 0:
            return ""
        elif amount > 0:
            return "¥{}".format(str(amount).replace(".", ","))
        else:
            return "-¥{}".format(str(-amount).replace(".", ","))

    @staticmethod
    def parse_date(string: str) -> Datetime:
        try:
            return Datetime.strptime(string, "%Y/%m/%d")
        except ValueError:
            return Datetime.strptime(string, "%y/%m/%d")

    @staticmethod
    def format_date(date: Datetime) -> str:
        return date.strftime("%y/%d/%m")


Locale = EuropeLocale
