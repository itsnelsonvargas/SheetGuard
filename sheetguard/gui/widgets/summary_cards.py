"""Error summary metric cards."""

from __future__ import annotations

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QPainter, QLinearGradient, QPen, QBrush
from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QVBoxLayout, QWidget, QSizePolicy


class SparklineWidget(QWidget):
    """A simplified interactive sparkline placeholder."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(150)
        self.setFixedHeight(60)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background gradient area
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(0, 212, 255, 40)) # Cyan with transparency
        gradient.setColorAt(1, QColor(0, 212, 255, 0))
        
        path_points = [
            QPointF(0, 40), QPointF(20, 30), QPointF(40, 50), 
            QPointF(60, 20), QPointF(80, 35), QPointF(100, 10),
            QPointF(120, 25), QPointF(150, 5)
        ]
        
        # Scale points to fit
        w_factor = self.width() / 150.0
        h_factor = self.height() / 60.0
        scaled_points = [QPointF(p.x() * w_factor, p.y() * h_factor + 10) for p in path_points]

        # Draw line
        pen = QPen(QColor("#00D4FF"), 2)
        painter.setPen(pen)
        for i in range(len(scaled_points) - 1):
            painter.drawLine(scaled_points[i], scaled_points[i+1])

        # Draw Magenta line
        pen_m = QPen(QColor("#F15BB5"), 2)
        painter.setPen(pen_m)
        path_points_m = [
            QPointF(0, 45), QPointF(30, 35), QPointF(60, 45), 
            QPointF(90, 25), QPointF(120, 40), QPointF(150, 30)
        ]
        scaled_m = [QPointF(p.x() * w_factor, p.y() * h_factor + 10) for p in path_points_m]
        for i in range(len(scaled_m) - 1):
            painter.drawLine(scaled_m[i], scaled_m[i+1])


class QualityScoreDial(QWidget):
    """A custom widget to render the Data-Quality Score dial."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(80, 80)
        self._score = 87

    def set_score(self, score: int) -> None:
        self._score = score
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = QRectF(5, 5, 70, 70)
        
        # Draw background track
        pen_bg = QPen(QColor("#242B38"), 8)
        painter.setPen(pen_bg)
        painter.drawArc(rect, -45 * 16, 270 * 16)
        
        # Draw active track (gradient)
        gradient = QLinearGradient(0, 0, 80, 80)
        gradient.setColorAt(0, QColor("#F15BB5")) # Magenta
        gradient.setColorAt(1, QColor("#00D4FF")) # Cyan
        
        pen_active = QPen(QBrush(gradient), 8)
        pen_active.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_active)
        
        span_angle = (self._score / 100.0) * 270
        painter.drawArc(rect, 225 * 16, -span_angle * 16)
        
        # Draw Score text
        painter.setPen(QColor("#FFFFFF"))
        font = painter.font()
        font.setPixelSize(22)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(self._score))


class SummaryCards(QFrame):
    """Display error/warning/duplicate/correction counts and a quality score."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("summaryContainer")
        self.setFixedHeight(120)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # 1. Sparkline (Left)
        spark_container = QFrame()
        spark_container.setObjectName("card")
        spark_layout = QVBoxLayout(spark_container)
        spark_layout.setContentsMargins(15, 10, 15, 10)
        
        self.sparkline = SparklineWidget()
        spark_layout.addWidget(self.sparkline)
        layout.addWidget(spark_container)

        # 2. Metrics (Middle)
        self._cards: dict[str, QLabel] = {}
        metrics = [
            ("errors", "ERRORS", "errorsValue", "#FF4D4D"),
            ("warnings", "WARNINGS", "warningsValue", "#FFB300"),
            ("duplicates", "DUPLICATES", "duplicatesValue", "#00D4FF"),
            ("corrections", "CORRECTIONS", "correctionsValue", "#00F5D4"),
        ]
        
        for key, title, obj_name, color_hex in metrics:
            card = QFrame()
            card.setObjectName("card")
            card.setMinimumWidth(100)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(15, 10, 15, 10)
            card_layout.setSpacing(2)
            
            t = QLabel(title)
            t.setObjectName("cardTitle")
            
            v = QLabel("0")
            v.setObjectName(obj_name)
            v.setStyleSheet(f"color: {color_hex}; font-size: 28px; font-weight: 800; background: transparent;")
            
            card_layout.addWidget(t)
            card_layout.addWidget(v)
            layout.addWidget(card)
            self._cards[key] = v

        layout.addStretch()

        # 3. Data Quality Score (Right)
        score_container = QFrame()
        score_container.setObjectName("card")
        score_container.setFixedWidth(200)
        score_layout = QHBoxLayout(score_container)
        score_layout.setContentsMargins(15, 10, 15, 10)
        
        score_text_layout = QVBoxLayout()
        st = QLabel("DATA-QUALITY SCORE")
        st.setObjectName("cardTitle")
        st.setWordWrap(True)
        score_text_layout.addWidget(st)
        score_text_layout.addStretch()
        
        self.dial = QualityScoreDial()
        
        score_layout.addLayout(score_text_layout)
        score_layout.addWidget(self.dial)
        layout.addWidget(score_container)

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
        
        # Simple heuristic for score
        total_issues = errors + warnings + duplicates
        score = max(0, 100 - total_issues)
        self.dial.set_score(score)

    def reset(self) -> None:
        self.update_counts(0, 0, 0, 0)
