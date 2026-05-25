"""Error summary metric cards."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QGridLayout, QLabel


class SummaryCards(QFrame):
    """Display error/warning/duplicate/correction counts."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("summaryContainer")
        layout = QGridLayout(self)
        layout.setSpacing(12)
        self._cards: dict[str, QLabel] = {}
        metrics = [
            ("errors", "Errors", "errorsValue"),
            ("warnings", "Warnings", "warningsValue"),
            ("duplicates", "Duplicates", "duplicatesValue"),
            ("corrections", "Corrections", "correctionsValue"),
        ]
        for i, (key, title, obj_name) in enumerate(metrics):
            card = QFrame()
            card.setObjectName("card")
            card_layout = QGridLayout(card)
            card_layout.setContentsMargins(15, 15, 15, 15)
            
            t = QLabel(title)
            t.setObjectName("cardTitle")
            
            v = QLabel("0")
            v.setObjectName(obj_name)
            v.setProperty("class", "cardValue") # Generic class for shared styles
            
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
