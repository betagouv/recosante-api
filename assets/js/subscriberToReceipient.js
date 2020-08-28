const OUI = `Oui`;
const NON = `Non`;

const INPUT_ALLERGIQUE_COLUMN_NAME = 'Êtes-vous allergique aux pollens ?'
const OUTPUT_ALLERGIQUE_COLUMN_NAME = 'Allergies'

const INPUT_EMAIL_COLUMN_NAME = `Votre adresse e-mail : elle permettra à l'Equipe Ecosanté de communiquer avec vous si besoin.`
const OUTPUT_EMAIL_COLUMN_NAME = 'Mail'

const OUTPUT_REGION_COLUMN_NAME = 'Région'

export const INPUT_VILLE_COLUMN_NAME = 'Dans quelle ville vivez-vous ?'
const OUTPUT_VILLE_COLUMN_NAME = 'Ville'

const INPUT_PATHOLOGIE_RESPIRATOIRE_COLUMN_NAME = `Vivez-vous avec une pathologie respiratoire ?`
const OUTPUT_PATHOLOGIE_RESPIRATOIRE_COLUMN_NAME = `Pathologie_respiratoire`;

const INPUT_ACTIVITE_SPORTIVE_COLUMN_NAME = `Pratiquez-vous une activité sportive au moins une fois par semaine ? On entend par activité sportive toute forme d'activité physique ayant pour objectif l'amélioration et le maintien de la condition physique.`
const OUTPUT_ACTIVITE_SPORTIVE_COLUMN_NAME = `Activité_sportive`

const INPUT_ACTIVITE_MAISON_COLUMN_NAME = `Pratiquez-vous au moins une fois par semaine les activités suivantes ?`
const OUTPUT_JARDINAGE_COLUMN_NAME = `Jardinage`
const OUTPUT_BRICOLAGE_COLUMN_NAME = `Bricolage`
const OUTPUT_MÉNAGE_COLUMN_NAME = `Ménage`

const INPUT_TRANSPORT_COLUMN_NAME = `Parmi les choix suivants, quel(s) moyen(s) de transport utilisez-vous principalement pour vos déplacements ?`
const OUTPUT_CYCLISTE_COLUMN_NAME = `Cycliste`
const OUTPUT_AUTOMOBILISTE_COLUMN_NAME = `Automobiliste`

const INPUT_FUMEUR_COLUMN_NAME = `Êtes-vous fumeur.euse ?`
const OUTPUT_FUMEUR_COLUMN_NAME = `Fumeur`

// Vivez-vous avec des enfants ?

const INPUT_PHONE_NUMBER_COLUMN_NAME = `Numéro de téléphone :`
const OUTPUT_PHONE_NUMBER_COLUMN_NAME = `Téléphone`

const OUTPUT_QUALITE_AIR_COLUMN_NAME = `QUALITE_AIR`
const OUTPUT_WEBSITE_COLUMN_NAME = `Lien_AASQA`

export const OUTPUT_RECOMMANDATION_COLUMN_NAME = `Recommandation`
export const OUTPUT_RECOMMANDATION_DETAILS_COLUMN_NAME = `Précisions`

export const INPUT_FREQUENCY_COLUMN_NAME = `A quelle fréquence souhaitez-vous recevoir les recommandations ? *`

// in the spreadsheet, casing is inconsistent
export const INPUT_FREQUENCY_EVERYDAY = `tous les jours`.toLowerCase()
export const INPUT_FREQUENCY_BAD_AIR_QUALITY = `Lorsque la qualité de l'air est mauvaise`.toLowerCase()





// Per  Arrêté du 22 juillet 2004 relatif aux indices de la qualité de l'air (article 6)
const QUALIFICATIF_TRES_BON = `Très bon`
const QUALIFICATIF_BON = `Bon`
const QUALIFICATIF_MOYEN = `Moyen`
const QUALIFICATIF_MÉDIOCRE = `Médiocre`
const QUALIFICATIF_MAUVAIS = `Mauvais`
const QUALIFICATIF_TRÈS_MAUVAIS = `Très mauvais`

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

const INDICE_ATMO_TO_EMAIL_QUALIFICATIF = Object.fromEntries(
    Object.entries(INDICE_ATMO_TO_QUALIFICATIF)
        .map(([indice, legalQualif]) => [indice, LEGAL_QUALIFICATIF_TO_EMAIL_QUALIFICATIF[legalQualif]])
)

export default function subscriberToReceipient(subscriber, airAPIResult){
    const receipient = Object.create(null);

    const {air = {}, website, region} = airAPIResult || {}
    //console.log('indiceATMODate', indiceATMODate, ville)
    const {indice} = air

    const qualif = INDICE_ATMO_TO_EMAIL_QUALIFICATIF[indice] || ''

    // if people only want recommandations only in case of bad air, list them only if indice is 8-10
    if(subscriber[INPUT_FREQUENCY_COLUMN_NAME] === INPUT_FREQUENCY_BAD_AIR_QUALITY && indice && parseInt(indice) < 8){
        return undefined
    }

    receipient[OUTPUT_EMAIL_COLUMN_NAME] = subscriber[INPUT_EMAIL_COLUMN_NAME].trim()
    receipient[OUTPUT_PHONE_NUMBER_COLUMN_NAME] = subscriber[INPUT_PHONE_NUMBER_COLUMN_NAME].trim()

    receipient[OUTPUT_REGION_COLUMN_NAME] = region
    receipient[OUTPUT_WEBSITE_COLUMN_NAME] = website;
    receipient[OUTPUT_VILLE_COLUMN_NAME] = subscriber[INPUT_VILLE_COLUMN_NAME].trim();
    receipient[OUTPUT_QUALITE_AIR_COLUMN_NAME] = qualif

    receipient[OUTPUT_PATHOLOGIE_RESPIRATOIRE_COLUMN_NAME] = subscriber[INPUT_PATHOLOGIE_RESPIRATOIRE_COLUMN_NAME].trim()
    receipient[OUTPUT_ALLERGIQUE_COLUMN_NAME] = subscriber[INPUT_ALLERGIQUE_COLUMN_NAME].trim().slice(0, 3)
    receipient[OUTPUT_ACTIVITE_SPORTIVE_COLUMN_NAME] = subscriber[INPUT_ACTIVITE_SPORTIVE_COLUMN_NAME].trim() === NON ? NON : OUI;
    receipient[OUTPUT_JARDINAGE_COLUMN_NAME] = subscriber[INPUT_ACTIVITE_MAISON_COLUMN_NAME].includes('Jardinage') ? OUI : NON;
    receipient[OUTPUT_BRICOLAGE_COLUMN_NAME] = subscriber[INPUT_ACTIVITE_MAISON_COLUMN_NAME].includes('Bricolage') ? OUI : NON;
    receipient[OUTPUT_MÉNAGE_COLUMN_NAME] = subscriber[INPUT_ACTIVITE_MAISON_COLUMN_NAME].includes('Ménage') ? OUI : NON;
    receipient[OUTPUT_CYCLISTE_COLUMN_NAME] = subscriber[INPUT_TRANSPORT_COLUMN_NAME].includes('Vélo') ? OUI : NON;
    receipient[OUTPUT_AUTOMOBILISTE_COLUMN_NAME] = subscriber[INPUT_TRANSPORT_COLUMN_NAME].includes('Voiture') ? OUI : NON;
    receipient[OUTPUT_FUMEUR_COLUMN_NAME] = subscriber[INPUT_FUMEUR_COLUMN_NAME].trim()


    return receipient;
}