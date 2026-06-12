"""
Cost Guard — Bảo Vệ Budget LLM

Mục tiêu: Tránh bill bất ngờ từ LLM API.
- Đếm tokens đã dùng mỗi ngày
- Cảnh báo khi gần hết budget
- Block khi vượt budget

Trong production: lưu trong Redis/DB, không phải in-memory.
"""
import time
import logging
import os
import redis
from dataclasses import dataclass, field
from fastapi import HTTPException

logger = logging.getLogger(__name__)


# Giá token (tham khảo, thay đổi theo model)
PRICE_PER_1K_INPUT_TOKENS = 0.00015   # GPT-4o-mini: $0.15/1M input
PRICE_PER_1K_OUTPUT_TOKENS = 0.0006   # GPT-4o-mini: $0.60/1M output


@dataclass
class UsageRecord:
    user_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    request_count: int = 0
    day: str = field(default_factory=lambda: time.strftime("%Y-%m-%d"))

    @property
    def total_cost_usd(self) -> float:
        input_cost = (self.input_tokens / 1000) * PRICE_PER_1K_INPUT_TOKENS
        output_cost = (self.output_tokens / 1000) * PRICE_PER_1K_OUTPUT_TOKENS
        return round(input_cost + output_cost, 6)


class CostGuard:
    def __init__(
        self,
        daily_budget_usd: float = 1.0,       # $1/ngày per user
        global_daily_budget_usd: float = 10.0, # $10/ngày tổng cộng
        warn_at_pct: float = 0.8,              # Cảnh báo khi dùng 80%
    ):
        self.daily_budget_usd = daily_budget_usd
        self.global_daily_budget_usd = global_daily_budget_usd
        self.warn_at_pct = warn_at_pct
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.r = redis.from_url(redis_url, decode_responses=True)

    @property
    def _global_cost(self) -> float:
        today = time.strftime("%Y-%m-%d")
        key = f"cost_guard:global_cost:{today}"
        val = self.r.get(key)
        return float(val) if val else 0.0

    def _get_user_cost(self, user_id: str, today: str) -> float:
        key = f"cost_guard:user_cost:{user_id}:{today}"
        val = self.r.get(key)
        return float(val) if val else 0.0

    def check_budget(self, user_id: str) -> None:
        """
        Kiểm tra budget trước khi gọi LLM.
        Raise 402 nếu vượt budget.
        """
        today = time.strftime("%Y-%m-%d")

        # Global budget check
        current_global_cost = self._global_cost
        if current_global_cost >= self.global_daily_budget_usd:
            logger.critical(f"GLOBAL BUDGET EXCEEDED: ${current_global_cost:.4f}")
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable due to budget limits. Try again tomorrow.",
            )

        # Per-user budget check
        current_user_cost = self._get_user_cost(user_id, today)
        if current_user_cost >= self.daily_budget_usd:
            raise HTTPException(
                status_code=402,  # Payment Required
                detail={
                    "error": "Daily budget exceeded",
                    "used_usd": current_user_cost,
                    "budget_usd": self.daily_budget_usd,
                    "resets_at": "midnight UTC",
                },
            )

        # Warning khi gần hết budget
        if current_user_cost >= self.daily_budget_usd * self.warn_at_pct:
            logger.warning(
                f"User {user_id} at {current_user_cost/self.daily_budget_usd*100:.0f}% budget"
            )

    def record_usage(
        self, user_id: str, input_tokens: int, output_tokens: int
    ) -> UsageRecord:
        """Ghi nhận usage sau khi gọi LLM xong."""
        today = time.strftime("%Y-%m-%d")
        
        cost = (input_tokens / 1000 * PRICE_PER_1K_INPUT_TOKENS +
                output_tokens / 1000 * PRICE_PER_1K_OUTPUT_TOKENS)

        # TTL 32 ngày (để tự reset sau 1 tháng)
        ttl = 32 * 24 * 3600

        # Update Redis
        user_cost_key = f"cost_guard:user_cost:{user_id}:{today}"
        self.r.incrbyfloat(user_cost_key, cost)
        self.r.expire(user_cost_key, ttl)

        req_key = f"cost_guard:user_reqs:{user_id}:{today}"
        self.r.incr(req_key, 1)
        self.r.expire(req_key, ttl)

        in_tokens_key = f"cost_guard:user_in_tokens:{user_id}:{today}"
        self.r.incr(in_tokens_key, input_tokens)
        self.r.expire(in_tokens_key, ttl)

        out_tokens_key = f"cost_guard:user_out_tokens:{user_id}:{today}"
        self.r.incr(out_tokens_key, output_tokens)
        self.r.expire(out_tokens_key, ttl)

        global_cost_key = f"cost_guard:global_cost:{today}"
        self.r.incrbyfloat(global_cost_key, cost)
        self.r.expire(global_cost_key, ttl)

        total_in = int(self.r.get(in_tokens_key) or 0)
        total_out = int(self.r.get(out_tokens_key) or 0)
        total_reqs = int(self.r.get(req_key) or 0)

        record = UsageRecord(
            user_id=user_id,
            input_tokens=total_in,
            output_tokens=total_out,
            request_count=total_reqs,
            day=today
        )

        logger.info(
            f"Usage: user={user_id} req={record.request_count} "
            f"cost=${record.total_cost_usd:.4f}/{self.daily_budget_usd}"
        )
        return record

    def get_usage(self, user_id: str) -> dict:
        today = time.strftime("%Y-%m-%d")
        
        cost = self._get_user_cost(user_id, today)
        requests = int(self.r.get(f"cost_guard:user_reqs:{user_id}:{today}") or 0)
        in_tokens = int(self.r.get(f"cost_guard:user_in_tokens:{user_id}:{today}") or 0)
        out_tokens = int(self.r.get(f"cost_guard:user_out_tokens:{user_id}:{today}") or 0)

        return {
            "user_id": user_id,
            "date": today,
            "requests": requests,
            "input_tokens": in_tokens,
            "output_tokens": out_tokens,
            "cost_usd": cost,
            "budget_usd": self.daily_budget_usd,
            "budget_remaining_usd": max(0, self.daily_budget_usd - cost),
            "budget_used_pct": round(cost / self.daily_budget_usd * 100, 1) if self.daily_budget_usd else 0.0,
        }


# Singleton
cost_guard = CostGuard(daily_budget_usd=1.0, global_daily_budget_usd=10.0)
