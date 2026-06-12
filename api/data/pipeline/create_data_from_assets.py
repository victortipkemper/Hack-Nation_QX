#!/usr/bin/env python3
"""
Pipeline script to extract structured rules and thresholds from legal texts
using gpt-5.4-nano and Instructor.
"""
import os
import sys
import json
import time
import logging
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("create_data_pipeline.log")
    ]
)

# Ensure api directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from dotenv import load_dotenv
load_dotenv()

import instructor
from openai import OpenAI


# ── Pydantic Models for Schema Enforce ────────────────────────────────

class RuleMetadata(BaseModel):
    check_id: str = Field(description="Unique ID for the check (e.g., L2-STVZO-36a, L2-R39-CIRC)")
    level: int = Field(description="Standard compliance level: 1 for StVZO (formales Recht), 2 for Merkblatt 751, 3 for TÜV-Praxis, 4 for Konsens")
    check_name: str = Field(description="Human-readable name of the checklist rule")
    citation: str = Field(description="Legal text paragraph citation (e.g., § 36a StVZO, § 57 Abs. 3 StVZO)")


class RuleMapping(BaseModel):
    applicable_fields: List[str] = Field(description="List of fields from DocumentFeatures checked for applicability (e.g., has_wheel_change, has_spacers, vmax_kmh, is_ev, rolling_circumference_delta_pct)")
    evaluate_fields: List[str] = Field(description="List of fields from DocumentFeatures checked for evaluation (e.g., aufstellung.section_36a_na, raw_text)")


class RuleExemption(BaseModel):
    condition: Optional[str] = Field(description="Python-like boolean expression defining the exemption condition using 'features' prefix (e.g., features.vmax_kmh <= 25)")
    reason: Optional[str] = Field(description="Reason why the rule is exempt/N/A under this condition")


class RuleEvaluationLogic(BaseModel):
    rule_description: str = Field(description="A clear description of what is checked and when it fails")
    expected_expression: str = Field(description="Python-like expression representing the passing condition using 'features' prefix")


class LegalTextRuleEntry(BaseModel):
    metadata: RuleMetadata
    mapping: RuleMapping
    parameters: Dict[str, float] = Field(default_factory=dict, description="Numerical thresholds or tolerance values converted for Gutachten (e.g. upper_limit_pct: 1.0, lower_limit_pct: -8.0)")
    exemptions: Optional[RuleExemption] = None
    evaluation_logic: RuleEvaluationLogic


class LegalTextAnalysisResult(BaseModel):
    rules: List[LegalTextRuleEntry] = Field(default_factory=list, description="List of rules extracted from this legal text. Return empty list if no rules relevant to vehicle modifications exist.")


SYSTEM_PROMPT = (
    "You are an expert in automotive legal regulations and vehicle inspection standards (TÜV-Sachverständiger).\n"
    "Your task is to analyze the provided StVZO German legal text and extract structured checklist rules "
    "that are relevant to vehicle modification verification (e.g. wheel/tire changes, braking modifications, "
    "track widening, speed indicators, emissions, weights/dimensions, etc.).\n\n"
    "Translate abstract legal tolerances (like speedometer or odometer display tolerances) into "
    "verifiable report metrics (like rolling circumference change percentage thresholds: +1.0% to -8.0% in Germany).\n"
    "If the legal text has no relevance to standard modification checks, return an empty list of rules.\n"
    "Ensure all python expressions in exemptions/logic use attributes from the 'features' object correctly."
)


def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logging.error("OPENAI_API_KEY is not set in the environment.")
        sys.exit(1)

    assets_dir = os.path.join(current_dir, "assets")
    if not os.path.exists(assets_dir):
        logging.error(f"Assets directory not found at {assets_dir}")
        sys.exit(1)

    # Initialize Instructor client
    client = instructor.from_openai(OpenAI(api_key=api_key))

    # Read assets
    files = sorted([f for f in os.listdir(assets_dir) if f.endswith(".txt")])
    logging.info(f"Found {len(files)} legal text assets. Starting rule extraction...")

    all_rules: Dict[str, dict] = {}
    
    for idx, filename in enumerate(files, 1):
        filepath = os.path.join(assets_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            text_content = f.read()

        para_name = filename.replace("stvzo_", "").replace(".txt", "")
        logging.info(f"[{idx}/{len(files)}] Processing § {para_name}...")

        try:
            response = client.chat.completions.create(
                model="gpt-5.4-nano",
                response_model=LegalTextAnalysisResult,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Filename: {filename}\nContent:\n{text_content}"}
                ],
            )
            
            # Print if rules were found
            if response.rules:
                logging.info(f"  Extracted {len(response.rules)} rules:")
                for rule in response.rules:
                    rule_id = rule.metadata.check_id
                    # Convert Pydantic object to dict
                    all_rules[rule_id] = rule.model_dump()
                    logging.info(f"    - {rule_id}: {rule.metadata.check_name}")
            else:
                logging.info("  No relevant rules found.")

        except Exception as e:
            logging.error(f"  ERROR processing {filename}: {e}")

        # Brief rate limit sleep
        time.sleep(0.5)

    # Save output
    output_path = os.path.join(current_dir, "assets_rules.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_rules, f, indent=2, ensure_ascii=False)

    logging.info(f"Rule extraction finished. Saved {len(all_rules)} rules to {output_path}")


if __name__ == "__main__":
    main()
