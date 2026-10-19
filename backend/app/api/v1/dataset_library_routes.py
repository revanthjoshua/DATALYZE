from typing import Literal

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth_middleware import get_current_user, require_analyst_user
from app.models.user import User
from app.services.data_ingestion_service import DataIngestionService
from app.services.dataset_library_service import DatasetLibraryService
from app.services.payload_limits import check_response_size

router = APIRouter(prefix='/datasets', tags=['Saved dataset library'])


class SaveInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default='', max_length=2000)
    revision: str = Field(min_length=1, max_length=100)


class RevisionInput(BaseModel):
    revision: str = Field(max_length=100)


class StateInput(BaseModel):
    archived: bool
    version: int = Field(ge=0)


class JoinInput(RevisionInput):
    left_key: str | list[str]
    right_key: str | list[str]
    how: Literal['left', 'inner', 'outer'] = 'left'
    cardinality: Literal['many_to_one', 'one_to_one', 'one_to_many'] = 'many_to_one'
    apply: bool = False


@router.get('')
def list_datasets(include_archived: bool = False, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return DatasetLibraryService(db, user).list(include_archived)


@router.post('/save', status_code=201)
def save_dataset(payload: SaveInput, user: User = Depends(require_analyst_user), db: Session = Depends(get_db)):
    return DatasetLibraryService(db, user).save_current(payload.name, payload.description, payload.revision)


@router.post('/upload', status_code=201)
async def upload_saved_dataset(file: UploadFile = File(...), name: str = Form(..., min_length=1, max_length=200),
                               description: str = Form('', max_length=2000), user: User = Depends(require_analyst_user), db: Session = Depends(get_db)):
    frame, filename = await DataIngestionService(user.company_id).read_uploaded_file(file)
    return DatasetLibraryService(db, user).save(frame, name, description, filename)


@router.get('/{dataset_id}/preview')
def preview_dataset(dataset_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return DatasetLibraryService(db, user).preview(dataset_id)


@router.get('/{dataset_id}/download')
def download_dataset(dataset_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service = DatasetLibraryService(db, user)
    frame = service.frame(service.get(dataset_id))
    # Escape headers as well as cells; the immutable stored source remains exact.
    def spreadsheet_safe(value):
        return "'" + value if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')) else value
    for column in frame:
        frame[column] = frame[column].map(spreadsheet_safe)
    frame.columns = [spreadsheet_safe(column) for column in frame.columns]
    content = '\ufeff' + frame.to_csv(index=False)
    check_response_size(content, 'This saved dataset download')
    return Response(content, media_type='text/csv',
                    headers={'Content-Disposition': f'attachment; filename="saved-dataset-{dataset_id}.csv"', 'X-Content-Type-Options': 'nosniff'})


@router.post('/{dataset_id}/activate')
def activate_dataset(dataset_id: int, payload: RevisionInput, user: User = Depends(require_analyst_user), db: Session = Depends(get_db)):
    return DatasetLibraryService(db, user).activate(dataset_id, payload.revision)


@router.post('/{dataset_id}/state')
def update_dataset_state(dataset_id: int, payload: StateInput, user: User = Depends(require_analyst_user), db: Session = Depends(get_db)):
    return DatasetLibraryService(db, user).set_state(dataset_id, payload.archived, payload.version)


@router.post('/{dataset_id}/join')
def join_saved_dataset(dataset_id: int, payload: JoinInput, user: User = Depends(require_analyst_user), db: Session = Depends(get_db)):
    return DatasetLibraryService(db, user).join(dataset_id, **payload.model_dump())
