import {
    OUI, NON,

    INPUT_ALLERGIQUE_COLUMN_NAME,
    OUTPUT_ALLERGIQUE_COLUMN_NAME,

    INPUT_EMAIL_COLUMN_NAME,
    OUTPUT_EMAIL_COLUMN_NAME,
    
    INPUT_VILLE_COLUMN_NAME,
    OUTPUT_VILLE_COLUMN_NAME,
    
    INPUT_PATHOLOGIE_RESPIRATOIRE_COLUMN_NAME,
    OUTPUT_PATHOLOGIE_RESPIRATOIRE_COLUMN_NAME,
    
    INPUT_ACTIVITE_SPORTIVE_COLUMN_NAME ,
    OUTPUT_ACTIVITE_SPORTIVE_COLUMN_NAME,
    
    INPUT_ACTIVITE_MAISON_COLUMN_NAME,
    OUTPUT_JARDINAGE_COLUMN_NAME,
    OUTPUT_BRICOLAGE_COLUMN_NAME,
    OUTPUT_MÉNAGE_COLUMN_NAME,
    
    INPUT_TRANSPORT_COLUMN_NAME,
    OUTPUT_CYCLISTE_COLUMN_NAME,
    OUTPUT_AUTOMOBILISTE_COLUMN_NAME,
    
    INPUT_FUMEUR_COLUMN_NAME,
    OUTPUT_FUMEUR_COLUMN_NAME,
    
    INPUT_PHONE_NUMBER_COLUMN_NAME,
    OUTPUT_PHONE_NUMBER_COLUMN_NAME,
    
    OUTPUT_QUALITE_AIR_COLUMN_NAME,
    OUTPUT_WEBSITE_COLUMN_NAME,
    OUTPUT_REGION_COLUMN_NAME,
    INPUT_FREQUENCY_COLUMN_NAME,
    INPUT_FREQUENCY_BAD_AIR_QUALITY,
} from './subscriberReceipientConstants.js'


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