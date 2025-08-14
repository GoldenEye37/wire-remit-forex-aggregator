
from sqlalchemy.sql import func

from .extensions import db


class Provider(db.Model):
	__tablename__ = 'providers'

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100), unique=True, nullable=False)
	provider_class = db.Column(db.String(100), nullable=False)
	is_active = db.Column(db.Boolean, default=True)
	created_at = db.Column(db.DateTime, server_default=func.now())
	updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
	rates = db.relationship('Rate', backref='provider', lazy=True)


class CurrencyPair(db.Model):
	__tablename__ = 'currency_pairs'

	id = db.Column(db.Integer, primary_key=True)
	base_currency = db.Column(db.String(3), nullable=False)
	target_currency = db.Column(db.String(3), nullable=False)
	is_active = db.Column(db.Boolean, default=True)
	markup_percentage = db.Column(db.Numeric(5, 4), default=0.1000)
	created_at = db.Column(db.DateTime, server_default=func.now())
	rates = db.relationship('Rate', backref='currency_pair', lazy=True)
	aggregated_rates = db.relationship('AggregatedRate', backref='currency_pair', lazy=True)

	__table_args__ = (db.UniqueConstraint('base_currency', 'target_currency', name='_base_target_uc'),)


class Rate(db.Model):
	__tablename__ = 'rates'

	id = db.Column(db.Integer, primary_key=True)
	currency_pair_id = db.Column(db.Integer, db.ForeignKey('currency_pairs.id'))
	provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'))
	buy_rate = db.Column(db.Numeric(18, 8), nullable=False)
	sell_rate = db.Column(db.Numeric(18, 8), nullable=False)
	fetched_at = db.Column(db.DateTime, nullable=False)
	created_at = db.Column(db.DateTime, server_default=func.now())

	__table_args__ = (
		db.Index('idx_rates_pair_time', 'currency_pair_id', 'fetched_at'),
		db.Index('idx_rates_provider_time', 'provider_id', 'fetched_at'),
	)


class AggregatedRate(db.Model):
	__tablename__ = 'aggregated_rates'

	id = db.Column(db.Integer, primary_key=True)
	currency_pair_id = db.Column(db.Integer, db.ForeignKey('currency_pairs.id'))
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
		db.Index('idx_aggregated_pair_time', 'currency_pair_id', 'aggregated_at'),
	)


class User(db.Model):
	__tablename__ = 'users'

	id = db.Column(db.Integer, primary_key=True)
	first_name = db.Column(db.String(100), nullable=False)
	last_name = db.Column(db.String(100), nullable=False)
	email = db.Column(db.String(255), unique=True, nullable=False)
	password_hash = db.Column(db.Text, nullable=False)
	role = db.Column(db.String(50), default='customer')
	is_active = db.Column(db.Boolean, default=True)
	created_at = db.Column(db.DateTime, server_default=func.now())
	last_login = db.Column(db.DateTime)
