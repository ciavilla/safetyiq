"""
scripts/run_ingestion.py
Run this script to ingest your OSHA PDF files into the database.

Usage:
    python3 scripts/run_ingestion.py

Make sure you have:
  1. Docker running with the database container up (docker-compose up -d)
  2. Your .env file configured
  3. PDF files downloaded to data/pdfs/

To download PDFs automatically, set DOWNLOAD_PDFS = True below.
"""

import sys
import os
import httpx
from pathlib import Path

# Add the project root to Python's path so we can import from app/
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, init_db

# ─────────────────────────────────────────────
# CONFIGURATION — edit these as needed
# ─────────────────────────────────────────────

# Set to True to automatically download PDFs from OSHA's website
DOWNLOAD_PDFS = True

# OSHA PDFs to ingest — add or remove as you like
# Format: (url, filename, human-readable title)
OSHA_PDFS = [
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3903.pdf",
        "osha_fall_protection_general_factsheet.pdf",
        "OSHA Fall Protection General Industry Factsheet"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/PPE-FACTSHEET.pdf",
        "osha_personal_protective_equipment_factsheet.pdf",
        "OSHA Personal Protective Equipment Factsheet"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3151.pdf",
        "osha_personal_protective_equipment.pdf",
        "OSHA Personal Protective Equipment"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHAFS3529.pdf",
        "osha_lockout_tagout_factsheet.pdf",
        "OSHA Lockout Tagout Factsheet"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/PORTABLE_LADDER_QC.pdf",
        "osha_portable_ladder_quickcard.pdf",
        "OSHA Portable Ladder Safety Quickcard"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3660.pdf",
        "osha_extension_ladder_factsheet.pdf",
        "OSHA Extension Ladder Safety FactSheet"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3662.pdf",
        "osha_step_ladder_factsheet.pdf",
        "OSHA Step Ladder Safety FactSheet"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3722.pdf",
        "osha_narrow_frame_scaffold_factsheet.pdf",
        "OSHA Narrow Frame Scaffold FactSheet"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3857.pdf",
        "osha_ladder_jack_scaffold_factsheet.pdf",
        "OSHA Ladder Jack Scaffold FactSheet"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA_FS-3759.pdf",
        "osha_tube_and_coupler_scaffold_factsheet.pdf",
        "OSHA Tube And Coupler Scaffold Erection and Use FactSheet"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA_FS-3760.pdf",
        "osha_tube_and_coupler_scaffold_design_factsheet.pdf",
        "OSHA Tube And Coupler Scaffold Planning and Design FactSheet"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3788.pdf",
        "osha_confined_space_pits_factsheet.pdf",
        "OSHA Confined Spaces in Construction Pits FactSheet"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/ATMOSPHERIC_TEST_CONFINED.pdf",
        "osha_confined_space_atmospheric_testing_factsheet.pdf",
        "OSHA Confined Spaces Atmospheric Testing FactSheet"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/CONFINED_SPACE_PERMIT.pdf",
        "osha_confined_space_permit_required_quickcard.pdf",
        "OSHA Confined Spaces Permit Required QuickCard"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA4495.pdf",
        "osha_extension_cord_quickcard.pdf",
        "OSHA Extension Cord QuickCard"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3124.pdf",
        "osha_stairways_ladder_guide.pdf",
        "OSHA Stairways and Ladders Guide"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3138.pdf",
        "osha_confined_space_guide.pdf",
        "OSHA Confined Spaces Permit-Required Guide"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/CONSTRUCTION_PPE.pdf",
        "osha_ppe_quickcard.pdf",
        "OSHA Construction PPE Quickcard"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3146.pdf",
        "osha_fall_protection_guide.pdf",
        "OSHA Fall Protection in Construction Guide"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3120.pdf",
        "osha_lockout_tagout_guide.pdf",
        "OSHA Lockout Tagout Guide"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3150.pdf",
        "osha_scaffold_guide.pdf",
        "OSHA Scaffold Use in Construction Guide"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3150.pdf",
        "osha_scaffold_guide.pdf",
        "OSHA Scaffold Use in Construction Guide"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3666.pdf",
        "osha_fall_arrest_systems.pdf",
        "OSHA Fall Protection Personal Fall Arrest Systems"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/SAFETY_HELMET_SHIB.pdf",
        "osha_safety_helmets.pdf",
        "OSHA Safety Helmets Head Protection"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3074.pdf",
        "osha_hearing_conservation_guide.pdf",
        "OSHA Hearing Conservation Guide"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/HEARING_PROTECTOR_FIT_TESTING_SHIB.pdf",
        "osha_hearing_protector_fit.pdf",
        "OSHA Hearing Protector Fit Testing Guide"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3172.pdf",
        "osha_hazardous_chemicals.pdf",
        "OSHA Hazardous Chemicals Exposure"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/SHIB092203.pdf",
        "osha_Personal_Fall_Protection.pdf",
        "OSHA Personal Fall Protection System Components"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3825.pdf",
        "osha_confined_spaces.pdf",
        "OSHA Confined Spaces and Permit Spaces Guide"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3695.pdf",
        "osha_hazard_communication_Hazard_Chemicals.pdf",
        "OSHA Hazard Communication for Use of Hazardous Chemicals Guide"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/HYDROGEN_SULFIDE_FACT.pdf",
        "osha_hydrogen_sulfide_factsheet.pdf",
        "OSHA Hydrogen Sulfide H2S FactSheet"
    ),
]
OSHA_HTML_PAGES = [
    (
        "https://www.osha.gov/publications/hib19960514",
        "Chemical Exposure from Industrial Valve And Piping Systems"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.21",
        "Regulations Standards 1910.21 Walking-Working Surfaces Scope and definitions"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.22",
        "Regulations Standards 1910.22 Walking-Working Surfaces General requirements"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.23",
        "Regulations Standards 1910.23 Walking-Working Surfaces Ladders"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.24",
        "Regulations Standards 1910.24 Walking-Working Surfaces Step bolts and manhole steps"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.25",
        "Regulations Standards 1910.25 Walking-Working Surfaces Stairways"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.26",
        "Regulations Standards 1910.26 Walking-Working Surfaces Dockboards"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.27",
        "Regulations Standards 1910.27 Walking-Working Surfaces Scaffolds and rope descent systems"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.28",
        "Regulations Standards 1910.28 Walking-Working Surfaces Duty to have Fall Protection and Falling Object Protection"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.29",
        "Regulations Standards 1910.29 Walking-Working Surfaces Duty to have Fall Protection and Falling Object Protection Criteria and Practices"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.30",
        "Regulations Standards 1910.30 Walking-Working Surfaces Fall Protection Training requirements"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.66",
        "Regulations Standards 1910.66 Powered Platforms, Manlifts, and vehicle-mounted Work Platforms for building maintenance"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.66AppA",
        "Regulations Standards 1910.66AppA Powered Platforms, Manlifts, and vehicle-mounted Work Platforms Guidelines (advisory)"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.66AppD",
        "Regulations Standards 1910.66AppD Powered Platforms, Manlifts, and vehicle-mounted Work Platforms Existing Installations (Mandatory)"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.67",
        "Regulations Standards 1910.67 vehicle-mounted Work Platforms"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.68",
        "Regulations Standards 1910.68 Manlifts"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.95",
        "Regulations Standards 1910.95 Occupational Noise Exposure"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.101",
        "Regulations Standards 1910.101 Hazardous Materials Compressed gases general requirements"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.119AppA",
        "Regulations Standards 1910.119AppA List of Highly Hazardous Chemicals, Toxics"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.119",
        "Regulations Standards 1910.119 Highly Hazardous Chemicals Process safety management"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.102",
        "Regulations Standards 1910.102 Hazardous Materials Acetylene"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.132",
        "Regulations Standards 1910.132 Personal Protective Equipment General Requirements"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.133",
        "Regulations Standards 1910.133 Personal Protective Equipment Eye and Face Protection"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.134",
        "Regulations Standards 1910.134 Personal Protective Equipment Respiratory Protection"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.134AppA",
        "Regulations Standards 1910.134AppA Personal Protective Equipment Respiratory Protection Fit Testing Procedures"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.134AppB1",
        "Regulations Standards 1910.134AppB1 Personal Protective Equipment Respiratory Protection User Seal Check Procedures"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.134AppB2",
        "Regulations Standards 1910.134AppB2 Personal Protective Equipment Respiratory Protection Respirator Cleaning Procedures"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.135",
        "Regulations Standards 1910.135 Personal Protective Equipment Head Protection"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.136",
        "Regulations Standards 1910.136 Personal Protective Equipment Foot Protection"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.137",
        "Regulations Standards 1910.137 Personal Protective Equipment Electrical Protective Equipment"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.138",
        "Regulations Standards 1910.138 Personal Protective Equipment Hand Protection"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.140",
        "Regulations Standards 1910.140 Personal Protective Equipment Personal Fall Protection Systems"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910SubpartIAppC",
        "Regulations Standards 1910 Personal Protective Equipment Personal Fall Protection Guidelines non-mandatory"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.144",
        "Regulations Standards 1910.144 General Environmental Controls Safety Color for marking physical hazards"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.146",
        "Regulations Standards 1910.146 General Environmental Controls Permit Required Confined Spaces"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.146AppB",
        "Regulations Standards 1910.146AppB General Environmental Controls Permit Required Confined Spaces Procedure for Atmospheric Testing"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.146AppC",
        "Regulations Standards 1910.146AppC General Environmental Controls Permit Required Confined Spaces Examples"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.147",
        "Regulations Standards 1910.147 General Environmental Controls Lockout/Tagout the control of hazardous energy"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.155",
        "Regulations Standards 1910.155 Fire Protection Scope, appliocation and definitions"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.157",
        "Regulations Standards 1910.157 Fire Protection Portable Fire Extinguishers"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910SubpartLAppA",
        "Regulations Standards 1910 Fire Protection"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.169",
        "Regulations Standards 1910.169 Compressed Gas and Compressed Air Equipment Air Receivers"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.176",
        "Regulations Standards 1910.176 Materials Handling and Storage General Handling Materials"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.178",
        "Regulations Standards 1910.178 Materials Handling and Storage Powered Industrial Trucks"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.178AppA",
        "Regulations Standards 1910.178AppA Materials Handling and Storage Powered Industrial Trucks Stability"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.179",
        "Regulations Standards 1910.179 Materials Handling and Storage Overhead and Gantry Cranes"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.180",
        "Regulations Standards 1910.180 Materials Handling and Storage Crawler Locomotive and Truck Cranes"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.181",
        "Regulations Standards 1910.181 Materials Handling and Storage Derricks"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.183",
        "Regulations Standards 1910.183 Materials Handling and Storage Helicopters"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.184",
        "Regulations Standards 1910.184 Materials Handling and Storage Slings"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.212",
        "Regulations Standards 1910.212 Machinery and Machine Guarding General requirements for all machines"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.241",
        "Regulations Standards 1910.241 Hand and Portable Powered Tools and Other Hand-Held Equipment Definitions"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.242",
        "Regulations Standards 1910.242 Hand and Portable Powered Tools and Other Hand-Held Equipment General Information"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.243",
        "Regulations Standards 1910.243 Hand and Portable Powered Tools and Other Hand-Held Equipment Guarding of Portable Powered Tools"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.244",
        "Regulations Standards 1910.244 Hand and Portable Powered Tools and Other Hand-Held Equipment Other Portable Tools and Equipment"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.252",
        "Regulations Standards 1910.252 Welding Cutting and Brazing General Requirements"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.253",
        "Regulations Standards 29 CFR 1910 Welding Cutting and Brazing Oxygen-Fuel Gas Welding and Cutting"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.254",
        "Regulations Standards 29 CFR 1910 Welding Cutting and Brazing Arc Welding and Cutting"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.255",
        "Regulations Standards 1910 Subpart Q 1910.255 Welding Cutting and Brazing: Resistance Welding"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.303",
        "Regulations Standards 1910 Subpart S 1910.303 Electrical General Information"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.335",
        "Regulations Standards 1910 Subpart S 1910.335 Electrical Personal Protective Equipment"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1000",
        "Regulations Standards 1910 Subpart Z 1910.1000 Toxic and Hazardous Substances: Ait Contaminants"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1000TABLEZ2",
        "Regulations Standards 1910 Subpart Z 1910.1000 Toxic and Hazardous Substances: Table Z"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1000TABLEZ3",
        "Regulations Standards 1910 Subpart Z 1910.1000 Toxic and Hazardous Substances: Table Z-3 Mineral Dusts"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1000TABLEZ1",
        "Regulations Standards 1910 Subpart Z 1910.1000 Toxic and Hazardous Substances: Table Z-1 Limits for Air Contaminants"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1200",
        "Regulations Standards 1910.1200 Hazard Communication"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1200AppA",
        "Regulations Standards 1910 Subpart Z Toxic And Hazardous Substances: Health Hazard Criteria (Mandatory)"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1200AppB",
        "Regulations Standards 1910 Subpart Z Toxic And Hazardous Substances: Physical Criteria (Mandatory)"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1200AppC",
        "Regulations Standards 1910 Subpart Z Toxic And Hazardous Substances: Allocation Of Label Elements (Mandatory)"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1200AppD",
        "Regulations Standards 1910 Subpart Z Toxic And Hazardous Substances: Safety Data Sheets (Mandatory)"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1201",
        "Regulations Standards 1910 Subpart Z Toxic And Hazardous Substances: Retention of DOT markings, placards, and labels"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.20",
        "1926 Subpart C - General Safety and Health Provisions 1926.20 - General safety and health provisions."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.21",
        "1926 Subpart C - General Safety and Health Provisions 1926.21 - Safety training and education."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.24",
        "1926.24 - Fire protection and prevention."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.25",
        "1926.25 - Housekeeping."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.26",
        "1926.26 - Illumination."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.32",
        "1926.32 - Definitions."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.34",
        "1926.34 - Means of egress."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.35",
        "1926.35 - Employee emergency action plans."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.50",
        "1926 Subpart D - Occupational Health and Environmental Controls 1926.50 - Medical services and first aid."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.51",
        "1926.51 - Sanitation."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.52",
        "1926.52 - Occupational noise exposure."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.55",
        "1926.55 - Gases, vapors, fumes, dusts, and mists."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.56",
        "1926.56 - Illumination."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.57",
        "1926.57 - Ventilation."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.65",
        "1926.65 - Hazardous waste operations and emergency response."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.95",
        "1926 Subpart E - Personal Protective and Life Saving Equipment 1926.95 - Criteria for personal protective equipment."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.97",
        "1926.97 - Electrical protective equipment."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.100",
        "1926.100 - Head protection."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.101",
        "1926.101 - Hearing protection."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.102",
        "1926.102 - Eye and face protection."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.104",
        "1926.104 - Safety belts, lifelines, and lanyards."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.105",
        "1926.105 - Safety nets."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.106",
        "1926.106 - Working over or near water."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.107",
        "1926.107 - Definitions applicable to this subpart."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.150",
        "1926 Subpart F - Fire Protection and Prevention 1926.150 - Fire protection."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.151",
        "1926.151 - Fire prevention"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.152",
        "1926.152 - Flammable liquids."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.153",
        "1926.153 - Liquefied petroleum gas (LP-Gas)."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.154",
        "1926.154 - Temporary heating devices."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.155",
        "1926.155 - Definitions applicable to this subpart."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.200",
        "1926 Subpart G - Signs, Signals, and Barricades 1926.200 - Accident prevention signs and tags."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.201",
        "1926.201 - Signaling."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.250",
        "1926 Subpart H - Materials Handling, Storage, Use, and Disposal"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.251",
        "1926.251 - Rigging equipment for material handling."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.252",
        "1926.252 - Disposal of waste materials."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.300",
        "1926 Subpart I - Tools-Hand and Power 1926.300 - General requirements."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.301",
        "1926.301 - Hand tools."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.302",
        "1926.302 - Power-operated hand tools."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.303",
        "1926.303 - Abrasive wheels and tools."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.304",
        "1926.304 - Woodworking tools."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.305",
        "1926.305 - Jacks-lever and ratchet, screw, and hydraulic."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.306",
        "1926.306 - Air receivers."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.307",
        "1926.307 - Mechanical power-transmission apparatus."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.350",
        "1926 Subpart J - Welding and Cutting 1926.350 - Gas welding and cutting."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.351",
        "1926.351 - Arc welding and cutting."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.352",
        "1926.352 - Fire prevention."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.353",
        "1926.353 - Ventilation and protection in welding, cutting, and heating."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.354",
        "1926.354 - Welding, cutting, and heating in way of preservative coatings."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.400",
        "1926 Subpart K - Electrical 1926.400 - Introduction."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.402",
        "1926.402 - Applicability."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.403",
        "1926.403 - General requirements."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.416",
        "1926.416 - General requirements."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.417",
        "1926.417 - Lockout and tagging of circuits."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.431",
        "1926.431 - Maintenance of equipment."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.441",
        "1926.441 - Batteries and battery charging."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.449",
        "1926.449 - Definitions applicable to this subpart."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.450",
        "1926 Subpart L - Scaffolds 1926.450 - Scope, application and definitions applicable to this subpart."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.451",
        "1926.451 - General requirements."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.452",
        "1926.452 - Additional requirements applicable to specific types of scaffolds."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.453",
        "1926.453 - Aerial lifts."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.454",
        "1926.454 - Training requirements."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926SubpartLAppA",
        "1926 Subpart L App A - Scaffold Specifications"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926SubpartLAppD",
        "1926 Subpart L App D - List of Training Topics for Scaffold Erectors and Dismantlers."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.500",
        "1926 Subpart M - Fall Protection 1926.500 - Scope, application, and definitions applicable to this subpart."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.501",
        "1926.501 - Duty to have fall protection."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.502",
        "1926.502 - Fall protection systems criteria and practices."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.503",
        "1926.503 - Training requirements."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926SubpartMAppB",
        "1926 Subpart M App B - Guardrail Systems - Non-Mandatory Guidelines for Complying with 1926.502(b)"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926SubpartMAppC",
        "1926 Subpart M App C - Personal Fall Arrest Systems - Non-Mandatory Guidelines for Complying with 1926.502(d)"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926SubpartMAppD",
        "1926 Subpart M App D - Positioning Device Systems - Non-Mandatory Guidelines for Complying with 1926.502(e)"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.551",
        "1926 Subpart N - Helicopters, Hoists, Elevators, and Conveyors 1926.551 - Helicopters."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.552",
        "1926.552 - Material hoists, personnel hoists, and elevators."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.553",
        "1926.553 - Base-mounted drum hoists."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.554",
        "1926.554 - Overhead hoists."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.555",
        "1926.555 - Conveyors."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.600",
        "1926 Subpart O - Motor Vehicles, Mechanized Equipment, and Marine Operations 1926.600 - Equipment."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.601",
        "1926.601 - Motor vehicles."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.602",
        "1926.602 - Material handling equipment."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.603",
        "1926.603 - Pile driving equipment."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.604",
        "1926.604 - Site clearing."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.650",
        "1926 Subpart P - Excavations 1926.650 - Scope, application, and definitions applicable to this subpart."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.651",
        "1926.651 - Specific Excavation Requirements."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.652",
        "1926.652 - Requirements for protective systems."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.700",
        "1926 Subpart Q - Concrete and Masonry Construction 1926.700 - Scope, application, and definitions applicable to this subpart."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.701",
        "1926.701 - General requirements"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.702",
        "1926.702 - Requirements for equipment and tools."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.703",
        "1926.703 - Requirements for cast-in-place concrete."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.704",
        "1926.704 - Requirements for precast concrete."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.705",
        "1926.705 - Requirements for lift-slab construction operations."
    ),
     (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.706",
        "1926.706 - Requirements for masonry construction."
    ),
     (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.750",
        "1926 Subpart R - Steel Erection 1926.750 - Scope."
    ),
     (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.751",
        "1926.751 - Definitions."
    ),
     (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.752",
        "1926.752 - Site layout, site-specific erection plan and construction sequence."
    ),
     (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.753",
        "1926.753 - Hoisting and rigging."
    ),
     (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.754",
        "1926.754 - Structural steel assembly."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.755",
        "1926.755 - Column anchorage."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.756",
        "1926.756 - Beams and columns."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.757",
        "1926.757 - Open web steel joists."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.758",
        "1926.758 - Systems-engineered metal buildings."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.759",
        "1926.759 - Falling object protection."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.760",
        "1926.760 - Fall protection."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.761",
        "1926.761 - Training."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.800",
        "1926 Subpart S - Underground Construction, Caissons, Cofferdams, and Compressed Air 1926.800 - Underground Construction"
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.801",
        "1926.801 - Caissons."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.802",
        "1926.802 - Cofferdams."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.803",
        "1926.803 - Compressed air."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.804",
        "1926.804 - Definitions applicable to this subpart."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.850",
        "1926 Subpart T - Demolition 1926.850 - Preparatory operations."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.900",
        "1926 Subpart U - Blasting and the Use of Explosives 1926.900 - General provisions."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.950",
        "1926 Subpart V - Electric Power Transmission and Distribution 1926.950 - General."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1000",
        "1926 Subpart W - Rollover Protective Structures; Overhead Protection 1926.1000 - Scope."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1001",
        "1926.1001 - Minimum performance criteria for rollover protective structures for designated scrapers, loaders, dozers, graders, crawler tractors, compactors, and rubber-tired skid steer equipment."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1002",
        "1926.1002 - Protective frames (roll-over protective structures, known as ROPS) for wheel-type agricultural and industrial tractors used in construction."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1003",
        "1926.1003 - Overhead protection for operators of agricultural and industrial tractors used in construction."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1050",
        "1926 Subpart X - Stairways and Ladders 1926.1050 - Scope, application, and definitions applicable to this subpart."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1051",
        "1926.1051 - General requirements."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1052",
        "1926.1052 - Stairways."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1053",
        "1926.1053 - Ladders."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1060",
        "1926.1060 - Training requirements."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1201",
        "1926 Subpart AA - Confined Spaces in Construction 1926.1201 - Scope."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1202",
        "1926.1202 - Definitions."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1203",
        "1926.1203 - General requirements."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1204",
        "1926.1204 - Permit-required confined space program."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1205",
        "1926.1205 - Permitting process."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1206",
        "1926.1206 - Entry permit."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1207",
        "1926.1207 - Training."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1208",
        "1926.1208 - Duties of authorized entrants."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1209",
        "1926.1209 - Duties of attendants."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1210",
        "1926.1210 - Duties of entry supervisors."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1211",
        "1926.1211 - Rescue and emergency services."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1212",
        "1926.1212 - Employee participation."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1400",
        "1926 Subpart CC - Cranes and Derricks in Construction 1926.1400 - Scope."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1401",
        "1926.1401 - Definitions."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1402",
        "1926.1402 - Ground conditions."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1404",
        "1926.1404 - Assembly/Disassembly—general requirements (applies to all assembly and disassembly operations)."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1405",
        "1926.1405 - Disassembly—additional requirements for dismantling of booms and jibs (applies to both the use of manufacturer procedures and employer procedures)."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1407",
        "1926.1407 - Power line safety (up to 350 kV)—assembly and disassembly."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1408",
        "1926.1408 - Power line safety (up to 350 kV)—equipment operations."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1410",
        "1926.1410 - Power line safety (all voltages)—equipment operations closer than the Table A zone."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1409",
        "1926.1409 - Power line safety (over 350 kV)."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1411",
        "1926.1411 - Power line safety—while traveling under or near power lines with no load."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1412",
        "1926.1412 - Inspections."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1413",
        "1926.1413 - Wire rope—inspection."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1414",
        "1926.1414 - Wire rope—selection and installation criteria."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1415",
        "1926.1415 - Safety devices."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1416",
        "1926.1416 - Operational aids."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1417",
        "1926.1417 - Operation."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1418",
        "1926.1418 - Authority to stop operation."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1419",
        "1926.1419 - Signals—general requirements."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1423",
        "1926.1423 - Fall protection."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1424",
        "1926.1424 - Work area control."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1425",
        "1926.1425 - Keeping clear of the load."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1426",
        "1926.1426 - Free fall and controlled load lowering."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1427",
        "1926.1427 - Operator training, certification, and evaluation."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1428",
        "1926.1428 - Signal person qualifications."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1430",
        "1926.1430 - Training."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1431",
        "1926.1431 - Hoisting personnel."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1433",
        "1926.1433 - Design, construction and testing."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1434",
        "1926.1434 - Equipment modifications."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1435",
        "1926.1435 - Tower cranes."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1436",
        "1926.1436 - Derricks."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1438",
        "1926.1438 - Overhead & gantry cranes."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1439",
        "1926.1439 - Dedicated pile drivers."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1440",
        "1926.1440 - Sideboom cranes."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1441",
        "1926.1441 - Equipment with a rated hoisting/ lifting capacity of 2,000 pounds or less."
    ),
    (
        "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.1442",
        "1926.1442 - Railroad roadway maintenance machines."
    ),
    (
        "",
        ""
    ),
    # add more as needed
]
PDF_DIR = Path(__file__).parent.parent / "data" / "pdfs"

