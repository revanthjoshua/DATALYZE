"""Operator-configured, tenant-scoped read-only source connections."""
import json
import os
import io
import re
from urllib.parse import urlparse
import httpx
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, select

MAX_BYTES = 20 * 1024 * 1024
MAX_ROWS = 100000


def configured_sources(tenant_id):
    try:
        sources = json.loads(os.environ.get('DATALYZE_SOURCES_JSON', '[]'))
        if not isinstance(sources, list):
            raise ValueError()
        result = [s for s in sources if isinstance(s, dict) and tenant_id in s.get('company_ids', []) and s.get('type') in ['api', 'database']]
        identifiers = [s.get('id') for s in result]
        if any(not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', key) for key in identifiers) or len(set(identifiers)) != len(identifiers):
            raise ValueError()
        return result
    except (ValueError, TypeError):
        raise ValueError('Source configuration is invalid. Contact your administrator.')


def fetch_source(source):
    """Only fixed, operator-approved endpoints/tables; no user SQL or user URL."""
    try:
        if source['type'] == 'api':
            url = source['url']
            if urlparse(url).scheme != 'https':
                raise ValueError('API sources require HTTPS.')
            headers = source.get('headers', {})
            with httpx.Client(timeout=30, follow_redirects=False) as client:
                with client.stream('GET', url, headers=headers) as response:
                    response.raise_for_status()
                    chunks = bytearray()
                    for chunk in response.iter_bytes():
                        chunks.extend(chunk)
                        if len(chunks) > MAX_BYTES:
                            raise ValueError('Source exceeds the 20 MB limit.')
            if source.get('format', 'json') == 'csv':
                frame = pd.read_csv(io.BytesIO(chunks), dtype=str, keep_default_na=False, na_values=[''])
            else:
                payload = json.loads(chunks)
                if source.get('records_key'):
                    payload = payload[source['records_key']]
                if not isinstance(payload, list) or any(not isinstance(r, dict) for r in payload):
                    raise ValueError('JSON source must contain a list of records.')
                frame = pd.DataFrame(payload)
        else:
            engine = create_engine(source['url'])
            try:
                with engine.connect() as connection:
                    if engine.dialect.name == 'postgresql':
                        connection.exec_driver_sql('SET TRANSACTION READ ONLY')
                        connection.exec_driver_sql('SET LOCAL statement_timeout = 30000')
                    elif engine.dialect.name == 'sqlite':
                        connection.exec_driver_sql('PRAGMA query_only = ON')
                    table = Table(source['table'], MetaData(), schema=source.get('schema'), autoload_with=connection)
                    selected = [table.c[name] for name in source.get('columns', [])] or list(table.c)
                    frame = pd.read_sql(select(*selected).limit(MAX_ROWS+1), connection)
            finally:
                engine.dispose()
        if frame.empty or len(frame) > MAX_ROWS:
            raise ValueError('Source must contain between 1 and 100,000 rows.')
        if len(frame.to_csv(index=False).encode()) > MAX_BYTES:
            raise ValueError('Source exceeds the 20 MB limit.')
        return frame
    except Exception:
        # Driver and HTTP errors can contain credentials, URLs, or response bodies.
        raise ValueError('Source could not be read. Check its configuration, read permissions, format, and 20 MB / 100,000 row limits.') from None
