import pytest

from widgetastic.widget import View
from widgetastic_patternfly import (
    BarChart,
    GroupedBarChart,
    LineChart,
    SingleLineChart,
    SingleSplineChart,
    SparkLineChart,
    SplineChart,
)

SPARK_DATA = [10, 14, 12, 20, 31, 27, 44, 36, 52, 55, 62, 68, 69, 88, 74, 88, 91]

LINE_DATA = {
    "0": {"data5": "90", "data3": "70", "data2": "50", "data1": "30", "data4": "10"},
    "1": {"data4": "340", "data2": "220", "data1": "200", "data5": "150", "data3": "100"},
    "2": {"data3": "390", "data2": "310", "data5": "160", "data1": "100", "data4": "30"},
    "3": {"data1": "400", "data3": "295", "data4": "290", "data2": "240", "data5": "165"},
    "4": {"data5": "180", "data3": "170", "data1": "150", "data2": "115", "data4": "35"},
    "5": {"data1": "250", "data3": "220", "data2": "25", "data4": "20", "data5": "5"},
}

BAR_DATA = {
    "2013": {"Q1": "400", "Q2": "355", "Q3": "315", "Q4": "180"},
    "2014": {"Q1": "250", "Q2": "305", "Q3": "340", "Q4": "390"},
    "2015": {"Q1": "375", "Q2": "300", "Q3": "276", "Q4": "190"},
}

LINE_DATA_1 = {"0": "30", "1": "200", "2": "100", "3": "400", "4": "150", "5": "250"}

BAR_DATA_1 = {"Q1": "400", "Q2": "360", "Q3": "320", "Q4": "175"}

LINE_DATA_4 = {
    "0": {"data4": "10"},
    "1": {"data4": "340"},
    "2": {"data4": "30"},
    "3": {"data4": "290"},
    "4": {"data4": "35"},
    "5": {"data4": "20"},
}

BAR_DATA_Q4 = {"2013": {"Q4": "180"}, "2014": {"Q4": "390"}, "2015": {"Q4": "190"}}

LINE_LEGENDS = ["data1", "data2", "data3", "data4", "data5"]

BAR_LEGENDS = ["Q1", "Q3", "Q2", "Q4"]


class TestDataVisualization(View):
    spark = SparkLineChart(id="sparklineChart")

    single_line = SingleLineChart(id="singleLineChart")
    line = LineChart(id="lineChart")

    single_spline = SingleSplineChart(id="singleSplineChart")
    spline = SplineChart(id="splineChart")

    vertical_bar_chart = BarChart(id="verticalBarChart")
    gp_vertical_bar_chart = GroupedBarChart(id="groupedVerticalBarChart")
    stack_vertical_bar_chart = GroupedBarChart(id="stackedVerticalBarChart")

    horizontal_bar_chart = BarChart(id="horizontalBarChart")
    gp_horizontal_bar_chart = GroupedBarChart(id="groupedHorizontalBarChart")
    stack_horizontal_bar_chart = GroupedBarChart(id="stackedHorizontalBarChart")


def test_spark_line_chart(browser):
    view = TestDataVisualization(browser)

    assert view.spark.is_displayed
    data = view.spark.read()
    data_without_unit = [int(d.split("%")[0]) for d in data]
    assert data_without_unit == SPARK_DATA


@pytest.mark.parametrize(
    "graph", ["single_line", "single_spline", "vertical_bar_chart", "horizontal_bar_chart"]
)
def test_single_legend_charts(browser, graph):
    view = TestDataVisualization(browser)
    chart = getattr(view, graph)
    data = LINE_DATA_1 if "line" in graph else BAR_DATA_1

    assert chart.is_displayed

    # read overall chart
    assert chart.read() == data

    # check  for x axis values
    for x_point, value in data.items():
        assert chart.get_values(x_point)[x_point] == value


@pytest.mark.parametrize(
    "graph",
    [
        "line",
        "spline",
        "gp_vertical_bar_chart",
        "stack_vertical_bar_chart",
        "gp_horizontal_bar_chart",
        "stack_horizontal_bar_chart",
    ],
)
def test_multi_legend_charts(browser, graph):
    view = TestDataVisualization(browser)
    chart = getattr(view, graph)

    data = LINE_DATA if "line" in graph else BAR_DATA
    leg_data = LINE_DATA_4 if "line" in graph else BAR_DATA_Q4
    legs = LINE_LEGENDS if "line" in graph else BAR_LEGENDS
    fouth_leg = "data4" if "line" in graph else "Q4"

    assert chart.is_displayed
    # read full chart
    assert chart.read() == data

    # check  data as per x axis value
    for x_point, value in data.items():
        assert chart.get_values(x_point)[x_point] == value

    # check all legends on chart
    assert set(chart.legends) == set(legs)

    # check legends hide and display properties
    chart.display_all_legends()
    for leg in legs:
        chart.hide_legends(leg)
        assert not chart.legend_is_displayed(leg)

    chart.hide_all_legends()
    for leg in legs:
        chart.display_legends(leg)
        assert chart.legend_is_displayed(leg)

    # check data for particular legends
    assert chart.get_data_for_legends(fouth_leg) == leg_data
    assert chart.get_data_for_legends(*chart.legends) == data
