import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock

from app.modules.workflow.service import workflow_service
from app.modules.workflow.repository import WorkflowRepository
from app.modules.obligations.repository import ObligationRepository
from app.modules.tasks.repository import TaskRepository
from app.models.workflow_document import WorkflowDocument
from app.models.obligation import Obligation
from app.models.task import Task

@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    return session

@pytest.mark.asyncio
async def test_workflow_repository_get_or_create(mock_db_session):
    repo = WorkflowRepository()
    doc_id = uuid.uuid4()
    
    # Test creation
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    
    workflow = await repo.get_or_create_workflow(mock_db_session, doc_id)
    assert workflow.document_id == doc_id
    mock_db_session.add.assert_called_once()
    
    # Test retrieval
    existing_wf = WorkflowDocument(id=uuid.uuid4(), document_id=doc_id)
    mock_result.scalar_one_or_none.return_value = existing_wf
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    
    workflow2 = await repo.get_or_create_workflow(mock_db_session, doc_id)
    assert workflow2.id == existing_wf.id

@pytest.mark.asyncio
async def test_obligation_repository_upsert(mock_db_session):
    repo = ObligationRepository()
    workflow_id = uuid.uuid4()
    
    # Existing obligations
    existing_ob = Obligation(id=uuid.uuid4(), workflow_id=workflow_id)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [existing_ob]
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    
    new_data = [{"title": "Test ob", "category": "Security"}]
    
    obs = await repo.upsert_obligations(mock_db_session, workflow_id, new_data)
    
    # Ensure existing is deleted
    mock_db_session.delete.assert_called_once_with(existing_ob)
    
    # Ensure new is added
    assert len(obs) == 1
    assert obs[0].title == "Test ob"
    assert obs[0].workflow_id == workflow_id
    mock_db_session.add.assert_called_once()

@pytest.mark.asyncio
async def test_task_repository_upsert(mock_db_session):
    repo = TaskRepository()
    workflow_id = uuid.uuid4()
    
    # Existing tasks
    existing_task = Task(id=uuid.uuid4(), workflow_id=workflow_id)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [existing_task]
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    
    new_data = [{"title": "Test task", "status": "Pending"}]
    
    tasks = await repo.upsert_tasks(mock_db_session, workflow_id, new_data)
    
    # Ensure existing is deleted
    mock_db_session.delete.assert_called_once_with(existing_task)
    
    # Ensure new is added
    assert len(tasks) == 1
    assert tasks[0].title == "Test task"
    assert tasks[0].workflow_id == workflow_id
    mock_db_session.add.assert_called_once()

@pytest.mark.asyncio
@patch("app.modules.workflow.service.workflow_repository", new_callable=AsyncMock)
@patch("app.modules.workflow.service.obligation_repository", new_callable=AsyncMock)
@patch("app.modules.workflow.service.task_repository", new_callable=AsyncMock)
async def test_workflow_service_save_results(mock_task_repo, mock_ob_repo, mock_wf_repo, mock_db_session):
    doc_id = str(uuid.uuid4())
    wf_id = uuid.uuid4()
    
    mock_wf = MagicMock()
    mock_wf.id = wf_id
    mock_wf.swd = {}
    mock_wf_repo.get_or_create_workflow.return_value = mock_wf
    mock_wf_repo.get_workflow.return_value = mock_wf
    
    results = {
        "obligations": [{"title": "O1"}],
        "tasks": [{"title": "T1"}],
        "applicability": {"score": 1.0},
        "ambiguity": {"has_ambiguity": False}
    }
    
    await workflow_service.save_pipeline_results(mock_db_session, doc_id, results)
    
    # Verifies that it coordinates properly
    mock_wf_repo.update_swd.assert_called_once()
    mock_ob_repo.upsert_obligations.assert_called_once_with(mock_db_session, wf_id, results["obligations"])
    mock_task_repo.upsert_tasks.assert_called_once_with(mock_db_session, wf_id, results["tasks"])

