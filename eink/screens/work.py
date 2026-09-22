"""Work screen: GitHub pull request status."""
from .base import Screen
from .. import theme
from ..layout import truncate_chars

TITLE_CHARS = 10


class WorkScreen(Screen):
    id = 'work'
    requires = ('github',)

    def render(self, canvas, rect, ctx):
        github = ctx.load('github')
        if github is None:
            return

        icon = canvas.icon('github', 'icon.png')
        icon_x = rect.x + theme.MARGIN
        icon_y = rect.y + theme.MARGIN
        canvas.paste(icon, (icon_x, icon_y))

        text_x = icon_x + theme.ICON + theme.ICON_GAP
        text_y = icon_y

        for pr in github.get('opened_prs', [])[:3]:
            title = truncate_chars(pr.get('title', 'No title'), TITLE_CHARS)
            state = 'draft' if pr.get('draft', False) else pr.get('state', 'unknown')
            canvas.text((text_x, text_y), f"{title} - {state}", theme.BODY)
            text_y += theme.LINE_HEIGHT

        # Review count sits below the icon, never overlapping the PR list.
        text_y = max(text_y, icon_y + theme.ICON + theme.ICON_GAP)
        review_prs = github.get('prs_for_review', 0)
        summary = f"{review_prs} PRs to review" if review_prs > 0 else "No PRs to review :)"
        canvas.text((icon_x, text_y), summary, theme.BODY)
