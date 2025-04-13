"""empty message

Revision ID: 3ea5f9e5fb69
Revises: 4fde214637ab, ccaaf76c889f
Create Date: 2025-04-13 23:46:14.670140

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "3ea5f9e5fb69"
down_revision = ("4fde214637ab", "ccaaf76c889f")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
