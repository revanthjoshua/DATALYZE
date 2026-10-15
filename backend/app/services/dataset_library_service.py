"""Immutable, tenant-scoped datasets retained independently of the active source."""
import hashlib
import io
from datetime import timezone

import pandas as pd
from fastapi import HTTPException
from sqlalchemy import func

from app.models.analysis_record import AnalysisRecord
from app.models.company import Company
from app.models.uploaded_dataset import UploadedDataset
from app.services.analyst_service import AnalystService, records
from app.services.data_processing_service import DataProcessingService

MAX_SNAPSHOT_BYTES = 20 * 1024 * 1024
MAX_LIBRARY_BYTES = 200 * 1024 * 1024
MAX_LIBRARY_DATASETS = 100


class DatasetLibraryService:
    def __init__(self, db, user):
        self.db, self.user, self.tenant = db, user, user.company_id

    def lock(self):
        if not self.db.query(Company).filter_by(id=self.tenant).with_for_update().first():
            raise HTTPException(404, 'Workspace not found.')

    def current(self):
        return self.db.query(UploadedDataset).filter_by(company_id=self.tenant).populate_existing().order_by(UploadedDataset.created_at.desc()).first()

    @staticmethod
    def revision(dataset):
        return f'{dataset.id}:{dataset.file_hash}' if dataset else ''

    def source(self, expected):
        from app.api.v1.data_routes import _ensure_dataset_loaded
        dataset = self.current()
        if self.revision(dataset) != expected:
            raise HTTPException(409, 'Active dataset changed. Refresh before continuing.')
        if not dataset:
            raise HTTPException(404, 'Upload an active dataset first.')
        frame = _ensure_dataset_loaded(self.tenant, self.db)
        if frame is None or frame.empty:
            raise HTTPException(409, 'The active source is unavailable.')
        return dataset, frame.copy()

    def get(self, dataset_id):
        row = self.db.query(AnalysisRecord).filter_by(company_id=self.tenant, id=dataset_id, kind='saved_dataset').first()
        if not row:
            raise HTTPException(404, 'Saved dataset not found.')
        return row

    def states(self):
        events = self.db.query(AnalysisRecord).filter_by(company_id=self.tenant, kind='dataset_state').order_by(AnalysisRecord.id).all()
        return {event.content['dataset_id']: {'archived': event.content['archived'], 'version': event.id} for event in events}

    def state(self, dataset_id):
        event = self.db.query(AnalysisRecord).filter(
            AnalysisRecord.company_id == self.tenant, AnalysisRecord.kind == 'dataset_state',
            AnalysisRecord.content['dataset_id'].as_integer() == dataset_id,
        ).order_by(AnalysisRecord.id.desc()).first()
        return {'archived': event.content['archived'], 'version': event.id} if event else {'archived': False, 'version': 0}

    def present(self, row):
        return {'id': row.id, 'name': row.title, 'created_at': row.created_at.replace(tzinfo=timezone.utc).isoformat(),
                'source_revision': row.dataset_revision, **row.content['metadata'], **self.state(row.id)}

    def list(self, include_archived=False):
        # Project metadata so list requests do not read every source snapshot.
        rows = self.db.query(AnalysisRecord.id, AnalysisRecord.title, AnalysisRecord.created_at,
                             AnalysisRecord.dataset_revision, AnalysisRecord.content['metadata'].label('metadata')).filter_by(
                                 company_id=self.tenant, kind='saved_dataset').order_by(AnalysisRecord.id.desc()).all()
        states = self.states()
        output = []
        for row in rows:
            state = states.get(row.id, {'archived': False, 'version': 0})
            if include_archived or not state['archived']:
                output.append({'id': row.id, 'name': row.title, 'created_at': row.created_at.replace(tzinfo=timezone.utc).isoformat(),
                               'source_revision': row.dataset_revision, **row.metadata, **state})
        return output

    def save(self, frame, name, description, filename, revision=None):
        name, description = name.strip(), description.strip()
        if not name or len(name) > 200 or len(description) > 2000:
            raise HTTPException(422, 'Provide a dataset name up to 200 characters and description up to 2,000 characters.')
        if frame.empty or len(frame) > 100000 or len(frame.columns) > 500:
            raise HTTPException(422, 'Saved datasets support 1–100,000 rows and up to 500 columns.')
        if not frame.columns.is_unique:
            raise HTTPException(422, 'Dataset column names must be unique.')
        snapshot = frame.to_json(orient='table', index=False, date_format='iso', double_precision=15)
        size = len(snapshot.encode('utf-8'))
        if size > MAX_SNAPSHOT_BYTES:
            raise HTTPException(413, 'A saved dataset must be at most 20 MB.')
        self.lock()
        count, total = self.db.query(func.count(AnalysisRecord.id), func.sum(
            AnalysisRecord.content['metadata']['size_bytes'].as_integer())).filter_by(company_id=self.tenant, kind='saved_dataset').one()
        if count >= MAX_LIBRARY_DATASETS or (total or 0) + size > MAX_LIBRARY_BYTES:
            raise HTTPException(413, 'The saved dataset library allows 100 snapshots and 200 MB per company, including archived snapshots.')
        row = AnalysisRecord(company_id=self.tenant, user_id=self.user.id, kind='saved_dataset', title=name,
                             dataset_revision=revision, content={'snapshot': snapshot, 'metadata': {
                                 'description': description, 'filename': filename, 'rows': len(frame),
                                 'columns': list(frame.columns), 'size_bytes': size,
                                 'checksum': hashlib.sha256(snapshot.encode('utf-8')).hexdigest()}})
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return self.present(row)

    def save_current(self, name, description, revision):
        self.lock()
        dataset, frame = self.source(revision)
        frame = AnalystService(frame).frame
        return self.save(frame, name, description, dataset.filename, revision)

    def frame(self, row):
        snapshot = row.content['snapshot']
        if hashlib.sha256(snapshot.encode('utf-8')).hexdigest() != row.content['metadata']['checksum']:
            raise HTTPException(409, 'The saved snapshot failed its integrity check.')
        try:
            return pd.read_json(io.StringIO(snapshot), orient='table')
        except (ValueError, TypeError, KeyError):
            raise HTTPException(409, 'The saved snapshot cannot be read.')

    def source_frame(self, row):
        frame = self.frame(row)
        # Old active-source snapshots may contain cached analysis helper columns.
        # Raw library uploads have no revision and retain their original columns.
        return AnalystService(frame).frame if row.dataset_revision is not None else frame

    def preview(self, dataset_id):
        row = self.get(dataset_id)
        frame = self.frame(row)
        return {**self.present(row), 'preview': records(frame.head(30)), 'preview_limit': 30}

    def set_state(self, dataset_id, archived, version):
        self.lock()
        row = self.get(dataset_id)
        state = self.state(dataset_id)
        if state['version'] != version:
            raise HTTPException(409, 'Saved dataset status changed. Refresh the library.')
        if state['archived'] != archived:
            self.db.add(AnalysisRecord(company_id=self.tenant, user_id=self.user.id, kind='dataset_state',
                                       title=('Archived: ' if archived else 'Restored: ') + row.title[:180],
                                       content={'dataset_id': dataset_id, 'archived': archived}))
            self.db.commit()
        return self.present(row)

    def usable(self, dataset_id):
        row = self.get(dataset_id)
        if self.state(dataset_id)['archived']:
            raise HTTPException(409, 'Restore this archived dataset before using it.')
        return row

    def activate(self, dataset_id, revision):
        self.lock()
        row = self.usable(dataset_id)
        outcome = DataProcessingService(self.db, self.tenant).process_dataframe(
            self.source_frame(row), row.content['metadata']['filename'], expected_revision=revision)
        if outcome.status not in ('success', 'partial_success'):
            raise HTTPException(422, outcome.message)
        return {'activated': True, 'dataset_id': row.id, 'revision': self.revision(self.current()),
                'rows': outcome.processed_rows, 'message': 'Saved snapshot is now active. The previous active dataset was backed up.'}

    def join(self, dataset_id, revision, left_key, right_key, how, cardinality, apply=False):
        row = self.usable(dataset_id)
        _, left = self.source(revision)
        right = self.source_frame(row)
        try:
            result, audit = AnalystService(left).join(right, left_key=left_key, right_key=right_key, how=how, cardinality=cardinality)
        except (ValueError, TypeError, KeyError) as error:
            raise HTTPException(422, str(error))
        response = {**audit, 'columns': list(result.columns), 'preview': records(result.head(30)), 'applied': False,
                    'lookup_dataset_id': row.id, 'lookup_checksum': row.content['metadata']['checksum']}
        if apply:
            outcome = DataProcessingService(self.db, self.tenant).process_dataframe(result, 'joined_dataset.csv', expected_revision=revision)
            if outcome.status not in ('success', 'partial_success'):
                raise HTTPException(422, outcome.message)
            self.db.add(AnalysisRecord(company_id=self.tenant, user_id=self.user.id, kind='preparation', title='Saved dataset join applied',
                dataset_revision=self.revision(self.current()), content={'lookup_dataset_id': row.id, 'lookup_name': row.title,
                'lookup_checksum': row.content['metadata']['checksum'], 'left_key': left_key, 'right_key': right_key,
                'how': how, 'cardinality': cardinality, 'audit': audit}))
            self.db.commit()
            response.update(applied=True, revision=self.revision(self.current()))
        return response