# ─────────────────────────────────────────────


def download_pdfs():
    """Downloads OSHA PDFs from the web to data/pdfs/."""
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    for url, filename, title in OSHA_PDFS:
        dest = PDF_DIR / filename

        if dest.exists():
            print(f"   ✅ Already downloaded: {filename}")
            continue

        print(f"   ⬇️  Downloading: {filename}")
        try:
            response = httpx.get(url, follow_redirects=True, timeout=30)
            response.raise_for_status()
            dest.write_bytes(response.content)
            print(f"   ✅ Saved to {dest}")
        except Exception as e:
            print(f"   ❌ Failed to download {filename}: {e}")


def ingest_html_pages(db):
    """Fetches and ingests HTML pages into the database."""
    from app.ingestion.parser import parse_html_url
    from app.ingestion.chunker import chunk_pages
    from app.ingestion.embedder import generate_embeddings_batch
    from app.models import Document, Chunk

    if not OSHA_HTML_PAGES:
        return 0

    total = 0
    print(f"\n🌐 Processing {len(OSHA_HTML_PAGES)} HTML page(s)...")

    for url, title in OSHA_HTML_PAGES:
        print(f"\n🌐 Processing: {title}")

        # Skip if already ingested
        existing = db.query(Document).filter_by(title=title).first()
        if existing:
            print(f"   ⚠️  Already ingested — skipping")
            continue

        # Same pipeline as PDFs: parse → chunk → embed → store
        pages = parse_html_url(url)
        if not pages:
            continue

        chunks = chunk_pages(pages)
        print(f"   ✂️  Split into {len(chunks)} chunks")

        chunks_with_embeddings = generate_embeddings_batch(chunks)

        doc = Document(
            filename=title.lower().replace(" ", "_") + ".html",
            title=title,
            source_url=url
        )
        db.add(doc)
        db.flush()

        for chunk_data in chunks_with_embeddings:
            chunk = Chunk(
                document_id=doc.id,
                content=chunk_data["content"],
                chunk_index=chunk_data["chunk_index"],
                page_number=chunk_data["page_number"],
                embedding=chunk_data["embedding"]
            )
            db.add(chunk)

        db.commit()
        print(f"   💾 Stored {len(chunks_with_embeddings)} chunks in database")
        total += len(chunks_with_embeddings)

    return total

