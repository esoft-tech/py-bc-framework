import os
import xml.etree.ElementTree as ET
from pathlib import Path


def create_simple_badge(
    left_txt: str,
    right_txt: str,
    color: str,
    output_path: Path,
) -> None:
    """
    Создает простой SVG-бейдж с заданным текстом и цветом.

    :param left_txt: Текст левой части бейджа.
    :param right_txt: Текст правой части бейджа.
    :param color: Цвет правой части бейджа (например, "green", "red", "blue").
    :param output_path: Путь для сохранения SVG-файла.
    """
    # Приблизительные размеры для текста. Можно доработать для более точного расчета.
    # Для простоты используем фиксированные значения, которые хорошо смотрятся для коротких текстов.
    padding = 10
    left_text_width = (len(left_txt) + 1) * 6 + padding
    right_text_width = (len(right_txt) + 1) * 6 + padding
    total_width = left_text_width + right_text_width

    # Радиус закругления
    r = 3

    svg_content = f"""<svg width="{total_width}" height="20" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <clipPath id="round-rect">
      <rect width="{total_width}" height="20" rx="{r}"/>
    </clipPath>
  </defs>
  <g clip-path="url(#round-rect)">
    <rect x="0" y="0" width="{left_text_width}" height="20" fill="#555"/>
    <rect x="{left_text_width}" y="0" width="{right_text_width}" height="20" fill="{color}"/>
  </g>
  <text x="{left_text_width / 2}" y="14" fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">{left_txt}</text>
  <text x="{left_text_width + right_text_width / 2}" y="14" fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">{right_txt}</text>
</svg>"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg_content, encoding="utf-8")


def run_pytest_and_create_badge() -> None:
    """
    Запускает тесты с pytest и создает бейдж на основе результата.
    """
    output_path = Path("./docs/source/_static/tests-badge.svg")
    if os.system("./.venv/bin/python -m pytest"):
        create_simple_badge(
            left_txt="tests",
            right_txt="failed",
            color="red",
            output_path=output_path,
        )
    else:
        create_simple_badge(
            left_txt="tests",
            right_txt="passed",
            color="green",
            output_path=output_path,
        )


def run_coverage_and_create_badge() -> None:
    """
    Запускает сбор покрытия кода с pytest-cov, генерирует XML-отчет и создает бейдж покрытия.
    """
    coverage_xml_path = Path("coverage.xml")
    output_path = Path("./docs/source/_static/coverage-badge.svg")

    # Запускаем pytest с генерацией XML-отчета по покрытию
    os.system("./.venv/bin/python -m pytest --cov=src --cov-report=xml")

    coverage_percent = 0.0
    if coverage_xml_path.exists():
        tree = ET.parse(coverage_xml_path)
        root = tree.getroot()
        # Ищем процент покрытия в XML-отчете
        # Обычно это атрибут 'line-rate' в теге 'coverage'
        coverage_element = root.find("coverage") or root
        if coverage_element is not None:
            coverage_percent = float(coverage_element.get("line-rate", "0.0")) * 100

    color = "red"
    if coverage_percent > 90:
        color = "green"
    elif coverage_percent > 70:
        color = "orange"
    else:
        color = "red"

    create_simple_badge(
        left_txt="coverage",
        right_txt=f"{coverage_percent:.0f}%",
        color=color,
        output_path=output_path,
    )


def run_mypy_and_create_badge() -> None:
    """
    Запускает проверку типов с помощью Mypy и создает бейдж на основе результата.
    """
    output_path = Path("./docs/source/_static/mypy-badge.svg")
    if os.system("./.venv/bin/python -m mypy ."):
        create_simple_badge(
            left_txt="mypy",
            right_txt="failed",
            color="red",
            output_path=output_path,
        )
    else:
        create_simple_badge(
            left_txt="mypy",
            right_txt="passed",
            color="green",
            output_path=output_path,
        )


def run_ruff_and_create_badge() -> None:
    """
    Запускает проверку кода с помощью Ruff и создает бейдж на основе результата.
    """
    output_path = Path("./docs/source/_static/ruff-badge.svg")
    if os.system("./.venv/bin/python -m ruff check ."):
        create_simple_badge(
            left_txt="Ɍuff",
            right_txt="failed",
            color="red",
            output_path=output_path,
        )
    else:
        create_simple_badge(
            left_txt="Ɍuff",
            right_txt="passed",
            color="green",
            output_path=output_path,
        )


if __name__ == "__main__":
    run_pytest_and_create_badge()
    run_coverage_and_create_badge()
    run_mypy_and_create_badge()
    run_ruff_and_create_badge()
