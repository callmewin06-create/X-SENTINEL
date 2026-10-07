"""Keep exact primary method names, including both M4 and fusion variants."""
from alembic import op
import sqlalchemy as sa

revision = '0002_primary_scores'
down_revision = '0001_v2_multiuser'
branch_labels = depends_on = None


def upgrade():
    # The imported initial migration uses already-prefixed check names under a
    # naming convention that prefixes them again. Preserve 0001 and normalize
    # those names here, including databases created without that convention.
    inspector=sa.inspect(op.get_bind())
    quote=op.get_bind().dialect.identifier_preparer.quote
    for table in inspector.get_table_names():
        prefix='ck_'+table+'_'
        for constraint in inspector.get_check_constraints(table):
            old=constraint['name']
            if old and old.startswith(prefix+prefix):
                new=old[len(prefix):]
                op.execute(sa.text(f'ALTER TABLE {quote(table)} RENAME CONSTRAINT {quote(old)} TO {quote(new)}'))
    op.drop_constraint(op.f('ck_detector_scores_detector_code_allowed'), 'detector_scores', type_='check')
    op.alter_column('detector_scores', 'detector_code', existing_type=sa.String(16), type_=sa.String(64))
    op.create_check_constraint(op.f('ck_detector_scores_detector_code_allowed'), 'detector_scores',
        "detector_code IN ('M1','M2','M3','M4','M5','TADR','STRIP','M3_view_mass','M4_shap_behavioral_conflict','M4_prob_gap','X_primary_reduced','X_primary_full')")


def downgrade():
    # Narrowing would discard primary history. Refuse rather than silently delete it.
    raise RuntimeError('Primary score history requires revision 0002; restore a pre-0002 backup to roll back')
