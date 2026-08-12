from app.services.template_engine import TemplateEngine


def test_render_template():
    result = TemplateEngine.render("Hello, {{ name}}", {"name": "world"})
    assert result == "Hello, world"


def test_render_missing_variable():
    result = TemplateEngine.render("Hello {{ name }}", {})
    assert result == "Hello "
