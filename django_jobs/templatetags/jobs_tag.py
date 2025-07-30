from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary in templates"""
    return dictionary.get(key)


@register.filter
def status_color(status):
    """Return color based on job status"""
    colors = {
        'P': '#ffc107',  # Pending - yellow
        'R': '#17a2b8',  # Running - blue
        'S': '#28a745',  # Success - green
        'F': '#dc3545',  # Failure - red
    }
    return colors.get(status, '#6c757d')  # Default - gray


@register.simple_tag
def job_status_badge(status, status_display):
    """Create a colored status badge"""
    color = status_color(status)
    return f'<span style="color: {color}; font-weight: bold;">{status_display}</span>'