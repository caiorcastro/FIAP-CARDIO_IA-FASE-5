import os
import smtplib
from email.mime.text import MIMEText
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI(title="CardioIA REST Alerts")


class Vitals(BaseModel):
    ts: Optional[int] = Field(None, description="Epoch seconds")
    temp: float
    hum: Optional[float] = None
    bpm: Optional[float] = None


def risk_check(v: Vitals) -> dict:
    alerts = []
    if v.bpm is not None and v.bpm > 120:
        alerts.append("Taquicardia")
    if v.temp is not None and v.temp > 38:
        alerts.append("Febre")
    risk = "alto" if alerts else "baixo"
    return {"risk": risk, "alerts": alerts}


def send_email(subject: str, body: str) -> dict:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    from_addr = os.getenv("FROM_EMAIL")
    to_addr = os.getenv("TO_EMAIL")

    if not all([host, user, password, from_addr, to_addr]):
        # Modo simulado
        print(f"[EMAIL-SIM] {subject}\n{body}")
        return {"status": "simulated"}

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(from_addr, [to_addr], msg.as_string())
    return {"status": "sent"}


@app.post("/vitals")
def post_vitals(v: Vitals):
    result = risk_check(v)
    if result["risk"] == "alto":
        subject = "[CardioIA] Alerta de risco"
        body = f"Risco alto: {', '.join(result['alerts'])}\nDados: {v.model_dump()}"
        email_info = send_email(subject, body)
        result["email"] = email_info
    return result

