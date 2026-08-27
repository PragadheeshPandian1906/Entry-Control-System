"""
Draws bounding boxes and result labels onto frames for saved snapshots.
"""
import cv2

GREEN = (0, 200, 0)
RED = (0, 0, 220)
YELLOW = (0, 200, 200)


def draw_box(frame, box, label: str, color=GREEN, thickness=2):
    x1, y1, x2, y2 = [int(v) for v in box]
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
    if label:
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (x1, max(0, y1 - th - 10)), (x1 + tw + 6, y1), color, -1)
        cv2.putText(frame, label, (x1 + 3, max(15, y1 - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    return frame


def draw_decision_banner(frame, decision: str):
    color = GREEN if decision == "ACCESS_GRANTED" else RED
    text = "ACCESS GRANTED" if decision == "ACCESS_GRANTED" else "SECURITY VERIFICATION REQUIRED"
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, h - 40), (w, h), color, -1)
    cv2.putText(frame, text, (10, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    return frame
