"""Deterministic, inspectable analysis over a tenant's actual dataset."""
import ast
import json
import operator
import numpy as np
import pandas as pd


def records(frame):
    return json.loads(frame.replace([np.inf, -np.inf], np.nan).to_json(orient="records", date_format="iso", double_precision=15))


def number(value):
    return float(value) if pd.notna(value) and np.isfinite(value) else None


class AnalystService:
    def __init__(self, frame):
        self.frame = frame[[c for c in frame.columns if not str(c).startswith('_')]].copy()

    def column(self, name, numeric=False):
        if name not in self.frame:
            raise ValueError(f"Unknown column: {name}")
        series = self.frame[name]
        if numeric:
            series = pd.to_numeric(series, errors='coerce').replace([np.inf, -np.inf], np.nan)
            if not series.notna().any():
                raise ValueError(f"{name} has no finite numeric values.")
        return series

    @staticmethod
    def _dates(series):
        if pd.api.types.is_numeric_dtype(series):
            raise ValueError('Choose a date column, not a numeric identifier or epoch value. Convert dates explicitly first.')
        return pd.to_datetime(series, errors='coerce', utc=True, format='mixed')

    def profile(self):
        df = self.frame
        columns = []
        numeric = df.select_dtypes(include='number').replace([np.inf, -np.inf], np.nan)
        for name in df:
            s = df[name]
            item = {'name': name, 'dtype': str(s.dtype), 'missing': int(s.isna().sum()),
                    'unique': int(s.nunique()), 'top_values': records(s.dropna().astype(str).value_counts().head(8).rename_axis('value').reset_index(name='count'))}
            if name in numeric:
                valid = numeric[name].dropna()
                item['statistics'] = {str(k): number(v) for k, v in valid.describe().items()}
                if len(valid):
                    counts, edges = np.histogram(valid, bins=min(12, max(1, int(np.sqrt(len(valid))))))
                    item['histogram'] = [{'from': float(edges[i]), 'to': float(edges[i+1]), 'count': int(counts[i])} for i in range(len(counts))]
            columns.append(item)
        limited = numeric.iloc[:, :30]
        return {'rows': len(df), 'columns': columns, 'duplicates': int(df.duplicated().sum()),
                'missing_cells': int(df.isna().sum().sum()), 'numeric_columns': list(numeric.columns),
                'correlation_columns': list(limited.columns),
                'correlations': records(limited.corr(min_periods=3).rename_axis('column').reset_index()),
                'notes': ['Correlations use pairwise complete observations and do not establish causation.', 'Correlation display is limited to the first 30 numeric columns.']}

    def prepare(self, operations):
        if not isinstance(operations, list) or len(operations) > 20:
            raise ValueError('Supply at most 20 preparation steps.')
        result = self.frame.copy()
        audit = []
        for operation in operations:
            if not isinstance(operation, dict):
                raise ValueError('Each preparation step must be an object.')
            op, col = operation.get('operation'), operation.get('column')
            before = len(result)
            missing_before = int(result[col].isna().sum()) if col in result else None
            if op == 'deduplicate':
                result = result.drop_duplicates()
            elif op == 'derive':
                from app.services.advanced_analysis import preparation_step
                result = preparation_step(self,result,operation)
            else:
                if col not in result:
                    raise ValueError(f'Unknown preparation column: {col}')
                if op == 'trim':
                    result[col] = result[col].map(lambda x: x.strip() if isinstance(x, str) else x)
                elif op == 'drop_missing':
                    result = result.dropna(subset=[col])
                elif op in ['fill_mean', 'fill_median']:
                    values = pd.to_numeric(result[col], errors='coerce').replace([np.inf, -np.inf], np.nan)
                    if (result[col].notna() & values.isna()).any():
                        raise ValueError('Convert invalid numeric values explicitly before imputing missing values.')
                    replacement = values.mean() if op == 'fill_mean' else values.median()
                    if pd.isna(replacement):
                        raise ValueError('Cannot impute a column with no numeric observations.')
                    result[col] = values.fillna(replacement)
                elif op == 'fill_value':
                    if operation.get('value') is None:
                        raise ValueError('A replacement value is required.')
                    result[col] = result[col].fillna(operation['value'])
                elif op == 'numeric':
                    result[col] = pd.to_numeric(result[col], errors='coerce').replace([np.inf, -np.inf], np.nan)
                elif op == 'date':
                    result[col] = self._dates(result[col])
                elif op == 'filter_equal':
                    result = result[result[col].astype(str) == str(operation.get('value'))]
                else:
                    from app.services.advanced_analysis import preparation_step
                    result = preparation_step(self,result,operation)
            audit.append({'operation': op, 'column': col, 'rows_before': before, 'rows_after': len(result), 'missing_before': missing_before,
                          'missing_after': int(result[col].isna().sum()) if col in result else None})
        if result.empty:
            raise ValueError('These steps remove every row. The original dataset has not been changed.')
        return result, audit

    def aggregate(self, metric, dimensions, aggregation='sum'):
        if aggregation not in ['sum', 'mean', 'median', 'min', 'max', 'count']:
            raise ValueError('Choose sum, mean, median, min, max or count.')
        if not isinstance(dimensions, list) or not 1 <= len(dimensions) <= 3:
            raise ValueError('Choose one to three grouping columns.')
        if len(set(dimensions)) != len(dimensions) or metric in dimensions:
            raise ValueError('Grouping columns must be distinct from one another and from the metric.')
        work = self.frame.copy()
        work[metric] = self.column(metric, True)
        for col in dimensions:
            self.column(col)
        grouped = work.groupby(dimensions, dropna=False, observed=True)[metric]
        values = grouped.sum(min_count=1) if aggregation == 'sum' else grouped.agg(aggregation)
        output = values.reset_index(name='value').sort_values('value', ascending=False)
        return {'method': f'{aggregation} by {", ".join(dimensions)}', 'rows': records(output.head(500)), 'total_groups': len(output), 'truncated': len(output) > 500}

    def _formula_series(self, expression):
        if not isinstance(expression, str) or len(expression) > 500:
            raise ValueError('Formula must be at most 500 characters.')
        try:
            tree = ast.parse(expression, mode='eval')
        except SyntaxError as error:
            raise ValueError('Formula syntax is invalid.') from error
        if len(list(ast.walk(tree))) > 60:
            raise ValueError('Formula is too complex.')
        operators = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: np.divide}
        def finite(value):
            if isinstance(value, pd.Series):
                return value.replace([np.inf, -np.inf], np.nan)
            return value if np.isfinite(value) else np.nan
        def evaluate(node):
            if isinstance(node, ast.Expression): return evaluate(node.body)
            if isinstance(node, ast.Name): return self.column(node.id, True)
            if isinstance(node, ast.Constant) and type(node.value) in (float, int):
                try:
                    return finite(float(node.value))
                except OverflowError as error:
                    raise ValueError('Formula constant is too large.') from error
            if isinstance(node, ast.BinOp) and type(node.op) in operators:
                with np.errstate(divide='ignore', invalid='ignore', over='ignore'):
                    return finite(operators[type(node.op)](evaluate(node.left), evaluate(node.right)))
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub): return -evaluate(node.operand)
            raise ValueError('Use column names, numbers, parentheses and + - * / only.')
        value = evaluate(tree)
        series = value if isinstance(value, pd.Series) else pd.Series(value, index=self.frame.index)
        series = series.replace([np.inf, -np.inf], np.nan)
        return series

    def formula(self, expression):
        series = self._formula_series(expression)
        return {'method': 'Row-level arithmetic; missing and undefined results are excluded.', 'expression': expression,
                'valid_rows': int(series.notna().sum()), 'undefined_rows': int(series.isna().sum()),
                'sum': number(series.sum(min_count=1)), 'mean': number(series.mean()),
                'rows': records(series.head(100).rename('value').rename_axis('row').reset_index())}

    def compare(self, metric, dimension, baseline, comparison):
        values = self.column(metric, True)
        groups = self.column(dimension).astype(str)
        if str(baseline) == str(comparison):
            raise ValueError('Choose two different groups.')
        a, b = values[groups == str(baseline)].dropna().to_numpy(), values[groups == str(comparison)].dropna().to_numpy()
        if min(len(a), len(b)) < 3:
            raise ValueError('Each group needs at least three finite observations.')
        if len(a) + len(b) > 20000:
            raise ValueError('This resampling test supports at most 20,000 observations. Filter the dataset first.')
        rng = np.random.default_rng(42)
        observed = float(b.mean() - a.mean())
        pooled = np.concatenate([a,b])
        extreme = 0
        boot = []
        for _ in range(1999):
            shuffled = rng.permutation(pooled)
            difference = shuffled[len(a):].mean() - shuffled[:len(a)].mean()
            extreme += abs(difference) >= abs(observed)
            boot.append(rng.choice(b, len(b), replace=True).mean() - rng.choice(a, len(a), replace=True).mean())
        low, high = np.quantile(boot, [.025,.975])
        return {'method': 'Two-sided permutation test of mean difference (1,999 permutations, fixed seed 42)',
                'baseline': baseline, 'comparison': comparison, 'baseline_n': len(a), 'comparison_n': len(b),
                'baseline_mean': float(a.mean()), 'comparison_mean': float(b.mean()), 'mean_difference': observed,
                'p_value': (extreme+1)/2000, 'confidence_interval_95': [float(low),float(high)],
                'notes': ['Requires independent, exchangeable observations under the null; not suitable for paired or time-dependent rows.', 'Interval is a percentile bootstrap interval for the mean difference. Small samples can be unstable.', 'Exploratory test; no correction for testing multiple hypotheses. Association is not proof of cause.']}

    def join(self, right, left_key, right_key, how='left', cardinality='many_to_one'):
        from app.services.advanced_analysis import validated_join
        return validated_join(self.frame,right,left_key,right_key,how,cardinality)

    def investigate(self, metric, date_column, dimension, split_date, baseline_start_date=None, comparison_end_date=None, filters=None):
        from app.services.advanced_analysis import investigate
        return investigate(self,metric,date_column,dimension,split_date,baseline_start_date,comparison_end_date,filters)

    def trend(self, metric, date_column, horizon=7):
        from app.services.advanced_analysis import forecast
        return forecast(self,metric,date_column,horizon)
