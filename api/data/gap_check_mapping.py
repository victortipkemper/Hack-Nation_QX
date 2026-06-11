"""
Maps solution-key gap types (Lösungsschlüssel) to primary checklist check_ids.
Used for calibration validation — NOT for per-file verdict hardcoding.
"""

# Primary check that must fire for each YELLOW gap type
GAP_PRIMARY_CHECKS: dict[str, list[str]] = {
    "load_index": ["L2-751-I.5.1.6"],
    "speed_rating": ["L2-751-I.5.1.4"],
    "r39_circumference": ["L2-R39-CIRC"],
    "brake_section_41": ["L2-751-I.5.1.10"],
    "wheel_cover_30c_36a": ["L2-751-I.5.1.8"],
    "tga_scope": ["L2-TGA-SCOPE"],
    "wheel_load_doc": ["L3-WHEEL-LOAD-DOC"],
    "min_rim_tga": ["L2-TGA-MIN-RIM"],
    "tga_auflage": ["L2-TGA-AUFLAGE"],
}

# If these L2 checks flag, suppress duplicate L3-AUFSTELLUNG flag
AUFSTELLUNG_DEDUPE_IF_FLAGGED = [
    "L2-R39-CIRC",
    "L2-751-I.5.1.10",
    "L2-751-I.5.1.8",
]
