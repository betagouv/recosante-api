// Per  Arrêté du 22 juillet 2004 relatif aux indices de la qualité de l'air (article 6)
export const QUALIFICATIF_TRES_BON = `Très bon`
export const QUALIFICATIF_BON = `Bon`
export const QUALIFICATIF_MOYEN = `Moyen`
export const QUALIFICATIF_MÉDIOCRE = `Médiocre`
export const QUALIFICATIF_MAUVAIS = `Mauvais`
export const QUALIFICATIF_TRÈS_MAUVAIS = `Très mauvais`

const INDICE_ATMO_TO_QUALIFICATIF = {
    1: QUALIFICATIF_TRES_BON,
    2: QUALIFICATIF_TRES_BON,
    3: QUALIFICATIF_BON,
    4: QUALIFICATIF_BON,
    5: QUALIFICATIF_MOYEN,
    6: QUALIFICATIF_MÉDIOCRE,
    7: QUALIFICATIF_MÉDIOCRE,
    8: QUALIFICATIF_MAUVAIS,
    9: QUALIFICATIF_MAUVAIS,
    10: QUALIFICATIF_TRÈS_MAUVAIS,
}

const LEGAL_QUALIFICATIF_TO_EMAIL_QUALIFICATIF = {
    [QUALIFICATIF_TRES_BON]: `très bonne`,
    [QUALIFICATIF_BON]: `bonne`,
    [QUALIFICATIF_MOYEN]: `moyenne`,
    [QUALIFICATIF_MÉDIOCRE]: `médiocre`,
    [QUALIFICATIF_MAUVAIS]: `mauvaise`,
    [QUALIFICATIF_TRÈS_MAUVAIS]: `très mauvaise`,
}

export const INDICE_ATMO_TO_EMAIL_QUALIFICATIF = Object.fromEntries(
    Object.entries(INDICE_ATMO_TO_QUALIFICATIF)
        .map(([indice, legalQualif]) => [indice, LEGAL_QUALIFICATIF_TO_EMAIL_QUALIFICATIF[legalQualif]])
)

export const EMAIL_QUALIFICATIF_TO_LEGAL_QUALIFICATIF = Object.fromEntries(
    Object.entries(LEGAL_QUALIFICATIF_TO_EMAIL_QUALIFICATIF)
        .map(([legalQualif, emailQualif]) => [emailQualif, legalQualif])
)