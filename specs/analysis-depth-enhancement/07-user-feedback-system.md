# Spec 07: User Feedback System
**Version:** 1.0
**Date:** February 10, 2026
**Status:** Ready for Implementation
**Dependencies:** Specs 01-06 (all features to gather feedback on)

---

## Executive Summary

This specification implements a **systematic user feedback system** to:

1. **Capture feedback** - In-app widgets, surveys, and direct submission
2. **Track feedback** - Database model, categorization, status tracking
3. **Prioritize feedback** - Voting, impact assessment, clustering
4. **Close the loop** - Link feedback to releases, notify users when addressed
5. **Drive improvement** - Analytics dashboard, trend identification

### Why This Matters

**User Feedback Context** (from audit):
- User provided feedback about earlier tool versions
- Unclear if feedback was systematically tracked
- No evidence of feedback → resolution verification
- Risk of same issues recurring

**Target State:**
- Every piece of feedback tracked in database
- User can see status of their feedback ("Under Review", "Planned", "Shipped")
- Team can prioritize based on user votes and impact
- Users notified when their feedback is addressed
- Analytics show feedback trends over time

---

## Architecture Overview

### Feedback Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   User Feedback Lifecycle                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  STAGE 1: CAPTURE                                           │
│  ──────────────────                                         │
│  User: "Cost calculations need more transparency"           │
│    ↓                                                         │
│  Widget: In-app feedback button                             │
│    ↓                                                         │
│  Form: Category, Description, Screenshot (optional)         │
│    ↓                                                         │
│  Database: FeedbackItem created                             │
│                                                              │
│  ↓                                                           │
│                                                              │
│  STAGE 2: TRIAGE                                            │
│  ────────────────                                           │
│  Admin reviews:                                              │
│    • Duplicate? → Link to existing                          │
│    • Category correct? → Re-categorize if needed            │
│    • Priority? → Set based on impact + votes                │
│    • Actionable? → Add to backlog or mark "Won't Fix"       │
│                                                              │
│  Status: new → triaged                                      │
│                                                              │
│  ↓                                                           │
│                                                              │
│  STAGE 3: PRIORITIZE                                        │
│  ─────────────────────                                      │
│  Factors:                                                    │
│    • User votes (other users +1 this)                       │
│    • Admin impact score (1-10)                              │
│    • Frequency (how often reported)                         │
│    • Deal value (high-value deals = higher priority)        │
│                                                              │
│  Backlog sorted by priority score                           │
│                                                              │
│  ↓                                                           │
│                                                              │
│  STAGE 4: IMPLEMENT                                         │
│  ────────────────────                                       │
│  Dev team:                                                   │
│    • Creates GitHub issue (linked to feedback)              │
│    • Implements fix/feature                                 │
│    • Links PR to feedback item                              │
│                                                              │
│  Status: triaged → in_progress → shipped                    │
│                                                              │
│  ↓                                                           │
│                                                              │
│  STAGE 5: NOTIFY                                            │
│  ─────────────────                                          │
│  System:                                                     │
│    • Email to submitter: "Your feedback was addressed!"     │
│    • In-app notification: "Check out what's new"            │
│    • Release notes: "Feedback #47: Cost transparency ✅"    │
│                                                              │
│  ↓                                                           │
│                                                              │
│  STAGE 6: VERIFY                                            │
│  ─────────────────                                          │
│  User:                                                       │
│    • Tests the fix                                          │
│    • Marks as "Resolved" or "Still an issue"                │
│                                                              │
│  If still an issue → Status: reopened                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Models

### FeedbackItem

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from web.database import db

