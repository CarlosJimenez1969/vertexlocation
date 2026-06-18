"""
report_generator.py — Reporte mensual PDF para veterinario (plan Premium)
usando ReportLab.
"""
from __future__ import annotations

import io
import os
from datetime import date
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)

from app.core.config import settings

# Paleta VertexMascota
AZUL = colors.HexColor("#3B82F6")
FONDO = colors.HexColor("#0A0E1A")
EXITO = colors.HexColor("#10B981")


def generate_vet_report(
    pet: dict[str, Any],
    periodo: tuple[date, date],
    resumen: dict[str, Any],
    output_dir: str | None = None,
) -> str:
    """
    Genera un PDF de reporte veterinario y devuelve la ruta del archivo.

    Args:
        pet: {nombre, raza, edad, sexo, peso_kg, ...}
        periodo: (fecha_inicio, fecha_fin)
        resumen: {
            actividad: {promedio_pasos, distancia_total_km, calorias_prom, ...},
            animo: {distribucion: {feliz: %, ...}, dominante: 'tranquilo'},
            anomalias: [ "texto", ... ],
        }
    """
    output_dir = output_dir or settings.UPLOAD_DIR
    os.makedirs(output_dir, exist_ok=True)
    inicio, fin = periodo
    filename = f"reporte_vet_{pet.get('nombre','mascota')}_{inicio}_{fin}.pdf".replace(" ", "_")
    path = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Titulo", fontSize=20, textColor=AZUL, spaceAfter=6, leading=24))
    styles.add(ParagraphStyle(name="Sub", fontSize=13, textColor=colors.HexColor("#1E3A6B"), spaceAfter=10))
    styles.add(ParagraphStyle(name="H2", fontSize=14, textColor=AZUL, spaceBefore=14, spaceAfter=6))

    el: list = []
    el.append(Paragraph("VertexLocation · Reporte Veterinario", styles["Titulo"]))
    el.append(Paragraph(f"Periodo: {inicio.strftime('%d/%m/%Y')} — {fin.strftime('%d/%m/%Y')}", styles["Sub"]))
    el.append(Spacer(1, 0.3 * cm))

    # --- Datos de la mascota ---
    el.append(Paragraph("Datos de la mascota", styles["H2"]))
    pet_rows = [
        ["Nombre", pet.get("nombre", "—")],
        ["Especie / Raza", f"{pet.get('especie','perro')} / {pet.get('raza','—')}"],
        ["Sexo", pet.get("sexo", "—")],
        ["Edad", _format_edad(pet)],
        ["Peso", f"{pet.get('peso_kg','—')} kg"],
    ]
    el.append(_tabla(pet_rows))

    # --- Resumen de actividad ---
    act = resumen.get("actividad", {})
    el.append(Paragraph("Resumen de actividad", styles["H2"]))
    act_rows = [
        ["Métrica", "Valor"],
        ["Promedio de pasos/día", str(act.get("promedio_pasos", "—"))],
        ["Distancia total", f"{act.get('distancia_total_km', '—')} km"],
        ["Calorías promedio/día", str(act.get("calorias_prom", "—"))],
        ["Minutos activo/día", str(act.get("minutos_activo_prom", "—"))],
        ["Minutos reposo/día", str(act.get("minutos_reposo_prom", "—"))],
    ]
    el.append(_tabla(act_rows, header=True))

    # --- Estado de ánimo ---
    animo = resumen.get("animo", {})
    el.append(Paragraph("Estado de ánimo (distribución)", styles["H2"]))
    dist = animo.get("distribucion", {})
    animo_rows = [["Estado", "% del periodo"]] + [
        [k.replace("_", " ").capitalize(), f"{v}%"] for k, v in dist.items()
    ]
    el.append(_tabla(animo_rows, header=True))
    el.append(Spacer(1, 0.2 * cm))
    el.append(Paragraph(f"<b>Ánimo dominante:</b> {animo.get('dominante','—')}", styles["Normal"]))

    # --- Anomalías / observaciones ---
    anomalias = resumen.get("anomalias", [])
    if anomalias:
        el.append(Paragraph("Observaciones para el veterinario", styles["H2"]))
        for a in anomalias:
            el.append(Paragraph(f"• {a}", styles["Normal"]))

    el.append(Spacer(1, 1 * cm))
    el.append(Paragraph(
        "Generado automáticamente por VertexLocation a partir de la telemetría del collar C059. "
        "Este reporte es informativo y no sustituye el diagnóstico profesional.",
        ParagraphStyle(name="pie", fontSize=8, textColor=colors.grey),
    ))

    doc.build(el)
    return path


def _tabla(rows: list[list[str]], header: bool = False) -> Table:
    t = Table(rows, hAlign="LEFT", colWidths=[7 * cm, 9 * cm])
    style = [
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#1E3A6B")),
        ("TEXTCOLOR", (0, 0), (0, -1), AZUL),
    ]
    if header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), AZUL),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]
    t.setStyle(TableStyle(style))
    return t


def _format_edad(pet: dict[str, Any]) -> str:
    if pet.get("edad_meses"):
        meses = pet["edad_meses"]
        return f"{meses // 12} años {meses % 12} meses" if meses >= 12 else f"{meses} meses"
    return str(pet.get("edad", "—"))
