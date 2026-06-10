from typing import Any


class Cond:
    """Helper for constructing Hive Engine query conditions (Mongo-style operators)."""

    @staticmethod
    def gt(value: Any) -> dict[str, Any]:
        """Greater than ($gt)."""
        return {"$gt": value}

    @staticmethod
    def gte(value: Any) -> dict[str, Any]:
        """Greater than or equal ($gte)."""
        return {"$gte": value}

    @staticmethod
    def lt(value: Any) -> dict[str, Any]:
        """Less than ($lt)."""
        return {"$lt": value}

    @staticmethod
    def lte(value: Any) -> dict[str, Any]:
        """Less than or equal ($lte)."""
        return {"$lte": value}

    @staticmethod
    def ne(value: Any) -> dict[str, Any]:
        """Not equal ($ne)."""
        return {"$ne": value}

    @staticmethod
    def in_list(values: list[Any]) -> dict[str, Any]:
        """In list ($in)."""
        return {"$in": values}

    @staticmethod
    def nin(values: list[Any]) -> dict[str, Any]:
        """Not in list ($nin)."""
        return {"$nin": values}


class Query:
    """Helper for constructing dictionary queries."""

    @staticmethod
    def match(**kwargs: Any | dict[str, Any]) -> dict[str, Any]:
        """
        Construct a query dictionary from keyword arguments.

        Example:
            Query.match(account="hive-engine", _id=Cond.gt(10))
            # Returns: {'account': 'hive-engine', '_id': {'$gt': 10}}
        """
        return kwargs
