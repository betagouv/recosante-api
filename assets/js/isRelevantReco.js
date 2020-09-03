import {
    OUI, NON,
    OUTPUT_AUTOMOBILISTE_COLUMN_NAME,
    OUTPUT_QUALITE_AIR_COLUMN_NAME,
    OUTPUT_ACTIVITE_SPORTIVE_COLUMN_NAME
} from './subscriberReceipientConstants.js'

import {
    RECO_VOITURE_COLUMN,
    RECO_VOITURE_RELATED,
    RECO_QA_MAUVAISE_COLUMN,
    RECO_QA_MAUVAISE_RELATED,
    RECO_ACTIVITE_PHYIQUE_COLUMN,
    RECO_ACTIVITE_PHYIQUE_RELATED
} from './recommandationConstants.js'

import {
    EMAIL_QUALIFICATIF_TO_LEGAL_QUALIFICATIF, 
    QUALIFICATIF_TRES_BON,
    QUALIFICATIF_BON,
    QUALIFICATIF_MOYEN,
    QUALIFICATIF_MÉDIOCRE
} from './qualiteAirConstants.js';

export default function isRelevantReco(reciepient, reco){
    // Voiture
    if(reciepient[OUTPUT_AUTOMOBILISTE_COLUMN_NAME] === NON && reco[RECO_VOITURE_COLUMN] === RECO_VOITURE_RELATED){
        console.log('false, voiture', reciepient, reco)
        return false
    }

    // Quand qualité de l'air mauvaise
    const airQualityIsNotBad = [QUALIFICATIF_TRES_BON, QUALIFICATIF_BON, QUALIFICATIF_MOYEN, QUALIFICATIF_MÉDIOCRE].includes(
        EMAIL_QUALIFICATIF_TO_LEGAL_QUALIFICATIF[reciepient[OUTPUT_QUALITE_AIR_COLUMN_NAME]]
    )
    if(airQualityIsNotBad && reco[RECO_QA_MAUVAISE_COLUMN] === RECO_QA_MAUVAISE_RELATED){
        console.log('false, qualité air mauvaise', reciepient, reco)
        return false
    }

    // activite physique
    if(reciepient[OUTPUT_ACTIVITE_SPORTIVE_COLUMN_NAME] === NON && reco[RECO_ACTIVITE_PHYIQUE_COLUMN] === RECO_ACTIVITE_PHYIQUE_RELATED){
        console.log('false, activité physique', reciepient, reco)
        return false;
    }

    return true;
}
