from sqlalchemy.sql import func

from .extensions import db


class Provider(db.Model):
    __tablename__ = "providers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    provider_class = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    rates = db.relationship("Rate", backref="provider", lazy=True)


class CurrencyPair(db.Model):
    __tablename__ = "currency_pairs"

    id = db.Column(db.Integer, primary_key=True)
    base_currency = db.Column(db.String(3), nullable=False)
    target_currency = db.Column(db.String(3), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    markup_percentage = db.Column(db.Numeric(5, 4), default=0.1000)
    created_at = db.Column(db.DateTime, server_default=func.now())
    rates = db.relationship("Rate", backref="currency_pair", lazy=True)
    aggregated_rates = db.relationship(
        "AggregatedRate", backref="currency_pair", lazy=True
    )

    __table_args__ = (
        db.UniqueConstraint("base_currency", "target_currency", name="_base_target_uc"),
    )

    def to_dict(self):
        """Serialize CurrencyPair to dictionary."""
        return {
            "id": self.id,
            "base_currency": self.base_currency,
            "target_currency": self.target_currency,
            "is_active": self.is_active,
            "markup_percentage": float(self.markup_percentage)
            if self.markup_percentage
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def validate_currency(cls, currency: str):
        """
        Validate if a currency exists in the database as either base or target currency.
        Returns error message if invalid, None if valid.
        """
        if not currency:
            return "Currency is required"

        if len(currency) != 3:
            return "Invalid currency format. Use 'XXX'"

        # check if currency is not upper case
        currency_upper = currency.upper()
        if currency != currency_upper:
            return f"Currency '{currency}' must be uppercase"

        # Check if currency exists in the database as either base or target currency
        currency_exists = db.session.query(
            db.session.query(cls)
            .filter(
                (cls.base_currency == currency_upper)
                | (cls.target_currency == currency_upper)
            )
            .exists()
        ).scalar()

        if not currency_exists:
            return f"Currency '{currency_upper}' not found in available currency pairs"

        return None


class Rate(db.Model):
    __tablename__ = "rates"

    id = db.Column(db.Integer, primary_key=True)
    currency_pair_id = db.Column(db.Integer, db.ForeignKey("currency_pairs.id"))
    provider_id = db.Column(db.Integer, db.ForeignKey("providers.id"))
    buy_rate = db.Column(db.Numeric(18, 8), nullable=False)
    sell_rate = db.Column(db.Numeric(18, 8), nullable=False)
    fetched_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

    __table_args__ = (
        db.Index("idx_rates_pair_time", "currency_pair_id", "fetched_at"),
        db.Index("idx_rates_provider_time", "provider_id", "fetched_at"),
    )

    def to_dict(self):
        """Serialize Rate to dictionary."""
        return {
            "id": self.id,
            "currency_pair_id": self.currency_pair_id,
            "provider_id": self.provider_id,
            "buy_rate": float(self.buy_rate) if self.buy_rate else None,
            "sell_rate": float(self.sell_rate) if self.sell_rate else None,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AggregatedRate(db.Model):
    __tablename__ = "aggregated_rates"

    id = db.Column(db.Integer, primary_key=True)
    currency_pair_id = db.Column(db.Integer, db.ForeignKey("currency_pairs.id"))
    average_buy_rate = db.Column(db.Numeric(18, 8), nullable=False)
    average_sell_rate = db.Column(db.Numeric(18, 8), nullable=False)
    final_buy_rate = db.Column(db.Numeric(18, 8), nullable=False)
    final_sell_rate = db.Column(db.Numeric(18, 8), nullable=False)
    markup_percentage = db.Column(db.Numeric(5, 4), nullable=False)
    provider_count = db.Column(db.Integer, nullable=False)
    aggregated_at = db.Column(db.DateTime, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

    __table_args__ = (
        db.Index("idx_aggregated_pair_time", "currency_pair_id", "aggregated_at"),
    )

    @classmethod
    def get_all_latest(cls):
        """
        Get the latest aggregated rate for each currency pair.
        Returns a list of AggregatedRate objects.
        """
        subquery = (
            db.session.query(
                cls.currency_pair_id,
                func.max(cls.aggregated_at).label("max_aggregated_at"),
            )
            .group_by(cls.currency_pair_id)
            .subquery()
        )

        return (
            db.session.query(cls)
            .join(
                subquery,
                (cls.currency_pair_id == subquery.c.currency_pair_id)
                & (cls.aggregated_at == subquery.c.max_aggregated_at),
            )
            .order_by(cls.aggregated_at.desc())
            .all()
        )

    @classmethod
    def get_latest_for_pair(cls, base_currency: str, target_currency: str):
        """
        Get the latest aggregated rate for a specific currency pair.
        Returns an AggregatedRate object or None if not found.
        """
        return (
            db.session.query(cls)
            .join(CurrencyPair, cls.currency_pair_id == CurrencyPair.id)
            .filter(
                CurrencyPair.base_currency == base_currency.upper(),
                CurrencyPair.target_currency == target_currency.upper(),
            )
            .order_by(cls.aggregated_at.desc())
            .first()
        )

    @classmethod
    def get_latest_for_base(cls, base_currency: str):
        """
        Get the latest aggregated rates for all pairs with a specific base currency.
        Returns a list of AggregatedRate objects.
        """
        subquery = (
            db.session.query(
                cls.currency_pair_id,
                func.max(cls.aggregated_at).label("max_aggregated_at"),
            )
            .join(CurrencyPair, cls.currency_pair_id == CurrencyPair.id)
            .filter(CurrencyPair.base_currency == base_currency.upper())
            .group_by(cls.currency_pair_id)
            .subquery()
        )

        return (
            db.session.query(cls)
            .join(
                subquery,
                (cls.currency_pair_id == subquery.c.currency_pair_id)
                & (cls.aggregated_at == subquery.c.max_aggregated_at),
            )
            .order_by(cls.aggregated_at.desc())
            .all()
        )

    @classmethod
    def get_latest_for_currency(cls, any_currency: str):
        """
        Derive the latest aggregated rate for a specific currency.
        It can either be a base or target currency.
        If not base currency, find it in target currencies, invert rates and return results.
        Returns a list of dictionaries with normalized rates where the specified currency is the base.
        """
        any_currency = any_currency.upper()
        results = []

        # Get rates where the currency is the base currency
        base_rates = cls.get_latest_for_base(any_currency)
        for rate in base_rates:
            rate_dict = rate.to_dict_with_pair()
            results.append(rate_dict)

        # Get rates where the currency is the target currency (need to invert)
        subquery = (
            db.session.query(
                cls.currency_pair_id,
                func.max(cls.aggregated_at).label("max_aggregated_at"),
            )
            .join(CurrencyPair, cls.currency_pair_id == CurrencyPair.id)
            .filter(CurrencyPair.target_currency == any_currency)
            .group_by(cls.currency_pair_id)
            .subquery()
        )

        target_rates = (
            db.session.query(cls, CurrencyPair)
            .join(CurrencyPair, cls.currency_pair_id == CurrencyPair.id)
            .join(
                subquery,
                (cls.currency_pair_id == subquery.c.currency_pair_id)
                & (cls.aggregated_at == subquery.c.max_aggregated_at),
            )
            .order_by(cls.aggregated_at.desc())
            .all()
        )

        # Invert rates for target currency pairs
        for rate, pair in target_rates:
            inverted_dict = {
                "id": rate.id,
                "currency_pair_id": rate.currency_pair_id,
                "base_currency": pair.target_currency,  # Swap: target becomes base
                "target_currency": pair.base_currency,  # Swap: base becomes target
                "average_buy_rate": float(1 / rate.average_sell_rate)
                if rate.average_sell_rate
                else None,  # Invert sell to buy
                "average_sell_rate": float(1 / rate.average_buy_rate)
                if rate.average_buy_rate
                else None,  # Invert buy to sell
                "final_buy_rate": float(1 / rate.final_sell_rate)
                if rate.final_sell_rate
                else None,
                "final_sell_rate": float(1 / rate.final_buy_rate)
                if rate.final_buy_rate
                else None,
                "markup_percentage": float(rate.markup_percentage)
                if rate.markup_percentage
                else None,
                "provider_count": rate.provider_count,
                "aggregated_at": rate.aggregated_at.isoformat()
                if rate.aggregated_at
                else None,
                "expires_at": rate.expires_at.isoformat() if rate.expires_at else None,
                "created_at": rate.created_at.isoformat() if rate.created_at else None,
                "inverted": True,  # Flag to indicate this rate was inverted
            }
            results.append(inverted_dict)

        return results

    def to_dict(self):
        """Serialize AggregatedRate to dictionary."""
        return {
            "id": self.id,
            "currency_pair_id": self.currency_pair_id,
            "average_buy_rate": float(self.average_buy_rate)
            if self.average_buy_rate
            else None,
            "average_sell_rate": float(self.average_sell_rate)
            if self.average_sell_rate
            else None,
            "final_buy_rate": float(self.final_buy_rate)
            if self.final_buy_rate
            else None,
            "final_sell_rate": float(self.final_sell_rate)
            if self.final_sell_rate
            else None,
            "markup_percentage": float(self.markup_percentage)
            if self.markup_percentage
            else None,
            "provider_count": self.provider_count,
            "aggregated_at": self.aggregated_at.isoformat()
            if self.aggregated_at
            else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def get_latest_for_all(cls):
        """
        Get rates for all currencies in the database, grouped by currency.
        Each currency will show rates where it's either base or target (with inversion).
        Returns a dictionary with currency codes as keys and their rates as values.
        """
        currencies_query = (
            db.session.query(CurrencyPair.base_currency.label("currency"))
            .union(db.session.query(CurrencyPair.target_currency.label("currency")))
            .distinct()
        )

        all_currencies = [row.currency for row in currencies_query]

        result = {}

        for currency in all_currencies:
            currency_rates = cls.get_latest_for_currency(currency)
            if currency_rates:
                result[currency] = {
                    "currency": currency,
                    "rates": currency_rates,
                    "count": len(currency_rates),
                }

        return result

    def to_dict_with_pair(self):
        """Serialize AggregatedRate with currency pair info."""
        data = self.to_dict()
        if hasattr(self, "currency_pair") and self.currency_pair:
            data.update(
                {
                    "base_currency": self.currency_pair.base_currency,
                    "target_currency": self.currency_pair.target_currency,
                }
            )
        return data


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(50), default="customer")
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime)

    creator = db.relationship("User", remote_side=[id], backref="created_users")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
