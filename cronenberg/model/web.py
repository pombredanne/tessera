import json
import uuid
import base64

class EntityEncoder(json.JSONEncoder):
    def default(self, obj):
            # TODO - handle iterables
        if isinstance(obj, list) or isinstance(obj, tuple):
            return [ self.default(i) for i in obj ]
        elif isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                result[key] = self.default(value)
            return result
        elif hasattr(obj, 'to_json') and callable(getattr(obj, 'to_json')):
            return obj.to_json()
        elif hasattr(obj, '__dict__'):
            return self.default(obj.__dict__)
        else:
            return obj

def dumps(obj):
    return json.dumps(obj, cls=EntityEncoder, indent=0)

# -----------------------------------------------------------------------------
# Dashboard Items
# -----------------------------------------------------------------------------

def _delattr(dictionary, attr):
    if attr in dictionary:
        del dictionary[attr]

class Thresholds(object):
    def __init__(self, summation_type='max', warning=None, danger=None):
        self.summation_type = summation_type
        self.warning = warning
        self.danger = danger

class DashboardItem(object):
    """Layout elements are class that define how presentations are
    arrange in the dashboard. The base class provides common CSS class
    overriding.
    """
    NEXT = 1

    class Style:
        PLAIN           = None
        WELL            = 'well'
        CALLOUT_NEUTRAL = 'callout_neutral'
        CALLOUT_INFO    = 'callout_info'
        CALLOUT_SUCCESS = 'callout_success'
        CALLOUT_WARNING = 'callout_warning'
        CALLOUT_DANGER  = 'callout_danger'

    def __init__(self, item_type, element_id=None, css_class='', style=Style.PLAIN, height=None, **kwargs):
        self.item_type = item_type
        self.css_class = css_class
        self.element_id = DashboardItem.nextid()
        self.height = height
        self.style = style

    @staticmethod
    def nextid():
        DashboardItem.NEXT += 1
        return 'd{0}'.format(DashboardItem.NEXT)

    @classmethod
    def from_json(cls, d):
        # TODO - this can be handled more cleanly and more
        # pythonically. E.g. with a dict, or some decorators, or a
        # metaclass.
        item_type = d['item_type']
        _delattr(d, 'item_type')
        if item_type == 'separator':
            return Separator.from_json(d)
        elif item_type == 'heading':
            return Heading.from_json(d)
        elif item_type == 'markdown':
            return Markdown.from_json(d)
        elif item_type == 'row':
            return Row.from_json(d)
        elif item_type == 'grid':
            return Grid.from_json(d)
        elif item_type == 'singlestat':
            return SingleStat.from_json(d)
        elif item_type == 'jumbotron_singlestat':
            return JumbotronSingleStat.from_json(d)
        elif item_type == 'simple_time_series':
            return SimpleTimeSeries.from_json(d)
        elif item_type == 'singlegraph':
            return SingleGraph.from_json(d)
        elif item_type =='standard_time_series':
            return StandardTimeSeries.from_json(d)
        elif item_type == 'stacked_area_chart':
            return StackedAreaChart.from_json(d)
        elif item_type == 'summation_table':
            return SummationTable.from_json(d)
        elif item_type == 'donut_chart':
            return DonutChart.from_json(d)
        else:
            return Cell.from_json(d)

# -----------------------------------------------------------------------------
# Presentations
# -----------------------------------------------------------------------------

class Presentation(DashboardItem):
    class Transform:
        MIN    = 'min'
        MAX    = 'max'
        MEDIAN = 'median'
        MEAN   = 'mean'
        LAST   = 'last'
        FIRST  = 'first'

    def __init__(self, query_name, thresholds=None, **kwargs):
        super(Presentation, self).__init__(**kwargs)
        self.query_name = query_name
        self.thresholds = thresholds


# -----------------------------------------------------------------------------
# Text Presentations
# -----------------------------------------------------------------------------

class SingleStat(Presentation):
    def __init__(self, title, query_name, units='', format=',.3f', index=False, transform=Presentation.Transform.MEAN, **kwargs):
        super(SingleStat, self).__init__(query_name=query_name,
                                         item_type=kwargs.get('item_type', 'singlestat'),
                                         **kwargs)
        self.title = title
        self.transform = transform
        self.index = index
        self.units = units
        self.format = format

    @classmethod
    def from_json(cls, d):
        _delattr(d, 'item_type')
        return cls(**d)

class JumbotronSingleStat(SingleStat):
    def __init__(self, **kwargs):
        super(JumbotronSingleStat, self).__init__(**kwargs)
        self.item_type='jumbotron_singlestat'

    @classmethod
    def from_json(cls, d):
        _delattr(d, 'item_type')
        return cls(**d)

class TablePresentation(Presentation):
    """Base class for all text-table-based presentations."""
    def __init__(self, **kwargs):
        super(TablePresentation, self).__init__(**kwargs)

class SummationTable(TablePresentation):
    # TODO - control which columns are shown
    def __init__(self, query_name, format=',.3f', striped=False, **kwargs):
        super(SummationTable, self).__init__(query_name=query_name,
                                             item_type='summation_table',
                                             **kwargs)
        self.format = format
        self.striped = striped

    @classmethod
    def from_json(cls, d):
        _delattr(d, 'item_type')
        return cls(**d)

# -----------------------------------------------------------------------------
# Chart Presentations
# -----------------------------------------------------------------------------

