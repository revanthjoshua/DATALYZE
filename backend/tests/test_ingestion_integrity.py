import io
import json
import pandas as pd
import pytest
from app.core.exceptions import DataValidationException
from app.services.data_ingestion_service import DataIngestionService
from app.services.data_type_detector import DataTypeDetector


def test_delimited_import_preserves_codes_na_labels_empty_columns_and_summary_records():
    frame = DataIngestionService(1).parse_raw_content(
        b'customer_id,region,revenue,empty\n001,NA,0,\n002,#North,1,\n003,Total,5,\n', 'sales.csv')
    assert len(frame) == 3
    assert frame.customer_id.tolist() == ['001', '002', '003']
    assert frame.region.tolist() == ['NA', '#North', 'Total']
    assert 'empty' in frame and frame.empty is False
    assert DataTypeDetector.detect_column_type('customer_id', frame.customer_id)['data_type'] == 'Identifier'
    assert DataTypeDetector.detect_column_type('postal', pd.Series(['001', '002']))['data_type'] == 'Identifier'
    assert DataTypeDetector.detect_column_type('units', pd.Series(['0', '1']))['data_type'] == 'Integer'


@pytest.mark.parametrize('content', [b'id,value\n1,4\n2,5,extra\n3,6\n', b'id,value\n1\n', b'id,value\n1,"unclosed\n'])
def test_malformed_csv_is_rejected_without_silent_row_loss(content):
    with pytest.raises(DataValidationException):
        DataIngestionService(1).parse_raw_content(content, 'bad.csv')


def test_utf16_and_multiline_quoted_cells_are_preserved():
    source = 'code\tdescription\tamount\n001\t"A\n# B"\t4\n002\tNA\t5\n'
    frame = DataIngestionService(1).parse_raw_content(source.encode('utf-16'), 'records.tsv')
    assert frame.code.tolist() == ['001', '002']
    assert frame.description.tolist() == ['A\n# B', 'NA']


def test_json_pretty_printed_objects_parse_before_jsonl_and_bad_lines_reject():
    service = DataIngestionService(1)
    source = json.dumps({'data': [{'id':'001', 'value':1}, {'id':'002', 'value':2}]}, indent=2)
    assert service.parse_raw_content(source.encode(), 'source.json').id.tolist() == ['001', '002']
    with pytest.raises(DataValidationException, match='line 2'):
        service.parse_raw_content(b'{"id":"001"}\nBROKEN\n{"id":"003"}\n', 'source.jsonl')


def test_mixed_measurements_are_not_silently_coerced_and_locale_values_are_correct():
    descriptor = DataTypeDetector.detect_column_type('revenue', pd.Series(['1', '2', '3', 'pending']))
    assert descriptor['data_type'] not in ['Currency', 'Integer', 'Decimal']
    assert DataTypeDetector.clean_numeric_value('€1.250,50') == 1250.5
    assert DataTypeDetector.clean_numeric_value('$1,250.50') == 1250.5
    assert DataTypeDetector.clean_numeric_value('890,20') == 890.2
    assert DataTypeDetector.clean_numeric_value('1,2,3') is None
    assert DataTypeDetector.detect_column_type('revenue_id', pd.Series([0, 1]))['data_type'] == 'Identifier'


def test_small_excel_does_not_promote_a_data_row_or_drop_total_label():
    buf = io.BytesIO()
    pd.DataFrame({'group':['North', 'Total'], 'value':[1, 2]}).to_excel(buf, index=False)
    frame = DataIngestionService(1).parse_raw_content(buf.getvalue(), 'small.xlsx')
    assert frame['group'].tolist() == ['North', 'Total']
    assert len(frame) == 2


def test_explicit_numeric_headers_and_duplicate_names_preserve_every_column():
    frame = DataIngestionService(1).parse_raw_content(
        b'2020,amount,amount,amount_2\n10,20,30,40\n', 'columns.csv')
    assert frame.columns[0] == '2020'
    assert len(set(frame.columns)) == 4
    assert frame.iloc[0].tolist() == ['10', '20', '30', '40']


@pytest.mark.parametrize('value', ['NaN', 'Infinity', '-Infinity'])
def test_nonstandard_nonfinite_json_values_fail_with_an_actionable_error(value):
    with pytest.raises(DataValidationException, match='Use null'):
        DataIngestionService(1).parse_raw_content(
            ('[{"value":' + value + '}]').encode(), 'values.json')
