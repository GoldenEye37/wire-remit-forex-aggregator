# Currency service for managing currency pairs and markup
from decimal import Decimal

from loguru import logger

from app.extensions import db
from app.models import CurrencyPair


class CurrencyService:
    @staticmethod
    def add_currency_pair(
        base_currency: str,
        target_currency: str,
        markup_percentage: float = 0.1000,
        is_active: bool = True,
    ) -> dict:
        try:
            base_currency = base_currency.upper().strip()
            target_currency = target_currency.upper().strip()

            if len(base_currency) != 3 or len(target_currency) != 3:
                return {
                    "success": False,
                    "message": "Currency codes must be exactly 3 characters",
                }

            if base_currency == target_currency:
                return {
                    "success": False,
                    "message": "Base and target currencies cannot be the same",
                }

            pair_combinations = [
                (base_currency, target_currency),
                (target_currency, base_currency),
            ]

            existing_pair = CurrencyPair.query.filter(
                db.or_(
                    *[
                        db.and_(
                            CurrencyPair.base_currency == base,
                            CurrencyPair.target_currency == target,
                        )
                        for base, target in pair_combinations
                    ]
                )
            ).first()

            if existing_pair:
                return {
                    "success": False,
                    "message": f"Currency pair {base_currency}-{target_currency} already exists",
                }

            if markup_percentage < 0 or markup_percentage > 1:
                return {
                    "success": False,
                    "message": "Markup percentage must be between 0 and 1",
                }

            new_pair = CurrencyPair(
                base_currency=base_currency,
                target_currency=target_currency,
                markup_percentage=Decimal(str(markup_percentage)),
                is_active=is_active,
            )

            db.session.add(new_pair)
            db.session.commit()

            logger.info(
                f"Currency pair added: {base_currency}-{target_currency} with markup {markup_percentage}"
            )
            return {
                "success": True,
                "message": "Currency pair added successfully",
                "pair": new_pair.to_dict(),
            }

        except Exception as e:
            logger.error(f"Error adding currency pair: {e}")
            db.session.rollback()
            return {"success": False, "message": "Failed to add currency pair"}

    @staticmethod
    def update_all_pairs_markup(markup_percentage: float) -> dict:
        try:
            if markup_percentage < 0 or markup_percentage > 1:
                return {
                    "success": False,
                    "message": "Markup percentage must be between 0 and 1",
                }

            pairs = CurrencyPair.query.all()

            if not pairs:
                return {"success": False, "message": "No currency pairs found"}

            updated_count = 0
            for pair in pairs:
                pair.markup_percentage = Decimal(str(markup_percentage))
                updated_count += 1

            db.session.commit()

            logger.info(
                f"Markup updated for all {updated_count} currency pairs to {markup_percentage}"
            )
            return {
                "success": True,
                "message": f"Markup updated for {updated_count} currency pairs",
                "updated_count": updated_count,
                "new_markup": markup_percentage,
            }

        except Exception as e:
            logger.error(f"Error updating all pairs markup: {e}")
            db.session.rollback()
            return {
                "success": False,
                "message": "Failed to update markup for all pairs",
            }