def main():
    print("=" * 50)
    print("SafetyIQ — Ingestion Pipeline")
    print("=" * 50)

    # Step 1: Make sure DB tables exist
    print("\n🔧 Initializing database...")
    init_db()

    # Step 2: Download PDFs if configured
    if DOWNLOAD_PDFS:
        print("\n⬇️  Downloading OSHA PDFs...")
        download_pdfs()

    # Step 3: Find all PDFs in data/pdfs/
    pdf_files = list(PDF_DIR.glob("*.pdf"))

    if not pdf_files:
        print(f"\n❌ No PDF files found in {PDF_DIR}")
        print("   Either set DOWNLOAD_PDFS = True or manually add PDFs to data/pdfs/")
        return

    print(f"\n📂 Found {len(pdf_files)} PDF(s) to process")

    # Step 4: Ingest each PDF
    # Import here to avoid circular imports
    from app.ingestion.pipeline import ingest_pdf

    db = SessionLocal()
    total_chunks = 0

    try:
        for pdf_path in pdf_files:
            # Look up the title from our list (if it's one of our known PDFs)
            title = None
            source_url = None
            for url, filename, pdf_title in OSHA_PDFS:
                if pdf_path.name == filename:
                    title = pdf_title
                    source_url = url
                    break

            doc = ingest_pdf(
                pdf_path=str(pdf_path),
                db=db,
                title=title,
                source_url=source_url
            )

            if doc:
                chunk_count = db.query(__import__('app.models', fromlist=['Chunk']).Chunk).filter_by(document_id=doc.id).count()
                total_chunks += chunk_count

        # ── Ingest HTML pages ────────────────────────────
        total_chunks += ingest_html_pages(db)

    finally:
        db.close()

    print("\n" + "=" * 50)
    print(f"✅ Ingestion complete!")
    print(f"   Documents processed: {len(pdf_files)}")
    print(f"   HTML pages processed: {len(OSHA_HTML_PAGES)}")
    print(f"   Total chunks stored: {total_chunks}")
    print("\nNext step: Start the API server with:")
    print("   uvicorn app.main:app --reload")
    print("Then visit http://localhost:8000/docs")
    print("=" * 50)


if __name__ == "__main__":
    main()
