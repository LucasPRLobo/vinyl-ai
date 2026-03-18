# Import all models so SQLAlchemy registers them for table creation
from app.models.user import User  # noqa: F401
from app.models.group import Group, GroupMembership  # noqa: F401
from app.models.feed_event import FeedEvent  # noqa: F401
from app.models.annotation import Annotation  # noqa: F401
from app.models.store import Store, StoreVisit  # noqa: F401
from app.models.ritual import Rotation, DigChallenge, CrateCensus  # noqa: F401
