"""Modification villes

Revision ID: 08bb5d4e3455
Revises: 86489b0fc49b
Create Date: 2022-02-23 12:14:55.426279

"""
from alembic import op
import sqlalchemy as sa
import csv
from indice_pollution.history.models.commune import Commune


# revision identifiers, used by Alembic.
revision = '08bb5d4e3455'
down_revision = '6603bd49a22b'
branch_labels = None
depends_on = None


def upgrade():
    with open("migrations/data/nouvelles-communes-2021.csv") as f:
        reader = csv.DictReader(f, fieldnames=['DepComN','NomCN','DepComA','NomCA','ChefLieu','ComDLG','Date1','Date1_bis','Date2','Date3','Commentaire'])
        lines = list(reversed(list(reader)[1:]))
    for line in lines:
        if line['DepComA'] != line['DepComN']:
            op.execute(
                sa.text("""UPDATE inscription
                    SET commune_id = (SELECT id FROM indice_schema.commune WHERE insee=:nouvel_insee)
                    WHERE commune_id=(SELECT id from indice_schema.commune WHERE insee=:ancien_insee)"""
                ).bindparams(
                    nouvel_insee=line['DepComN'], ancien_insee=line['DepComA']
                )
            )
            op.execute(sa.text("DELETE FROM indice_schema.commune WHERE insee=:insee").bindparams(insee=line['DepComA']))
        else:
            op.execute(sa.text("UPDATE indice_schema.commune SET nom = :nouveau_nom WHERE insee = :insee").bindparams(
            nouveau_nom=line['NomCN'], insee=line['DepComA']))

def downgrade():
    pass
