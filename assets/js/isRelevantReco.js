import {
    OUI, NON,
    OUTPUT_AUTOMOBILISTE_COLUMN_NAME
} from './subscriberReceipientConstants.js'

import {
    RECO_VOITURE_COLUMN,
    RECO_VOITURE_RELATED
} from './recommandationConstants.js'

export default function isRelevantReco(reciepient, reco){
    // Voiture
    if(reciepient[OUTPUT_AUTOMOBILISTE_COLUMN_NAME] === NON && reco[RECO_VOITURE_COLUMN] === RECO_VOITURE_RELATED){
        console.log('false', reciepient, reco)
        return false
    }

    return true;
}