class ChartPresentation(Presentation):
    """Base class for all chart presentations."""
    def __init__(self, title='', options=None, interactive=True, **kwargs):
        super(ChartPresentation, self).__init__(**kwargs)
        self.title = title
        self.options = options or {}
        self.interactive = interactive

class DonutChart(ChartPresentation):
    def __init__(self, **kwargs):
        super(DonutChart, self).__init__(item_type='donut_chart', **kwargs)

    @classmethod
    def from_json(cls, d):
        _delattr(d, 'item_type')
        return cls(**d)

class SimpleTimeSeries(ChartPresentation):
    """A simple, somewhat abstracted view of a single time series,
    presented without a lot of chart extras, for high level
    visualizations.

    """
    def __init__(self, query_name, filled=False, **kwargs):
        super(SimpleTimeSeries, self).__init__(query_name=query_name,
                                               item_type='simple_time_series',
                                               **kwargs)
        self.filled = filled

    @classmethod
    def from_json(cls, d):
        _delattr(d, 'item_type')
        return cls(**d)

class SingleGraph(ChartPresentation):
    """A combination of SingleStat and SimpleTimeSeries - displays a
    single metric as a line graph, with a summation value overlayed
    (ala Tasseo).

    """
    def __init__(self, query_name, format=',.1s', transform=Presentation.Transform.MEAN, **kwargs):
        super(SingleGraph, self).__init__(query_name=query_name,
                                          item_type=kwargs.get('item_type', 'singlegraph'),
                                          **kwargs)
        self.format = format
        self.transform = transform

    @classmethod
    def from_json(cls, d):
        _delattr(d, 'item_type')
        return cls(**d)

class StandardTimeSeries(ChartPresentation):
    """A multi-series time series line chart, with all the bells and
    whistles.

    """
    def __init__(self, query_name, **kwargs):
        super(StandardTimeSeries, self).__init__(query_name=query_name,
                                                 item_type='standard_time_series',
                                                 **kwargs)
    @classmethod
    def from_json(cls, d):
        _delattr(d, 'item_type')
        return cls(**d)

class StackedAreaChart(ChartPresentation):
    """A multi-series stacked time series area chart, with all the bells
    and whistles and a few extras to boot.

    """
    def __init__(self, query_name, **kwargs):
        super(StackedAreaChart, self).__init__(query_name=query_name,
                                               item_type='stacked_area_chart',
                                               **kwargs)
    @classmethod
    def from_json(cls, d):
        _delattr(d, 'item_type')
        return cls(**d)

# -----------------------------------------------------------------------------
# Layouts
# -----------------------------------------------------------------------------

class Cell(DashboardItem):
    """Cell defines how to position and size a presentation on the
    grid. Cells should be contained in Rows.
    """
    def __init__(self, items, span, offset=None, align=None, **kwargs):
        super(Cell, self).__init__(item_type='cell', **kwargs)
        self.items = items if isinstance(items, list) else [items]
        self.span = span
        self.offset = offset
        self.align = align

    @classmethod
    def from_json(cls, d):
        d['items'] = [DashboardItem.from_json(p) for p in d['items']]
        _delattr(d, 'item_type')
        return Cell(**d)


class Row(DashboardItem):
    """A row holds one or more Cells, which span a single row in the
    rendered layout grid. An instance of Row maps directly to a <div
    class="row">...</div>.
    """
    def __init__(self, *items, **kwargs):
        super(Row, self).__init__(item_type='row', **kwargs)
        self.items = [] if len(items) == 0 else items

    @classmethod
    def from_json(cls, d):
        items = [DashboardItem.from_json(c) for c in d['items']]
        _delattr(d, 'item_type')
        _delattr(d, 'items')
        return Row(*items, **d)


class Grid(DashboardItem):
    def __init__(self, *items, **kwargs):
        super(Grid, self).__init__(item_type='grid', **kwargs)
        self.items = [] if len(items) == 0 else items

    @classmethod
    def from_json(cls, d):
        if not d:
            return Grid()
        items = [DashboardItem.from_json(r) for r in d['items']]
        _delattr(d, 'item_type')
        _delattr(d, 'items')
        return Grid(*items, **d)


class Separator(DashboardItem):
    """A visual element to separate groups of elements.
    """
    def __init__(self, **kwargs):
        super(Separator, self).__init__(item_type='separator', **kwargs)

    @classmethod
    def from_json(cls, d):
        return Separator(css_class=d['css_class'])


class Heading(DashboardItem):
    """A large text label."""
    def __init__(self, text, level=1, description='', **kwargs):
        super(Heading, self).__init__(item_type='heading', **kwargs)
        self.text = text
        self.level = level
        self.description = description

    @classmethod
    def from_json(cls, d):
        return Heading(text=d['text'],
                       level=d['level'],
                       description = d.get('description', ''),
                       css_class=d['css_class'])


class Markdown(DashboardItem):
    def __init__(self, text, raw=False, **kwargs):
        super(Markdown, self).__init__(item_type='markdown', **kwargs)
        self.text = text
        self.raw = raw

    @classmethod
    def from_json(cls, d):
        return Markdown(**d)


class DashboardDefinition(object):
    def __init__(self, queries=None, grid=None, item_type='dashboard'):
        self.item_type = item_type
        self.queries = queries or {}
        self.grid = grid or Grid()

    @classmethod
    def from_json(cls, data):
        data['grid'] = Grid.from_json(data.get('grid', None))
        return DashboardDefinition(**data)
