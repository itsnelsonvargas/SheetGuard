"""Error summary metric cards."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QGridLayout, QLabel


class SummaryCards(QFrame):
    """Display error/warning/duplicate/correction counts."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setSpacing(12)
        self._cards: dict[str, QLabel] = {}
        metrics = [
            ("errors", "Errors", "#dc2626"),
            ("warnings", "Warnings", "#d97706"),
            ("duplicates", "Duplicates", "#7c3aed"),
            ("corrections", "Corrections", "#16a34a"),
        ]
        for i, (key, title, color) in enumerate(metrics):
            card = QFrame()
            card.setObjectName("card")
            card_layout = QGridLayout(card)
            t = QLabel(title)
            t.setObjectName("cardTitle")
            v = QLabel("0")
            v.setObjectName("cardValue")
            v.setStyleSheet(f"color: {color};")
            card_layout.addWidget(t, 0, 0)
            card_layout.addWidget(v, 1, 0)
            layout.addWidget(card, 0, i)
            self._cards[key] = v

    def update_counts(
        self,
        errors: int = 0,
        warnings: int = 0,
        duplicates: int = 0,
        corrections: int = 0,
    ) -> None:
        self._cards["errors"].setText(str(errors))
        self._cards["warnings"].setText(str(warnings))
        self._cards["duplicates"].setText(str(duplicates))
        self._cards["corrections"].setText(str(corrections))

    def reset(self) -> None:
        self.update_counts(0, 0, 0, 0)
