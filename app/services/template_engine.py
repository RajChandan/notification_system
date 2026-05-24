import re


class TemplateEngine:
    pattern = re.compile(r"{{\s*(\w+)\s*}}")

    @staticmethod
    def render(template: str, payload: dict) -> str:
        def replacer(match):
            key = match.group(1)
            return str(payload.get(key, ""))

        return TemplateEngine.pattern.sub(replacer, template)
