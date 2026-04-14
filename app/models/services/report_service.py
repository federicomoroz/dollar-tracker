import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.report import ReportConfig
from app.models.repositories.report_repository import ReportRepository
from app.models.repositories.rate_repository import RateRepository
from app.models.services.email_service import EmailService

logger = logging.getLogger(__name__)

FREQUENCY_DELTA = {
    "hourly": timedelta(hours=1),
    "daily":  timedelta(days=1),
    "weekly": timedelta(weeks=1),
}


def _report_html(rates, stats_by_type: dict) -> str:
    rows = ""
    for rate in rates:
        stats = stats_by_type.get(rate.type, {})
        rows += f"""
        <tr>
          <td><b>{rate.name}</b></td>
          <td>${rate.sell:,.2f}</td>
          <td>${rate.buy:,.2f}" if rate.buy else "—"</td>
          <td>${stats.get('min_sell', '—')}</td>
          <td>${stats.get('max_sell', '—')}</td>
          <td>${stats.get('avg_sell', '—')}</td>
        </tr>"""
    return f"""
    <h2>Informe de cotizaciones — {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} UTC</h2>
    <table border="1" cellpadding="6" style="border-collapse:collapse;font-family:monospace">
      <thead>
        <tr>
          <th>Tipo</th><th>Venta actual</th><th>Compra actual</th>
          <th>Min 24h</th><th>Max 24h</th><th>Prom 24h</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    """


class ReportService:

    @staticmethod
    def create_report(db: Session, email: str, frequency: str) -> ReportConfig:
        report = ReportConfig(email=email, frequency=frequency)
        return ReportRepository.create(db, report)

    @staticmethod
    def list_reports(db: Session) -> list[ReportConfig]:
        return ReportRepository.get_all(db)

    @staticmethod
    def delete_report(db: Session, report_id: int) -> bool:
        report = ReportRepository.get_by_id(db, report_id)
        if not report:
            return False
        ReportRepository.delete(db, report)
        return True

    @staticmethod
    def send_due_reports(db: Session) -> None:
        reports = ReportRepository.get_active(db)
        if not reports:
            return

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        since_24h = now - timedelta(hours=24)
        latest_rates = RateRepository.get_latest(db)

        if not latest_rates:
            logger.info("No rates available yet — skipping reports.")
            return

        stats_by_type = {
            rate.type: RateRepository.get_stats(db, rate.type, since_24h)
            for rate in latest_rates
        }

        for report in reports:
            delta = FREQUENCY_DELTA.get(report.frequency, timedelta(days=1))
            if report.last_sent and (now - report.last_sent) < delta:
                continue

            html = _report_html(latest_rates, stats_by_type)
            subject = f"[Dollar Tracker] Informe {report.frequency} — {now.strftime('%d/%m/%Y')}"
            sent = EmailService.send(report.email, subject, html)
            if sent:
                ReportRepository.update_last_sent(db, report, now)
