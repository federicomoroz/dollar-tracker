import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import ALERT_COOLDOWN_HOURS
from app.models.alert import AlertConfig
from app.models.rate import Rate
from app.models.repositories.alert_repository import AlertRepository
from app.models.services.email_service import EmailService

logger = logging.getLogger(__name__)


def _alert_email_html(alert: AlertConfig, rate: Rate, breached: str) -> str:
    direction = "superó el máximo" if breached == "max" else "cayó por debajo del mínimo"
    threshold = alert.max_threshold if breached == "max" else alert.min_threshold
    return f"""
    <h2>Alerta de cotización — {rate.name}</h2>
    <p>El dólar <strong>{rate.name}</strong> {direction} configurado.</p>
    <table>
      <tr><td><b>Umbral configurado</b></td><td>${threshold:,.2f}</td></tr>
      <tr><td><b>Valor actual (venta)</b></td><td>${rate.sell:,.2f}</td></tr>
      <tr><td><b>Fecha</b></td><td>{rate.fetched_at.strftime('%d/%m/%Y %H:%M')} UTC</td></tr>
    </table>
    <p style="color:#888;font-size:0.85em">
      Próxima alerta disponible en {ALERT_COOLDOWN_HOURS}h.
    </p>
    """


class AlertService:

    @staticmethod
    def create_alert(db: Session, email: str, rate_type: str,
                     min_threshold: float | None, max_threshold: float | None) -> AlertConfig:
        alert = AlertConfig(
            email=email,
            rate_type=rate_type,
            min_threshold=min_threshold,
            max_threshold=max_threshold,
        )
        return AlertRepository.create(db, alert)

    @staticmethod
    def list_alerts(db: Session) -> list[AlertConfig]:
        return AlertRepository.get_all(db)

    @staticmethod
    def delete_alert(db: Session, alert_id: int) -> bool:
        alert = AlertRepository.get_by_id(db, alert_id)
        if not alert:
            return False
        AlertRepository.delete(db, alert)
        return True

    @staticmethod
    def check_and_notify(db: Session, rates: list[Rate]) -> None:
        alerts = AlertRepository.get_active(db)
        if not alerts:
            return

        rates_by_type = {r.type: r for r in rates}
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        cooldown = timedelta(hours=ALERT_COOLDOWN_HOURS)

        for alert in alerts:
            rate = rates_by_type.get(alert.rate_type)
            if not rate:
                continue

            if alert.last_alerted and (now - alert.last_alerted) < cooldown:
                continue

            breached = None
            if alert.max_threshold is not None and rate.sell > alert.max_threshold:
                breached = "max"
            elif alert.min_threshold is not None and rate.sell < alert.min_threshold:
                breached = "min"

            if breached:
                html = _alert_email_html(alert, rate, breached)
                subject = f"[Dollar Tracker] Alerta: {rate.name} {'supero maximo' if breached == 'max' else 'bajo minimo'}"
                sent = EmailService.send(alert.email, subject, html)
                if sent:
                    AlertRepository.update_last_alerted(db, alert, now)
