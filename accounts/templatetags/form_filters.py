from django import template

register = template.Library()

@register.filter(name='addclass')
def addclass(field, css_class):
    """添加CSS类到表单字段"""
    return field.as_widget(attrs={'class': css_class})