class FeedbackItem(db.Model):
    """
    User feedback on the IT Diligence Agent.

    Tracks bugs, feature requests, and improvement suggestions.
    """
    __tablename__ = 'feedback_items'

    # Identity
    id = Column(String(50), primary_key=True)  # "FB-20260210-abc123"
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Submitter
    user_id = Column(String(100), ForeignKey('users.id'), nullable=False)
    user_email = Column(String(255))  # Denormalized for easy access
    deal_id = Column(String(100), ForeignKey('deals.id'), nullable=True)  # Context deal

    # Content
    category = Column(String(50), nullable=False, index=True)
    """Category: bug, feature_request, improvement, question, other"""

    subcategory = Column(String(50), nullable=True)
    """Subcategory: ui, performance, calculation, data_quality, etc."""

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    screenshot_url = Column(String(500), nullable=True)
    """Optional screenshot uploaded by user"""

    affected_page = Column(String(255), nullable=True)
    """URL of page where feedback was submitted"""

    # Context
    browser_info = Column(JSON, nullable=True)
    """Browser, version, OS, screen resolution"""

    # Status
    status = Column(String(50), default='new', index=True)
    """
    Status flow:
    - new: Just submitted
    - triaged: Reviewed by admin
    - in_progress: Being worked on
    - shipped: Fix deployed
    - resolved: User confirmed fix
    - won't_fix: Decided not to address
    - duplicate: Duplicate of another item
    """

    # Priority
    priority = Column(String(20), default='medium')
    """Priority: low, medium, high, critical"""

    impact_score = Column(Float, default=5.0)
    """Admin-assigned impact score (1-10)"""

    vote_count = Column(Integer, default=0)
    """Number of users who +1'd this feedback"""

    # Resolution
    resolution = Column(Text, nullable=True)
    """Description of how this was addressed"""

    resolved_in_version = Column(String(50), nullable=True)
    """Version number where fix was shipped"""

    resolved_at = Column(DateTime, nullable=True)

    github_issue_url = Column(String(500), nullable=True)
    """Link to GitHub issue if created"""

    # Relationships
    user = relationship("User", backref="feedback_items")
    deal = relationship("Deal", backref="feedback_items")
    votes = relationship("FeedbackVote", backref="feedback_item", cascade="all, delete-orphan")
    comments = relationship("FeedbackComment", backref="feedback_item", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<FeedbackItem {self.id}: {self.title[:50]}>"

    @property
    def priority_score(self) -> float:
        """
        Calculate priority score for ranking.

        Formula: impact_score * (1 + log(vote_count + 1)) * urgency_multiplier
        """
        import math

        # Base impact
        score = self.impact_score

        # Boost from votes (logarithmic to prevent dominance)
        vote_boost = 1 + math.log(self.vote_count + 1)
        score *= vote_boost

        # Urgency multiplier
        urgency = {
            'critical': 3.0,
            'high': 2.0,
            'medium': 1.0,
            'low': 0.5
        }.get(self.priority, 1.0)
        score *= urgency

        return score

    def to_dict(self) -> dict:
        """Serialize to JSON."""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "user_email": self.user_email,
            "deal_id": self.deal_id,
            "category": self.category,
            "subcategory": self.subcategory,
            "title": self.title,
            "description": self.description,
            "screenshot_url": self.screenshot_url,
            "affected_page": self.affected_page,
            "status": self.status,
            "priority": self.priority,
            "impact_score": self.impact_score,
            "vote_count": self.vote_count,
            "priority_score": self.priority_score,
            "resolution": self.resolution,
            "resolved_in_version": self.resolved_in_version,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "github_issue_url": self.github_issue_url,
        }

class FeedbackVote(db.Model):
    """User upvote on feedback item."""
    __tablename__ = 'feedback_votes'

    id = Column(Integer, primary_key=True)
    feedback_item_id = Column(String(50), ForeignKey('feedback_items.id'), nullable=False)
    user_id = Column(String(100), ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('feedback_item_id', 'user_id', name='unique_user_vote'),
    )

class FeedbackComment(db.Model):
    """Comments on feedback items (admin or user)."""
    __tablename__ = 'feedback_comments'

    id = Column(Integer, primary_key=True)
    feedback_item_id = Column(String(50), ForeignKey('feedback_items.id'), nullable=False)
    user_id = Column(String(100), ForeignKey('users.id'), nullable=False)
    user_email = Column(String(255))
    comment_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_admin = Column(Boolean, default=False)

    user = relationship("User")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_email": self.user_email,
            "comment_text": self.comment_text,
            "created_at": self.created_at.isoformat(),
            "is_admin": self.is_admin
        }
```

---

## In-App Feedback Widget

### Floating Feedback Button

**Component:** `FeedbackButton.jsx`

```jsx
import React, { useState } from 'react';
import { Button, Modal, Form } from 'react-bootstrap';
import { submitFeedback } from '../api/feedback';

