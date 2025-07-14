"""
Aquabilidad Fishing Industry Workflows

This module contains the complete set of workflows for sustainable fishing management:
1. Fishing Permit Application
2. Catch Reporting  
3. Traceability & Invoice Linking
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta

# Import CivicStream workflow components
# Note: In a real plugin, these would be imported from the installed CivicStream package
try:
    from app.workflows.base import (
        ActionStep, ConditionalStep, ApprovalStep, IntegrationStep, TerminalStep, ValidationResult
    )
    from app.workflows.workflow import Workflow
except ImportError:
    # Fallback for development - import from relative path
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend/app'))
    from workflows.base import (
        ActionStep, ConditionalStep, ApprovalStep, IntegrationStep, TerminalStep, ValidationResult
    )
    from workflows.workflow import Workflow


# =============================================================================
# FISHING PERMIT WORKFLOW
# =============================================================================

def validate_fisher_identity(instance, context) -> Dict[str, Any]:
    """Validate commercial fisher identity and license"""
    fisher_name = instance.data.get("fisher_name", "")
    license_number = instance.data.get("commercial_license", "")
    
    if not fisher_name or not license_number:
        return {"status": "invalid", "reason": "Missing required information"}
    
    # Mock validation - in reality would check maritime authority database
    if license_number.startswith("CF"):
        return {
            "status": "valid",
            "fisher_id": f"FISHER_{license_number}",
            "license_type": "commercial",
            "experience_years": 5
        }
    
    return {"status": "invalid", "reason": "Invalid commercial fishing license"}


def verify_vessel_registration(instance, context) -> Dict[str, Any]:
    """Verify vessel registration and seaworthiness"""
    vessel_name = instance.data.get("vessel_name", "")
    registration_number = instance.data.get("vessel_registration", "")
    vessel_type = instance.data.get("vessel_type", "")
    
    if not all([vessel_name, registration_number, vessel_type]):
        return {"status": "incomplete", "reason": "Missing vessel information"}
    
    # Mock verification
    if registration_number.startswith("VR"):
        return {
            "status": "verified",
            "vessel_id": f"VESSEL_{registration_number}",
            "capacity_tons": 50,
            "last_inspection": datetime.now() - timedelta(days=180),
            "inspection_due": datetime.now() + timedelta(days=185)
        }
    
    return {"status": "unverified", "reason": "Vessel not found in registry"}


def check_safety_equipment(instance, context) -> Dict[str, Any]:
    """Verify required safety equipment is present"""
    equipment_list = instance.data.get("safety_equipment", [])
    required_equipment = [
        "life_jackets", "emergency_beacon", "fire_extinguisher",
        "first_aid_kit", "radio_communication", "gps_system"
    ]
    
    missing_equipment = [item for item in required_equipment if item not in equipment_list]
    
    if not missing_equipment:
        return {"status": "compliant", "safety_score": 100, "inspection_passed": True}
    
    return {
        "status": "non_compliant",
        "missing_equipment": missing_equipment,
        "safety_score": len(equipment_list) / len(required_equipment) * 100
    }


def calculate_quota_allocation(instance, context) -> Dict[str, Any]:
    """Calculate fishing quota based on vessel and zone"""
    vessel_capacity = context.get("capacity_tons", 50)
    fishing_zones = instance.data.get("requested_zones", [])
    permit_type = instance.data.get("permit_type", "general")
    
    # Base quota calculation
    base_quota = vessel_capacity * 10  # 10x vessel capacity in tons per year
    
    # Adjust for permit type
    quota_multipliers = {
        "general": 1.0,
        "specialized": 1.5,
        "sustainable": 2.0
    }
    
    final_quota = base_quota * quota_multipliers.get(permit_type, 1.0)
    
    # Zone-specific quotas
    zone_quotas = {}
    for zone in fishing_zones:
        if zone.startswith("PROTECTED"):
            zone_quotas[zone] = final_quota * 0.3
        else:
            zone_quotas[zone] = final_quota * 0.7
    
    return {
        "annual_quota_tons": final_quota,
        "zone_allocations": zone_quotas,
        "species_restrictions": ["No endangered species", "Seasonal restrictions apply"]
    }


def calculate_permit_fee(instance, context) -> Dict[str, Any]:
    """Calculate permit fee based on quota and vessel size"""
    annual_quota = context.get("annual_quota_tons", 500)
    vessel_capacity = context.get("capacity_tons", 50)
    permit_type = instance.data.get("permit_type", "general")
    
    # Base fee calculation
    base_fee = 100
    quota_fee = annual_quota * 2
    vessel_fee = vessel_capacity * 10
    
    type_multipliers = {"general": 1.0, "specialized": 1.2, "sustainable": 0.8}
    
    subtotal = (base_fee + quota_fee + vessel_fee) * type_multipliers.get(permit_type, 1.0)
    tax = subtotal * 0.15
    total_fee = subtotal + tax
    
    return {
        "base_fee": base_fee, "quota_fee": quota_fee, "vessel_fee": vessel_fee,
        "subtotal": subtotal, "tax": tax, "total_fee": total_fee, "currency": "USD"
    }


def generate_permit_data(instance, context) -> Dict[str, Any]:
    """Generate data for permit document"""
    return {
        "permit_number": f"FP{datetime.now().year}{instance.id[:8].upper()}",
        "fisher_name": instance.data.get("fisher_name"),
        "vessel_name": instance.data.get("vessel_name"),
        "permit_type": instance.data.get("permit_type"),
        "issue_date": datetime.now().isoformat(),
        "expiry_date": (datetime.now() + timedelta(days=365)).isoformat(),
        "annual_quota_tons": context.get("annual_quota_tons"),
        "zone_allocations": context.get("zone_allocations"),
        "terms_conditions": [
            "Must report catch within 24 hours of landing",
            "Subject to random inspections",
            "Must maintain electronic logbook",
            "GPS tracking required at all times"
        ]
    }


# Condition functions for permit workflow
def identity_valid(instance, context) -> bool:
    return context.get("status") == "valid"

def vessel_verified(instance, context) -> bool:
    return context.get("status") == "verified"

def safety_compliant(instance, context) -> bool:
    return context.get("status") == "compliant"

def payment_completed(instance, context) -> bool:
    return context.get("payment_status") == "completed"

def final_approved(instance, context) -> bool:
    return context.get("approved", False)


def create_fishing_permit_workflow() -> Workflow:
    """Create the fishing permit application workflow"""
    workflow = Workflow(
        workflow_id="fishing_permit_v1",
        name="Commercial Fishing Permit Application",
        description="Apply for commercial fishing permit with vessel verification and quota allocation"
    )
    
    # Define steps
    # CITIZEN DATA COLLECTION: Initial application data
    step_collect_initial_data = ActionStep(
        step_id="collect_initial_application_data",
        name="Collect Initial Application Data", 
        description="Collect basic fisher and vessel information from citizen",
        action=lambda instance, context: {"status": "awaiting_input"},
        requires_citizen_input=True,
        input_form={
            "title": "Commercial Fishing Permit Application",
            "description": "Please provide your basic information to start your fishing permit application.",
            "fields": [
                {
                    "id": "fisher_name",
                    "name": "fisher_name",
                    "label": "Full Name",
                    "type": "text",
                    "required": True,
                    "placeholder": "Enter your full legal name",
                    "validation": {
                        "minLength": 2,
                        "maxLength": 100
                    },
                    "helpText": "Your full legal name as it appears on your ID"
                },
                {
                    "id": "email",
                    "name": "email", 
                    "label": "Email Address",
                    "type": "email",
                    "required": True,
                    "placeholder": "your.email@example.com",
                    "helpText": "We'll use this to send you updates about your application"
                },
                {
                    "id": "phone",
                    "name": "phone",
                    "label": "Phone Number",
                    "type": "phone",
                    "required": True,
                    "placeholder": "+1 (555) 123-4567",
                    "validation": {
                        "pattern": "^[+]?[1-9]\\d{1,14}$"
                    },
                    "helpText": "Include country code for international numbers"
                },
                {
                    "id": "commercial_license",
                    "name": "commercial_license",
                    "label": "Commercial Fishing License Number",
                    "type": "text",
                    "required": True,
                    "placeholder": "CF123456789",
                    "validation": {
                        "pattern": "^CF[0-9]{8,12}$",
                        "minLength": 10,
                        "maxLength": 14
                    },
                    "helpText": "Your commercial fishing license number (starts with CF)"
                },
                {
                    "id": "license_document",
                    "name": "license_document",
                    "label": "Commercial License Document",
                    "type": "file",
                    "required": True,
                    "helpText": "Upload a clear photo or scan of your commercial fishing license"
                }
            ]
        }
    )

    step_validate_identity = ActionStep(
        step_id="validate_identity",
        name="Validate Fisher Identity",
        description="Verify commercial fisher identity and license",
        action=validate_fisher_identity,
        required_inputs=["fisher_name", "commercial_license", "email", "phone"]
    )
    
    step_identity_check = ConditionalStep(
        step_id="identity_check",
        name="Identity Verification Check",
        description="Check if identity verification passed"
    )
    
    # CITIZEN DATA COLLECTION: Vessel information
    step_collect_vessel_data = ActionStep(
        step_id="collect_vessel_information",
        name="Collect Vessel Information",
        description="Collect detailed vessel information and documentation",
        action=lambda instance, context: {"status": "awaiting_input"},
        requires_citizen_input=True,
        input_form={
            "title": "Vessel Information",
            "description": "Please provide detailed information about your fishing vessel.",
            "fields": [
                {
                    "id": "vessel_name",
                    "name": "vessel_name",
                    "label": "Vessel Name",
                    "type": "text",
                    "required": True,
                    "placeholder": "Enter your vessel's name",
                    "validation": {
                        "minLength": 2,
                        "maxLength": 50
                    },
                    "helpText": "The official name of your fishing vessel"
                },
                {
                    "id": "vessel_registration",
                    "name": "vessel_registration",
                    "label": "Vessel Registration Number",
                    "type": "text",
                    "required": True,
                    "placeholder": "VR123456789",
                    "validation": {
                        "pattern": "^VR[0-9]{8,12}$",
                        "minLength": 10,
                        "maxLength": 14
                    },
                    "helpText": "Your vessel registration number (starts with VR)"
                },
                {
                    "id": "vessel_type",
                    "name": "vessel_type",
                    "label": "Vessel Type",
                    "type": "select",
                    "required": True,
                    "options": [
                        "Fishing Trawler",
                        "Longline Vessel", 
                        "Seine Net Boat",
                        "Crab Boat",
                        "Lobster Boat",
                        "Multi-purpose Fishing Vessel",
                        "Other"
                    ],
                    "helpText": "Select the type of fishing vessel you operate"
                },
                {
                    "id": "vessel_length",
                    "name": "vessel_length",
                    "label": "Vessel Length (meters)",
                    "type": "number",
                    "required": True,
                    "validation": {
                        "min": 3,
                        "max": 200
                    },
                    "helpText": "Length of your vessel in meters"
                },
                {
                    "id": "vessel_registration_document",
                    "name": "vessel_registration_document",
                    "label": "Vessel Registration Certificate",
                    "type": "file",
                    "required": True,
                    "helpText": "Upload your vessel registration certificate"
                },
                {
                    "id": "vessel_inspection_certificate",
                    "name": "vessel_inspection_certificate", 
                    "label": "Latest Safety Inspection Certificate",
                    "type": "file",
                    "required": True,
                    "helpText": "Upload your most recent vessel safety inspection certificate"
                }
            ]
        }
    )

    step_verify_vessel = ActionStep(
        step_id="verify_vessel",
        name="Verify Vessel Registration",
        description="Verify vessel registration and seaworthiness",
        action=verify_vessel_registration,
        required_inputs=["vessel_name", "vessel_registration", "vessel_type"]
    )
    
    step_vessel_check = ConditionalStep(
        step_id="vessel_check",
        name="Vessel Verification Check",
        description="Check if vessel verification passed"
    )
    
    # CITIZEN DATA COLLECTION: Safety equipment and fishing zones
    step_collect_safety_and_zones = ActionStep(
        step_id="collect_safety_equipment_and_zones",
        name="Safety Equipment & Fishing Zones",
        description="Collect safety equipment inventory and requested fishing zones",
        action=lambda instance, context: {"status": "awaiting_input"},
        requires_citizen_input=True,
        input_form={
            "title": "Safety Equipment & Fishing Zone Selection",
            "description": "Please confirm your safety equipment and select your desired fishing zones.",
            "fields": [
                {
                    "id": "safety_equipment",
                    "name": "safety_equipment",
                    "label": "Available Safety Equipment",
                    "type": "select",
                    "required": True,
                    "options": [
                        "life_jackets",
                        "emergency_beacon", 
                        "fire_extinguisher",
                        "first_aid_kit",
                        "radio_communication",
                        "gps_system",
                        "life_rafts",
                        "flares",
                        "emergency_food_water"
                    ],
                    "helpText": "Select all safety equipment available on your vessel"
                },
                {
                    "id": "safety_equipment_photos",
                    "name": "safety_equipment_photos",
                    "label": "Safety Equipment Photos",
                    "type": "file",
                    "required": True,
                    "helpText": "Upload photos showing your vessel's safety equipment"
                },
                {
                    "id": "requested_zones",
                    "name": "requested_zones",
                    "label": "Requested Fishing Zones",
                    "type": "select",
                    "required": True,
                    "options": [
                        "ZONE_A - Coastal Waters (0-12 nautical miles)",
                        "ZONE_B - Continental Shelf (12-50 nautical miles)",
                        "ZONE_C - Deep Sea (50+ nautical miles)",
                        "SUSTAINABLE_1 - Protected Area 1 (Special Permit Required)",
                        "SUSTAINABLE_2 - Protected Area 2 (Seasonal Access)",
                        "INTERNATIONAL_1 - International Waters Zone 1"
                    ],
                    "helpText": "Select the fishing zones you want access to"
                },
                {
                    "id": "permit_type",
                    "name": "permit_type",
                    "label": "Permit Type",
                    "type": "select",
                    "required": True,
                    "options": [
                        "general",
                        "specialized", 
                        "sustainable"
                    ],
                    "helpText": "General: Standard fishing permit, Specialized: Specific species/methods, Sustainable: Eco-certified operations"
                },
                {
                    "id": "target_species",
                    "name": "target_species",
                    "label": "Target Fish Species",
                    "type": "textarea",
                    "required": True,
                    "placeholder": "List the main species you plan to catch (e.g., tuna, salmon, cod, etc.)",
                    "validation": {
                        "minLength": 10,
                        "maxLength": 500
                    },
                    "helpText": "Describe the primary fish species you intend to target"
                },
                {
                    "id": "fishing_methods",
                    "name": "fishing_methods",
                    "label": "Fishing Methods",
                    "type": "select",
                    "required": True,
                    "options": [
                        "Trawling",
                        "Longlining",
                        "Seine Netting",
                        "Gillnetting",
                        "Trap/Pot Fishing",
                        "Handline/Rod Fishing",
                        "Multiple Methods"
                    ],
                    "helpText": "Select your primary fishing method"
                }
            ]
        }
    )

    step_safety_inspection = ActionStep(
        step_id="safety_inspection",
        name="Safety Equipment Inspection",
        description="Verify required safety equipment",
        action=check_safety_equipment,
        required_inputs=["safety_equipment"]
    )
    
    step_safety_check = ConditionalStep(
        step_id="safety_check",
        name="Safety Compliance Check",
        description="Check if safety requirements met"
    )
    
    # NEW: Data collection step for citizen input
    step_collect_documents = ActionStep(
        step_id="collect_citizen_documents",
        name="Collect Additional Documents",
        description="Collect additional documentation from citizen",
        action=lambda instance, context: {"status": "awaiting_input"},
        requires_citizen_input=True,
        input_form={
            "title": "Additional Documentation Required",
            "description": "Please provide the following additional documentation to complete your fishing permit application.",
            "fields": [
                {
                    "id": "business_license",
                    "name": "business_license",
                    "label": "Business License",
                    "type": "file",
                    "required": True,
                    "helpText": "Upload your current business license (PDF, JPG, PNG)"
                },
                {
                    "id": "tax_id",
                    "name": "tax_id", 
                    "label": "Tax ID Number",
                    "type": "text",
                    "required": True,
                    "placeholder": "Enter your tax identification number",
                    "validation": {
                        "pattern": "^[0-9]{9,12}$",
                        "minLength": 9,
                        "maxLength": 12
                    },
                    "helpText": "Your 9-12 digit tax identification number"
                },
                {
                    "id": "fishing_experience",
                    "name": "fishing_experience",
                    "label": "Years of Commercial Fishing Experience",
                    "type": "number",
                    "required": True,
                    "validation": {
                        "min": 0,
                        "max": 50
                    },
                    "helpText": "Number of years you have been commercially fishing"
                },
                {
                    "id": "previous_violations",
                    "name": "previous_violations",
                    "label": "Previous Fishing Violations",
                    "type": "select",
                    "required": True,
                    "options": ["None", "Minor violations (1-2)", "Major violations (3+)"],
                    "helpText": "Select your fishing violation history"
                },
                {
                    "id": "insurance_certificate",
                    "name": "insurance_certificate",
                    "label": "Marine Insurance Certificate",
                    "type": "file",
                    "required": True,
                    "helpText": "Upload proof of marine insurance coverage"
                },
                {
                    "id": "additional_comments",
                    "name": "additional_comments",
                    "label": "Additional Comments",
                    "type": "textarea",
                    "required": False,
                    "placeholder": "Any additional information you'd like to provide...",
                    "helpText": "Optional: Provide any additional information about your application"
                }
            ]
        }
    )

    step_calculate_quota = ActionStep(
        step_id="calculate_quota",
        name="Calculate Fishing Quota",
        description="Calculate annual fishing quota allocation",
        action=calculate_quota_allocation,
        required_inputs=["requested_zones", "permit_type"]
    )
    
    step_calculate_fee = ActionStep(
        step_id="calculate_fee",
        name="Calculate Permit Fee",
        description="Calculate permit fee based on quota and vessel",
        action=calculate_permit_fee
    )
    
    step_payment = IntegrationStep(
        step_id="process_payment",
        name="Process Permit Payment",
        description="Process permit fee payment",
        service_name="payment_gateway",
        endpoint="/process",
        method="POST"
    )
    
    step_payment_check = ConditionalStep(
        step_id="payment_check",
        name="Payment Verification",
        description="Verify payment was successful"
    )
    
    step_final_approval = ApprovalStep(
        step_id="final_approval",
        name="Final Permit Approval",
        description="Final approval by permit supervisor",
        approvers=["permit_supervisor"]
    )
    
    step_approval_check = ConditionalStep(
        step_id="approval_check",
        name="Approval Decision",
        description="Check final approval decision"
    )
    
    step_generate_permit_data = ActionStep(
        step_id="generate_permit_data",
        name="Generate Permit Data",
        description="Prepare permit document data",
        action=generate_permit_data
    )
    
    step_blockchain_record = IntegrationStep(
        step_id="blockchain_record",
        name="Record on Blockchain",
        description="Record permit on blockchain for transparency",
        service_name="blockchain_service",
        endpoint="/record",
        method="POST"
    )
    
    # Terminal steps
    terminal_identity_failed = TerminalStep(
        step_id="identity_failed",
        name="Identity Verification Failed",
        description="Commercial fishing license invalid"
    )
    
    terminal_vessel_failed = TerminalStep(
        step_id="vessel_failed",
        name="Vessel Verification Failed",
        description="Vessel not registered or not seaworthy"
    )
    
    terminal_safety_failed = TerminalStep(
        step_id="safety_failed",
        name="Safety Inspection Failed",
        description="Required safety equipment missing"
    )
    
    terminal_payment_failed = TerminalStep(
        step_id="payment_failed",
        name="Payment Failed",
        description="Permit fee payment unsuccessful"
    )
    
    terminal_rejected = TerminalStep(
        step_id="permit_rejected",
        name="Permit Rejected",
        description="Fishing permit application rejected"
    )
    
    terminal_success = TerminalStep(
        step_id="permit_issued",
        name="Permit Issued",
        description="Fishing permit successfully issued"
    )
    
    # Define workflow flow with citizen data collection
    step_collect_initial_data >> step_validate_identity >> step_identity_check
    step_identity_check.when(identity_valid) >> step_collect_vessel_data
    step_identity_check.when(lambda i, c: not identity_valid(i, c)) >> terminal_identity_failed
    
    step_collect_vessel_data >> step_verify_vessel >> step_vessel_check
    step_vessel_check.when(vessel_verified) >> step_collect_safety_and_zones
    step_vessel_check.when(lambda i, c: not vessel_verified(i, c)) >> terminal_vessel_failed
    
    step_collect_safety_and_zones >> step_safety_inspection >> step_safety_check
    step_safety_check.when(safety_compliant) >> step_collect_documents
    step_safety_check.when(lambda i, c: not safety_compliant(i, c)) >> terminal_safety_failed
    
    step_collect_documents >> step_calculate_quota
    
    step_calculate_quota >> step_calculate_fee >> step_payment >> step_payment_check
    step_payment_check.when(payment_completed) >> step_final_approval
    step_payment_check.when(lambda i, c: not payment_completed(i, c)) >> terminal_payment_failed
    
    step_final_approval >> step_approval_check
    step_approval_check.when(final_approved) >> step_generate_permit_data
    step_approval_check.when(lambda i, c: not final_approved(i, c)) >> terminal_rejected
    
    step_generate_permit_data >> step_blockchain_record >> terminal_success
    
    # Add all steps to workflow
    for step in [step_collect_initial_data, step_validate_identity, step_identity_check, 
                step_collect_vessel_data, step_verify_vessel, step_vessel_check,
                step_collect_safety_and_zones, step_safety_inspection, step_safety_check,
                step_collect_documents, step_calculate_quota, step_calculate_fee, step_payment, 
                step_payment_check, step_final_approval, step_approval_check,
                step_generate_permit_data, step_blockchain_record,
                terminal_identity_failed, terminal_vessel_failed, terminal_safety_failed,
                terminal_payment_failed, terminal_rejected, terminal_success]:
        workflow.add_step(step)
    
    # Set start step to begin with citizen data collection
    workflow.set_start(step_collect_initial_data)
    
    # Build and validate
    workflow.build_graph()
    workflow.validate()
    
    return workflow


# =============================================================================
# CATCH REPORTING WORKFLOW
# =============================================================================

def validate_catch_data(instance, context) -> Dict[str, Any]:
    """Validate daily catch report data"""
    required_fields = ["vessel_id", "catch_date", "fishing_zone", "species_caught"]
    missing_fields = [field for field in required_fields if not instance.data.get(field)]
    
    if missing_fields:
        return {"status": "invalid", "missing_fields": missing_fields}
    
    # Validate species data
    species_list = instance.data.get("species_caught", [])
    total_weight = sum(species.get("weight_kg", 0) for species in species_list)
    
    return {
        "status": "valid",
        "total_weight_kg": total_weight,
        "species_count": len(species_list),
        "validated_at": datetime.now().isoformat()
    }


def check_quota_compliance(instance, context) -> Dict[str, Any]:
    """Check if catch is within allocated quotas"""
    vessel_id = instance.data.get("vessel_id")
    total_weight = context.get("total_weight_kg", 0)
    
    # Mock quota check - would query permit database
    annual_quota = 1000  # tons
    used_quota = 450    # tons already caught this year
    remaining_quota = annual_quota - used_quota
    
    if total_weight > remaining_quota * 1000:  # Convert to kg
        return {
            "status": "quota_exceeded",
            "annual_quota_tons": annual_quota,
            "used_quota_tons": used_quota,
            "remaining_quota_kg": remaining_quota * 1000,
            "catch_weight_kg": total_weight
        }
    
    return {
        "status": "compliant",
        "annual_quota_tons": annual_quota,
        "used_quota_tons": used_quota + (total_weight / 1000),
        "remaining_quota_kg": (remaining_quota * 1000) - total_weight
    }


def verify_fishing_zone(instance, context) -> Dict[str, Any]:
    """Verify fishing was done in permitted zones"""
    fishing_zone = instance.data.get("fishing_zone")
    gps_coordinates = instance.data.get("gps_coordinates", {})
    
    # Mock zone verification
    permitted_zones = ["ZONE_A", "ZONE_B", "SUSTAINABLE_1"]
    
    if fishing_zone not in permitted_zones:
        return {
            "status": "unauthorized_zone",
            "fishing_zone": fishing_zone,
            "permitted_zones": permitted_zones
        }
    
    return {
        "status": "authorized",
        "fishing_zone": fishing_zone,
        "coordinates_verified": bool(gps_coordinates)
    }


def generate_catch_certificate(instance, context) -> Dict[str, Any]:
    """Generate catch certificate with blockchain hash"""
    catch_id = f"CATCH_{datetime.now().strftime('%Y%m%d')}_{instance.id[:8]}"
    
    return {
        "catch_certificate_id": catch_id,
        "vessel_id": instance.data.get("vessel_id"),
        "catch_date": instance.data.get("catch_date"),
        "total_weight_kg": context.get("total_weight_kg"),
        "fishing_zone": instance.data.get("fishing_zone"),
        "blockchain_hash": f"0x{instance.id}",
        "certificate_url": f"/certificates/{catch_id}"
    }


# Condition functions for catch reporting
def catch_data_valid(instance, context) -> bool:
    return context.get("status") == "valid"

def quota_compliant(instance, context) -> bool:
    return context.get("status") == "compliant"

def zone_authorized(instance, context) -> bool:
    return context.get("status") == "authorized"


def create_catch_reporting_workflow() -> Workflow:
    """Create the daily catch reporting workflow"""
    workflow = Workflow(
        workflow_id="catch_reporting_v1",
        name="Daily Catch Reporting",
        description="Report daily catch with quota tracking and zone verification"
    )
    
    # Define steps
    # CITIZEN DATA COLLECTION: Daily catch reporting
    step_collect_catch_data = ActionStep(
        step_id="collect_daily_catch_data",
        name="Daily Catch Report Submission",
        description="Collect daily catch report from fishing vessel operator",
        action=lambda instance, context: {"status": "awaiting_input"},
        requires_citizen_input=True,
        input_form={
            "title": "Daily Catch Report",
            "description": "Please submit your daily catch report within 24 hours of landing.",
            "fields": [
                {
                    "id": "vessel_id",
                    "name": "vessel_id",
                    "label": "Vessel ID",
                    "type": "text",
                    "required": True,
                    "placeholder": "Enter your vessel registration ID",
                    "validation": {
                        "pattern": "^VR[0-9]{8,12}$",
                        "minLength": 10,
                        "maxLength": 14
                    },
                    "helpText": "Your vessel registration ID (starts with VR)"
                },
                {
                    "id": "catch_date",
                    "name": "catch_date",
                    "label": "Catch Date",
                    "type": "date",
                    "required": True,
                    "helpText": "Date when the fish were caught"
                },
                {
                    "id": "fishing_zone",
                    "name": "fishing_zone",
                    "label": "Fishing Zone",
                    "type": "select",
                    "required": True,
                    "options": [
                        "ZONE_A",
                        "ZONE_B",
                        "ZONE_C",
                        "SUSTAINABLE_1",
                        "SUSTAINABLE_2",
                        "INTERNATIONAL_1"
                    ],
                    "helpText": "Zone where fishing activity took place"
                },
                {
                    "id": "species_caught",
                    "name": "species_caught",
                    "label": "Species and Quantities Caught",
                    "type": "textarea",
                    "required": True,
                    "placeholder": "List species and weights, e.g.:\nTuna: 150kg\nSalmon: 75kg\nCod: 200kg",
                    "validation": {
                        "minLength": 10,
                        "maxLength": 1000
                    },
                    "helpText": "List all species caught with their weights in kilograms"
                },
                {
                    "id": "gps_coordinates",
                    "name": "gps_coordinates",
                    "label": "GPS Coordinates",
                    "type": "text",
                    "required": True,
                    "placeholder": "Latitude, Longitude (e.g., 40.7128, -74.0060)",
                    "validation": {
                        "pattern": "^-?\\d{1,3}\\.\\d+,\\s*-?\\d{1,3}\\.\\d+$"
                    },
                    "helpText": "GPS coordinates where fishing took place"
                },
                {
                    "id": "catch_photos",
                    "name": "catch_photos",
                    "label": "Catch Documentation Photos",
                    "type": "file",
                    "required": True,
                    "helpText": "Upload photos of your catch for verification"
                },
                {
                    "id": "fishing_gear_used",
                    "name": "fishing_gear_used",
                    "label": "Fishing Gear Used",
                    "type": "select",
                    "required": True,
                    "options": [
                        "Trawl Net",
                        "Longline",
                        "Seine Net",
                        "Gillnet",
                        "Fishing Rod",
                        "Trap/Pot",
                        "Multiple Gear Types"
                    ],
                    "helpText": "Primary fishing gear used for this catch"
                },
                {
                    "id": "weather_conditions",
                    "name": "weather_conditions",
                    "label": "Weather Conditions",
                    "type": "select",
                    "required": False,
                    "options": [
                        "Clear/Calm",
                        "Partly Cloudy",
                        "Overcast",
                        "Light Rain",
                        "Heavy Rain",
                        "Windy",
                        "Storm Conditions"
                    ],
                    "helpText": "Weather conditions during fishing (optional)"
                }
            ]
        }
    )

    step_validate_catch = ActionStep(
        step_id="validate_catch_data",
        name="Validate Catch Data",
        description="Validate catch report completeness and format",
        action=validate_catch_data,
        required_inputs=["vessel_id", "catch_date", "fishing_zone", "species_caught"]
    )
    
    step_data_check = ConditionalStep(
        step_id="data_validation_check",
        name="Data Validation Check",
        description="Check if catch data is valid"
    )
    
    step_verify_zone = ActionStep(
        step_id="verify_zone",
        name="Verify Fishing Zone",
        description="Verify fishing was done in permitted zones",
        action=verify_fishing_zone
    )
    
    step_zone_check = ConditionalStep(
        step_id="zone_check",
        name="Zone Authorization Check",
        description="Check if fishing zone is authorized"
    )
    
    step_check_quota = ActionStep(
        step_id="check_quota",
        name="Check Quota Compliance",
        description="Verify catch is within quota limits",
        action=check_quota_compliance
    )
    
    step_quota_check = ConditionalStep(
        step_id="quota_compliance_check",
        name="Quota Compliance Check",
        description="Check if catch complies with quotas"
    )
    
    step_generate_certificate = ActionStep(
        step_id="generate_certificate",
        name="Generate Catch Certificate",
        description="Create catch certificate with blockchain record",
        action=generate_catch_certificate
    )
    
    step_blockchain_record = IntegrationStep(
        step_id="record_blockchain",
        name="Record on Blockchain",
        description="Record catch data on blockchain",
        service_name="blockchain_service",
        endpoint="/record_catch",
        method="POST"
    )
    
    # Terminal steps
    terminal_invalid_data = TerminalStep(
        step_id="invalid_data",
        name="Invalid Catch Data",
        description="Catch report data is incomplete or invalid"
    )
    
    terminal_unauthorized_zone = TerminalStep(
        step_id="unauthorized_zone",
        name="Unauthorized Fishing Zone", 
        description="Fishing conducted in unauthorized zone"
    )
    
    terminal_quota_exceeded = TerminalStep(
        step_id="quota_exceeded",
        name="Quota Exceeded",
        description="Catch exceeds allocated quota limits"
    )
    
    terminal_success = TerminalStep(
        step_id="catch_reported",
        name="Catch Successfully Reported",
        description="Catch report submitted and verified"
    )
    
    # Define workflow flow with citizen data collection
    step_collect_catch_data >> step_validate_catch >> step_data_check
    step_data_check.when(catch_data_valid) >> step_verify_zone
    step_data_check.when(lambda i, c: not catch_data_valid(i, c)) >> terminal_invalid_data
    
    step_verify_zone >> step_zone_check
    step_zone_check.when(zone_authorized) >> step_check_quota
    step_zone_check.when(lambda i, c: not zone_authorized(i, c)) >> terminal_unauthorized_zone
    
    step_check_quota >> step_quota_check
    step_quota_check.when(quota_compliant) >> step_generate_certificate
    step_quota_check.when(lambda i, c: not quota_compliant(i, c)) >> terminal_quota_exceeded
    
    step_generate_certificate >> step_blockchain_record >> terminal_success
    
    # Add all steps to workflow
    for step in [step_collect_catch_data, step_validate_catch, step_data_check, step_verify_zone, step_zone_check,
                step_check_quota, step_quota_check, step_generate_certificate, 
                step_blockchain_record, terminal_invalid_data, terminal_unauthorized_zone,
                terminal_quota_exceeded, terminal_success]:
        workflow.add_step(step)
    
    # Set start step to begin with citizen data collection
    workflow.set_start(step_collect_catch_data)
    
    # Build and validate
    workflow.build_graph()
    workflow.validate()
    
    return workflow


# =============================================================================
# TRACEABILITY WORKFLOW
# =============================================================================

def link_catch_to_sale(instance, context) -> Dict[str, Any]:
    """Link catch certificate to sales transaction"""
    catch_certificate_id = instance.data.get("catch_certificate_id")
    invoice_number = instance.data.get("invoice_number")
    buyer_info = instance.data.get("buyer_info", {})
    
    if not all([catch_certificate_id, invoice_number, buyer_info]):
        return {"status": "incomplete", "reason": "Missing required information"}
    
    return {
        "status": "linked",
        "traceability_id": f"TRACE_{invoice_number}_{catch_certificate_id[:8]}",
        "catch_certificate_id": catch_certificate_id,
        "invoice_number": invoice_number,
        "buyer_name": buyer_info.get("name"),
        "sale_date": datetime.now().isoformat()
    }


def generate_qr_code(instance, context) -> Dict[str, Any]:
    """Generate QR code for consumer traceability"""
    traceability_id = context.get("traceability_id")
    
    # Mock QR code generation
    qr_data = {
        "traceability_id": traceability_id,
        "catch_date": instance.data.get("catch_date"),
        "fishing_vessel": instance.data.get("vessel_name"),
        "fishing_zone": instance.data.get("fishing_zone"),
        "species": instance.data.get("species"),
        "verification_url": f"/verify/{traceability_id}"
    }
    
    return {
        "qr_code_data": qr_data,
        "qr_code_url": f"/qr/{traceability_id}.png",
        "verification_url": qr_data["verification_url"]
    }


def create_consumer_certificate(instance, context) -> Dict[str, Any]:
    """Create certificate for final consumer"""
    return {
        "consumer_certificate_id": context.get("traceability_id"),
        "product_origin": {
            "vessel": instance.data.get("vessel_name"),
            "fisher": instance.data.get("fisher_name"),
            "catch_date": instance.data.get("catch_date"),
            "fishing_zone": instance.data.get("fishing_zone")
        },
        "sustainability_score": 95,  # Mock score
        "certifications": ["Sustainable Fishing", "GPS Verified", "Blockchain Recorded"],
        "qr_code_url": context.get("qr_code_url")
    }


def create_traceability_workflow() -> Workflow:
    """Create the traceability and invoice linking workflow"""
    workflow = Workflow(
        workflow_id="traceability_v1", 
        name="Supply Chain Traceability",
        description="Link catch data to sales for consumer transparency"
    )
    
    # Define steps
    step_link_sale = ActionStep(
        step_id="link_catch_sale",
        name="Link Catch to Sale",
        description="Connect catch certificate to sales invoice",
        action=link_catch_to_sale,
        required_inputs=["catch_certificate_id", "invoice_number", "buyer_info"]
    )
    
    step_generate_qr = ActionStep(
        step_id="generate_qr_code",
        name="Generate QR Code",
        description="Create QR code for consumer verification",
        action=generate_qr_code
    )
    
    step_create_certificate = ActionStep(
        step_id="create_consumer_certificate",
        name="Create Consumer Certificate",
        description="Generate final consumer traceability certificate",
        action=create_consumer_certificate
    )
    
    step_blockchain_record = IntegrationStep(
        step_id="record_traceability",
        name="Record Traceability Chain",
        description="Record full traceability chain on blockchain",
        service_name="blockchain_service",
        endpoint="/record_traceability",
        method="POST"
    )
    
    terminal_success = TerminalStep(
        step_id="traceability_complete",
        name="Traceability Chain Complete",
        description="Full traceability from catch to consumer established"
    )
    
    # Define workflow flow
    step_link_sale >> step_generate_qr >> step_create_certificate >> step_blockchain_record >> terminal_success
    
    # Add all steps to workflow
    for step in [step_link_sale, step_generate_qr, step_create_certificate, 
                step_blockchain_record, terminal_success]:
        workflow.add_step(step)
    
    # Set start step
    workflow.set_start(step_link_sale)
    
    # Build and validate
    workflow.build_graph()
    workflow.validate()
    
    return workflow