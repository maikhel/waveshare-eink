"""Work: my open pull requests and the ones waiting on my review."""
from .base import Screen
from .. import theme, widgets
from ..layout import Rect

COLUMN_GAP = 30
MARKER_WIDTH = 20
ROW_HEIGHT = 50
META_OFFSET = 25

# reviewDecision -> (marker shape, label). None means nobody has looked yet.
REVIEW_STATES = {
    'APPROVED': ('filled', 'approved'),
    'CHANGES_REQUESTED': ('triangle', 'changes requested'),
    'REVIEW_REQUIRED': ('hollow', 'review required'),
    None: ('hollow', 'review required'),
}

DRAFT_STATE = ('square', 'draft')

CI_LABELS = {
    'SUCCESS': 'CI ok',
    'FAILURE': 'CI failed',
    'ERROR': 'CI failed',
    'PENDING': 'CI running',
    'EXPECTED': 'CI running',
}


def _meta_line(*parts):
    return ' · '.join(part for part in parts if part)


class WorkScreen(Screen):
    id = 'work'
    requires = ('github',)

    def render(self, canvas, rect, ctx):
        github = ctx.load('github')
        if github is None:
            return

        body = Rect(rect.x + theme.MARGIN, rect.y + 10,
                    rect.w - 2 * theme.MARGIN, rect.h - 20)
        left, right = body.columns(2, gap=COLUMN_GAP)

        divider_x = (left.right + right.x) // 2
        canvas.line([divider_x, body.y, divider_x, body.bottom])

        self._draw_mine(canvas, left, github.get('opened_prs', []))
        self._draw_review_queue(canvas, right, github)

    def _draw_mine(self, canvas, rect, prs):
        rows = widgets.section_header(canvas, rect, "MY PRS", len(prs))
        if not prs:
            canvas.text((rows.x, rows.y), "Nothing open.", theme.LIST)
            return

        for pr, row in self._rows(rows, prs):
            shape, label = DRAFT_STATE if pr.get('draft') else \
                REVIEW_STATES.get(pr.get('review'), REVIEW_STATES[None])

            widgets.marker(canvas, row.x, row.y + 5, shape)
            title_x = row.x + MARKER_WIDTH
            title_width = row.w - MARKER_WIDTH
            canvas.text((title_x, row.y),
                        canvas.fit_text(pr.get('title', ''), theme.LIST, title_width),
                        theme.LIST)
            canvas.text((title_x, row.y + META_OFFSET),
                        _meta_line(label, CI_LABELS.get(pr.get('ci'))),
                        theme.LIST_META)

    def _draw_review_queue(self, canvas, rect, github):
        queue = github.get('review_requested', [])
        total = github.get('prs_for_review', len(queue))

        rows = widgets.section_header(canvas, rect, "TO REVIEW", total)
        if not queue:
            canvas.text((rows.x, rows.y), "Nothing waiting :)", theme.LIST)
            return

        shown = list(self._rows(rows, queue, reserve_last=total > 0))
        for pr, row in shown:
            canvas.text((row.x, row.y),
                        canvas.fit_text(pr.get('title', ''), theme.LIST, row.w),
                        theme.LIST)
            canvas.text((row.x, row.y + META_OFFSET),
                        _meta_line(pr.get('repo'), CI_LABELS.get(pr.get('ci'))),
                        theme.LIST_META)

        hidden = total - len(shown)
        if hidden > 0:
            last = shown[-1][1]
            canvas.text((rect.x, last.y + ROW_HEIGHT), f"+ {hidden} more", theme.LIST_META)

    @staticmethod
    def _rows(rect, items, reserve_last=False):
        """Pair items with the row rects that fit, leaving room for a '+N' line."""
        capacity = rect.h // ROW_HEIGHT
        if reserve_last and len(items) > capacity:
            capacity -= 1

        for i, item in enumerate(items[:max(capacity, 0)]):
            yield item, Rect(rect.x, rect.y + i * ROW_HEIGHT, rect.w, ROW_HEIGHT)
