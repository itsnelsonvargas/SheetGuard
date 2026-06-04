"""Error summary metric cards."""

from __future__ import annotations

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QPainter, QLinearGradient, QPen, QBrush, QFont
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
        self._score = 0
        self._calculated = False  # Track if a score has been calculated
        self._is_hovering = False
        self._errors = 0
        self._warnings = 0
        self._duplicates = 0
        self._corrections = 0
        self.setMouseTracking(True)
        self._update_tooltip()

    def set_score(self, score: int, errors: int = 0, warnings: int = 0, duplicates: int = 0, corrections: int = 0) -> None:
        """Set score and update calculation metrics."""
        self._score = score
        self._calculated = True
        self._errors = errors
        self._warnings = warnings
        self._duplicates = duplicates
        self._corrections = corrections
        self._update_tooltip()
        self.update()

    def _get_score_color(self) -> QColor:
        """Return a color from Red (0) to Yellow (50) to Green (100)."""
        if not self._calculated:
            return QColor("#64748B")  # Slate gray for N/A
            
        if self._score < 50:
            # Red to Yellow
            ratio = self._score / 50.0
            r = 255
            g = int(255 * ratio)
            b = 0
        else:
            # Yellow to Green
            ratio = (self._score - 50) / 50.0
            r = int(255 * (1.0 - ratio))
            g = 255
            b = 0
        return QColor(r, g, b)

    def _update_tooltip(self) -> None:
        """Generate detailed tooltip showing the calculation formula."""
        if not self._calculated:
            tooltip = "Data Quality Score\n\nCalculation Formula:\nBase Score: 100\n- (Errors × 5)\n- (Warnings × 2)\n- (Duplicates × 3)\n+ (Corrections × 1, max +10)\n= Final Score (0-100)\n\nLoad data to calculate."
        else:
            # Calculate step by step
            base = 100
            error_deduct = self._errors * 5
            warning_deduct = self._warnings * 2
            duplicate_deduct = self._duplicates * 3
            correction_bonus = min(self._corrections, 10)
            
            tooltip = f"Data Quality Score: {self._score}\n\n"
            tooltip += "Calculation Breakdown:\n"
            tooltip += f"Base Score:           +100\n"
            tooltip += f"Errors ({self._errors} × -5):      -{error_deduct}\n"
            tooltip += f"Warnings ({self._warnings} × -2):    -{warning_deduct}\n"
            tooltip += f"Duplicates ({self._duplicates} × -3):  -{duplicate_deduct}\n"
            tooltip += f"Corrections ({self._corrections} × +1):  +{correction_bonus}\n"
            tooltip += "─" * 32 + "\n"
            tooltip += f"Final Score:          {self._score}/100\n\n"
            tooltip += "Legend:\n"
            tooltip += "• Errors: Critical validation issues\n"
            tooltip += "• Warnings: Minor anomalies\n"
            tooltip += "• Duplicates: Duplicate records found\n"
            tooltip += "• Corrections: Issues automatically fixed"
        
        self.setToolTip(tooltip)

    def enterEvent(self, event) -> None:
        """Handle mouse enter - show calculation indicator."""
        self._is_hovering = True
        self.update()

    def leaveEvent(self, event) -> None:
        """Handle mouse leave - hide calculation indicator."""
        self._is_hovering = False
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = QRectF(5, 5, 70, 70)
        
        # Draw background track
        pen_bg = QPen(QColor("#242B38"), 8)
        painter.setPen(pen_bg)
        painter.drawArc(rect, -45 * 16, 270 * 16)
        
        if self._calculated:
            # Draw active track (dynamic color)
            color = self._get_score_color()
            pen_active = QPen(QBrush(color), 8)
            pen_active.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen_active)
            
            span_angle = (self._score / 100.0) * 270
            painter.drawArc(rect, 225 * 16, -span_angle * 16)
        
        # Draw Score text
        text_color = self._get_score_color() if self._calculated else QColor("#FFFFFF")
        painter.setPen(text_color)
        font = painter.font()
        font.setPixelSize(22)
        font.setBold(True)
        painter.setFont(font)
        
        text = str(self._score) if self._calculated else "N/A"
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        
        # Show "Calculating..." when hovering
        if self._is_hovering and not self._calculated:
            # Semi-transparent overlay
            overlay_color = QColor(11, 14, 20, 200)  # Dark background with transparency
            painter.fillRect(QRectF(0, 0, 80, 80), overlay_color)
            
            # Draw "Calculating..." text
            painter.setPen(QColor("#00D4FF"))
            calc_font = painter.font()
            calc_font.setPixelSize(10)
            calc_font.setWeight(QFont.Weight.Bold)
            painter.setFont(calc_font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "Calculating...")



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
        
        # Weighted quality score calculation
        # Start at 100 and deduct points based on issues
        score = 100
        
        # Deduct for errors (most critical - 5 points each)
        score -= errors * 5
        
        # Deduct for warnings (less critical - 2 points each)
        score -= warnings * 2
        
        # Deduct for duplicates (3 points each)
        score -= duplicates * 3
        
        # Add bonus for corrections (1 point each, up to 10)
        score += min(corrections, 10)
        
        # Clamp score between 0 and 100
        score = max(0, min(100, score))
        
        self.dial.set_score(score, errors=errors, warnings=warnings, duplicates=duplicates, corrections=corrections)

    def reset(self) -> None:
        self.update_counts(0, 0, 0, 0)
