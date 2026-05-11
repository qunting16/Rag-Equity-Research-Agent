"""Generate daily morning investment brief."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.agents.morning_brief_agent import MorningBriefAgent


def main() -> None:
    Path("reports").mkdir(exist_ok=True)

    agent = MorningBriefAgent()
    result = agent.generate(limit=80)

    today = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%d")
    output_path = Path(f"reports/morning_brief_{today}.md")

    output_path.write_text(result["markdown"], encoding="utf-8")

    print(f"saved: {output_path}")


if __name__ == "__main__":
    main()
