"""
Tests for Aquabilidad fishing workflows.
"""

import pytest
from aquabilidad.fishing_workflows import (
    create_fishing_permit_workflow,
    create_catch_reporting_workflow, 
    create_traceability_workflow
)


def test_fishing_permit_workflow_creation():
    """Test that fishing permit workflow can be created"""
    workflow = create_fishing_permit_workflow()
    
    assert workflow.workflow_id == "fishing_permit_v1"
    assert workflow.name == "Commercial Fishing Permit Application"
    assert len(workflow.steps) > 0
    assert workflow.start_step is not None


def test_catch_reporting_workflow_creation():
    """Test that catch reporting workflow can be created"""
    workflow = create_catch_reporting_workflow()
    
    assert workflow.workflow_id == "catch_reporting_v1"
    assert workflow.name == "Daily Catch Reporting"
    assert len(workflow.steps) > 0
    assert workflow.start_step is not None


def test_traceability_workflow_creation():
    """Test that traceability workflow can be created"""
    workflow = create_traceability_workflow()
    
    assert workflow.workflow_id == "traceability_v1"
    assert workflow.name == "Supply Chain Traceability"
    assert len(workflow.steps) > 0
    assert workflow.start_step is not None


def test_all_workflows_validate():
    """Test that all workflows pass validation"""
    workflows = [
        create_fishing_permit_workflow(),
        create_catch_reporting_workflow(),
        create_traceability_workflow()
    ]
    
    for workflow in workflows:
        try:
            workflow.validate()
        except Exception as e:
            pytest.fail(f"Workflow {workflow.workflow_id} failed validation: {e}")


def test_workflow_step_connections():
    """Test that workflow steps are properly connected"""
    workflow = create_fishing_permit_workflow()
    
    # Should have start step
    assert workflow.start_step is not None
    
    # Should have terminal steps
    terminal_steps = [step for step in workflow.steps.values() 
                     if step.__class__.__name__ == "TerminalStep"]
    assert len(terminal_steps) > 0
    
    # Should have conditional routing
    conditional_steps = [step for step in workflow.steps.values()
                        if step.__class__.__name__ == "ConditionalStep"]  
    assert len(conditional_steps) > 0