const FeedbackButton = () => {
  const [showModal, setShowModal] = useState(false);
  const [category, setCategory] = useState('improvement');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [screenshot, setScreenshot] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const formData = new FormData();
      formData.append('category', category);
      formData.append('title', title);
      formData.append('description', description);
      formData.append('affected_page', window.location.href);
      formData.append('browser_info', JSON.stringify({
        user_agent: navigator.userAgent,
        screen: `${screen.width}x${screen.height}`
      }));

      if (screenshot) {
        formData.append('screenshot', screenshot);
      }

      await submitFeedback(formData);

      alert('Thank you for your feedback!');
      setShowModal(false);
      resetForm();
    } catch (error) {
      alert('Failed to submit feedback. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setCategory('improvement');
    setTitle('');
    setDescription('');
    setScreenshot(null);
  };

  return (
    <>
      {/* Floating button */}
      <div className="feedback-button-container">
        <Button
          variant="primary"
          className="feedback-button"
          onClick={() => setShowModal(true)}
        >
          💬 Feedback
        </Button>
      </div>

      {/* Feedback modal */}
      <Modal show={showModal} onHide={() => setShowModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Share Your Feedback</Modal.Title>
        </Modal.Header>

        <Form onSubmit={handleSubmit}>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>Category</Form.Label>
              <Form.Select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                required
              >
                <option value="bug">🐛 Bug Report</option>
                <option value="feature_request">✨ Feature Request</option>
                <option value="improvement">📈 Improvement</option>
                <option value="question">❓ Question</option>
                <option value="other">💭 Other</option>
              </Form.Select>
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Title</Form.Label>
              <Form.Control
                type="text"
                placeholder="Brief summary..."
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                maxLength={255}
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Description</Form.Label>
              <Form.Control
                as="textarea"
                rows={5}
                placeholder="Please describe your feedback in detail..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Screenshot (optional)</Form.Label>
              <Form.Control
                type="file"
                accept="image/*"
                onChange={(e) => setScreenshot(e.target.files[0])}
              />
              <Form.Text className="text-muted">
                A screenshot helps us understand the issue better
              </Form.Text>
            </Form.Group>
          </Modal.Body>

          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowModal(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" disabled={submitting}>
              {submitting ? 'Submitting...' : 'Submit Feedback'}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
    </>
  );
};

export default FeedbackButton;
```

**CSS:** `feedback-widget.css`

```css
.feedback-button-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 1000;
}

.feedback-button {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 12px 20px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 24px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.feedback-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}
```

---

## Admin Dashboard

### Feedback Management UI

**Component:** `FeedbackDashboard.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import { Table, Badge, Button, Form, Modal } from 'react-bootstrap';
import { fetchFeedbackItems, updateFeedbackStatus, addComment } from '../api/feedback';

const FeedbackDashboard = () => {
  const [feedback, setFeedback] = useState([]);
  const [filter, setFilter] = useState({ status: 'all', category: 'all' });
  const [selectedItem, setSelectedItem] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);

  useEffect(() => {
    loadFeedback();
  }, [filter]);

  const loadFeedback = async () => {
    const data = await fetchFeedbackItems(filter);
    setFeedback(data.items);
  };

  const handleStatusChange = async (itemId, newStatus) => {
    await updateFeedbackStatus(itemId, newStatus);
    loadFeedback();
  };

  const openDetail = (item) => {
    setSelectedItem(item);
    setShowDetailModal(true);
  };

  return (
    <div className="feedback-dashboard">
      <h2>Feedback Dashboard</h2>

      {/* Filters */}
      <div className="feedback-filters">
        <Form.Select
          value={filter.status}
          onChange={(e) => setFilter({ ...filter, status: e.target.value })}
        >
          <option value="all">All Statuses</option>
          <option value="new">New</option>
          <option value="triaged">Triaged</option>
          <option value="in_progress">In Progress</option>
          <option value="shipped">Shipped</option>
        </Form.Select>

        <Form.Select
          value={filter.category}
          onChange={(e) => setFilter({ ...filter, category: e.target.value })}
        >
          <option value="all">All Categories</option>
          <option value="bug">Bugs</option>
          <option value="feature_request">Feature Requests</option>
          <option value="improvement">Improvements</option>
        </Form.Select>
      </div>

      {/* Feedback Table */}
      <Table striped bordered hover>
        <thead>
          <tr>
            <th>ID</th>
            <th>Title</th>
            <th>Category</th>
            <th>Status</th>
            <th>Priority</th>
            <th>Votes</th>
            <th>Submitted</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {feedback.map((item) => (
            <tr key={item.id}>
              <td>{item.id}</td>
              <td>
                <a href="#" onClick={() => openDetail(item)}>
                  {item.title}
                </a>
              </td>
              <td>
                <Badge bg="info">{item.category}</Badge>
              </td>
              <td>
                <Form.Select
                  value={item.status}
                  onChange={(e) => handleStatusChange(item.id, e.target.value)}
                  size="sm"
                >
                  <option value="new">New</option>
                  <option value="triaged">Triaged</option>
                  <option value="in_progress">In Progress</option>
                  <option value="shipped">Shipped</option>
                  <option value="won't_fix">Won't Fix</option>
                </Form.Select>
              </td>
              <td>
                <Badge
                  bg={
                    item.priority === 'critical' ? 'danger' :
                    item.priority === 'high' ? 'warning' :
                    'secondary'
                  }
                >
                  {item.priority}
                </Badge>
              </td>
              <td>{item.vote_count}</td>
              <td>{new Date(item.created_at).toLocaleDateString()}</td>
              <td>
                <Button size="sm" onClick={() => openDetail(item)}>
                  View
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>

      {/* Detail Modal */}
      {selectedItem && (
        <FeedbackDetailModal
          show={showDetailModal}
          item={selectedItem}
          onHide={() => setShowDetailModal(false)}
          onUpdate={loadFeedback}
        />
      )}
    </div>
  );
};

export default FeedbackDashboard;
```

---

## API Endpoints

### POST /api/feedback/submit

**Submit new feedback**

```python
from flask import Blueprint, request, jsonify, current_user
from web.database import db, FeedbackItem
import uuid
from datetime import datetime

feedback_api = Blueprint('feedback_api', __name__)

@feedback_api.route('/api/feedback/submit', methods=['POST'])
def submit_feedback():
    """Submit new feedback item."""

    # Parse form data
    category = request.form.get('category')
    title = request.form.get('title')
    description = request.form.get('description')
    affected_page = request.form.get('affected_page')
    browser_info = request.form.get('browser_info')  # JSON string

    # Handle screenshot upload
    screenshot_url = None
    if 'screenshot' in request.files:
        screenshot = request.files['screenshot']
        # Upload to S3 or local storage
        screenshot_url = upload_screenshot(screenshot)

    # Create feedback item
    feedback_id = f"FB-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"

    feedback = FeedbackItem(
        id=feedback_id,
        user_id=current_user.id,
        user_email=current_user.email,
        deal_id=request.form.get('deal_id'),  # Optional context
        category=category,
        title=title,
        description=description,
        screenshot_url=screenshot_url,
        affected_page=affected_page,
        browser_info=json.loads(browser_info) if browser_info else None,
        status='new'
    )

    db.session.add(feedback)
    db.session.commit()

    # Notify admins (email/Slack)
    notify_admins_new_feedback(feedback)

    return jsonify({
        "success": True,
        "feedback_id": feedback_id,
        "message": "Thank you for your feedback!"
    }), 201

def upload_screenshot(file):
    """Upload screenshot to storage."""
    # Implement S3 or local file storage
    # Return public URL
    pass

def notify_admins_new_feedback(feedback):
    """Send notification to admins about new feedback."""
    # Email or Slack notification
    pass
```

### GET /api/feedback/list

**List feedback items with filtering**

```python
@feedback_api.route('/api/feedback/list', methods=['GET'])
def list_feedback():
    """List feedback items with filters."""

    status = request.args.get('status', 'all')
    category = request.args.get('category', 'all')
    sort_by = request.args.get('sort_by', 'priority_score')  # or 'created_at', 'vote_count'

    query = FeedbackItem.query

    # Filters
    if status != 'all':
        query = query.filter_by(status=status)

    if category != 'all':
        query = query.filter_by(category=category)

    # Sorting
    if sort_by == 'priority_score':
        # Sort by calculated property (requires subquery or Python sort)
        items = query.all()
        items.sort(key=lambda x: x.priority_score, reverse=True)
    elif sort_by == 'vote_count':
        items = query.order_by(FeedbackItem.vote_count.desc()).all()
    else:  # created_at
        items = query.order_by(FeedbackItem.created_at.desc()).all()

    return jsonify({
        "success": True,
        "items": [item.to_dict() for item in items],
        "total": len(items)
    })
```

### POST /api/feedback/<feedback_id>/vote

**Upvote feedback item**

```python
@feedback_api.route('/api/feedback/<feedback_id>/vote', methods=['POST'])
def vote_feedback(feedback_id):
    """Upvote feedback item."""

    feedback = FeedbackItem.query.get_or_404(feedback_id)

    # Check if already voted
    existing_vote = FeedbackVote.query.filter_by(
        feedback_item_id=feedback_id,
        user_id=current_user.id
    ).first()

    if existing_vote:
        return jsonify({"error": "Already voted"}), 400

    # Create vote
    vote = FeedbackVote(
        feedback_item_id=feedback_id,
        user_id=current_user.id
    )
    db.session.add(vote)

    # Increment vote count
    feedback.vote_count += 1

    db.session.commit()

    return jsonify({
        "success": True,
        "vote_count": feedback.vote_count
    })
```

### POST /api/feedback/<feedback_id>/comment

**Add comment to feedback**

```python
@feedback_api.route('/api/feedback/<feedback_id>/comment', methods=['POST'])
def add_feedback_comment(feedback_id):
    """Add comment to feedback item."""

    feedback = FeedbackItem.query.get_or_404(feedback_id)

    data = request.get_json()
    comment_text = data.get('comment')

    if not comment_text:
        return jsonify({"error": "Comment text required"}), 400

    comment = FeedbackComment(
        feedback_item_id=feedback_id,
        user_id=current_user.id,
        user_email=current_user.email,
        comment_text=comment_text,
        is_admin=current_user.is_admin
    )

    db.session.add(comment)
    db.session.commit()

    # Notify submitter if admin commented
    if comment.is_admin and feedback.user_id != current_user.id:
        notify_user_feedback_update(feedback, comment)

    return jsonify({
        "success": True,
        "comment": comment.to_dict()
    })
```

---

## Notification System

### Email Notifications

```python
from flask_mail import Message
from web.app import mail

def notify_user_feedback_shipped(feedback: FeedbackItem):
    """Notify user that their feedback was addressed."""

    subject = f"Your feedback was addressed! ({feedback.id})"

    body = f"""
Hi,

Good news! The feedback you submitted has been addressed in our latest release.

Your Feedback: "{feedback.title}"

Resolution:
{feedback.resolution}

Deployed in: Version {feedback.resolved_in_version}

You can now test the fix and let us know if it resolves your issue.

View Details: https://app.example.com/feedback/{feedback.id}

Thank you for helping us improve!

Best regards,
IT Diligence Agent Team
"""

    msg = Message(
        subject=subject,
        recipients=[feedback.user_email],
        body=body
    )

    mail.send(msg)
```

### In-App Notifications

```python
class UserNotification(db.Model):
    """In-app notifications for users."""
    __tablename__ = 'user_notifications'

    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), ForeignKey('users.id'), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    link_url = Column(String(500), nullable=True)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

def create_feedback_notification(feedback: FeedbackItem, event_type: str):
    """Create in-app notification for feedback event."""

    if event_type == "shipped":
        title = "Your feedback was addressed!"
        message = f'"{feedback.title}" has been resolved in version {feedback.resolved_in_version}'
    elif event_type == "commented":
        title = "New comment on your feedback"
        message = f'An admin commented on "{feedback.title}"'
    else:
        return

    notification = UserNotification(
        user_id=feedback.user_id,
        title=title,
        message=message,
        link_url=f"/feedback/{feedback.id}"
    )

    db.session.add(notification)
    db.session.commit()
```

---

## Analytics Dashboard

### Feedback Analytics

**Endpoint:** `/api/admin/feedback-analytics`

```python
@feedback_api.route('/api/admin/feedback-analytics', methods=['GET'])
def get_feedback_analytics():
    """Get feedback statistics and trends."""

    # Total counts by status
    status_counts = db.session.query(
        FeedbackItem.status,
        db.func.count(FeedbackItem.id)
    ).group_by(FeedbackItem.status).all()

    # Category breakdown
    category_counts = db.session.query(
        FeedbackItem.category,
        db.func.count(FeedbackItem.id)
    ).group_by(FeedbackItem.category).all()

    # Trend over time (last 90 days)
    from datetime import timedelta
    since = datetime.utcnow() - timedelta(days=90)

    trend = db.session.query(
        db.func.date(FeedbackItem.created_at).label('date'),
        db.func.count(FeedbackItem.id).label('count')
    ).filter(
        FeedbackItem.created_at >= since
    ).group_by('date').order_by('date').all()

    # Top voted items
    top_voted = FeedbackItem.query.filter(
        FeedbackItem.status.in_(['new', 'triaged', 'in_progress'])
    ).order_by(FeedbackItem.vote_count.desc()).limit(10).all()

    # Resolution time (average days from submission to shipped)
    resolved = FeedbackItem.query.filter_by(status='shipped').all()
    resolution_times = []
    for item in resolved:
        if item.resolved_at:
            delta = item.resolved_at - item.created_at
            resolution_times.append(delta.days)

    avg_resolution_days = sum(resolution_times) / len(resolution_times) if resolution_times else 0

    return jsonify({
        "status_breakdown": dict(status_counts),
        "category_breakdown": dict(category_counts),
        "trend_90d": [{"date": str(d), "count": c} for d, c in trend],
        "top_voted": [item.to_dict() for item in top_voted],
        "avg_resolution_days": avg_resolution_days,
        "total_submitted": FeedbackItem.query.count(),
        "total_shipped": FeedbackItem.query.filter_by(status='shipped').count()
    })
```

---

## Testing Strategy

### Unit Tests

```python
import pytest
from web.app import create_app
from web.database import db, FeedbackItem, FeedbackVote

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_submit_feedback(client):
    """Test feedback submission."""
    response = client.post('/api/feedback/submit', data={
        'category': 'bug',
        'title': 'Test Bug',
        'description': 'This is a test bug report'
    })

    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert 'feedback_id' in data

def test_vote_feedback(client):
    """Test upvoting feedback."""
    # Submit feedback first
    submit_response = client.post('/api/feedback/submit', data={
        'category': 'improvement',
        'title': 'Test Improvement',
        'description': 'Test description'
    })
    feedback_id = submit_response.get_json()['feedback_id']

    # Vote
    vote_response = client.post(f'/api/feedback/{feedback_id}/vote')
    assert vote_response.status_code == 200
    assert vote_response.get_json()['vote_count'] == 1

    # Duplicate vote should fail
    duplicate_vote = client.post(f'/api/feedback/{feedback_id}/vote')
    assert duplicate_vote.status_code == 400
```

---

## Implementation Checklist

### Phase 1: Data Models & API (Week 1)
- [ ] Create FeedbackItem, FeedbackVote, FeedbackComment models
- [ ] Write database migrations
- [ ] Implement API endpoints (submit, list, vote, comment)
- [ ] Unit tests for models and APIs

### Phase 2: In-App Widget (Week 1-2)
- [ ] Build FeedbackButton component
- [ ] Add screenshot upload functionality
- [ ] Integrate with API
- [ ] Test on all pages

### Phase 3: Admin Dashboard (Week 2)
- [ ] Build FeedbackDashboard component
- [ ] Implement filtering and sorting
- [ ] Add status update functionality
- [ ] Build detail view modal

### Phase 4: Notifications (Week 2-3)
- [ ] Implement email notifications
- [ ] Build in-app notification system
- [ ] Test notification triggers
- [ ] Add notification preferences

### Phase 5: Analytics & Reporting (Week 3)
- [ ] Build analytics dashboard
- [ ] Add trend visualization
- [ ] Create feedback reports
- [ ] Set up monitoring

---

## Success Criteria

✅ **Feedback system successful when:**

1. **Adoption:** >40% of active users submit at least one piece of feedback
2. **Response time:** Median triage time <48 hours
3. **Resolution rate:** >70% of feedback triaged and addressed or closed
4. **User satisfaction:** >80% of users report feeling "heard"
5. **Notification effectiveness:** >60% of shipped notifications result in user verification
6. **Data quality:** <5% duplicate or spam submissions

---

## Document Status

**Status:** ✅ Ready for Implementation
**Dependencies:** Specs 01-06 (features to gather feedback on)
**Next Steps:** Proceed to Spec 08 (Testing & Deployment)

**Author:** Claude Sonnet 4.5
**Date:** February 10, 2026
**Version:** 1.0
