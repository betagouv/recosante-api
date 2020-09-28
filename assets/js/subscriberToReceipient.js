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
    
    INPUT_ACTIVITE_SPORTIVE_COLUMN_NAME,
    INPUT_APA_COLUMN_NAME,
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

import {INDICE_ATMO_TO_EMAIL_QUALIFICATIF} from './qualiteAirConstants.js';
import {slugify} from './utils.js';


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
    receipient[OUTPUT_ACTIVITE_SPORTIVE_COLUMN_NAME] = 
        subscriber[INPUT_ACTIVITE_SPORTIVE_COLUMN_NAME] === OUI || subscriber[INPUT_APA_COLUMN_NAME] === OUI ? 
            OUI : NON;
    receipient[OUTPUT_JARDINAGE_COLUMN_NAME] = slugify(subscriber[INPUT_ACTIVITE_MAISON_COLUMN_NAME]).toLowerCase().includes('jardinage') ? OUI : NON;
    receipient[OUTPUT_BRICOLAGE_COLUMN_NAME] = slugify(subscriber[INPUT_ACTIVITE_MAISON_COLUMN_NAME]).toLowerCase().includes('bricolage') ? OUI : NON;
    receipient[OUTPUT_MÉNAGE_COLUMN_NAME] = slugify(subscriber[INPUT_ACTIVITE_MAISON_COLUMN_NAME]).toLowerCase().includes('menage') ? OUI : NON;
    receipient[OUTPUT_CYCLISTE_COLUMN_NAME] = slugify(subscriber[INPUT_TRANSPORT_COLUMN_NAME]).toLowerCase().includes('velo') ? OUI : NON;
    receipient[OUTPUT_AUTOMOBILISTE_COLUMN_NAME] = slugify(subscriber[INPUT_TRANSPORT_COLUMN_NAME]).toLowerCase().includes('voiture') ? OUI : NON;
    receipient[OUTPUT_FUMEUR_COLUMN_NAME] = subscriber[INPUT_FUMEUR_COLUMN_NAME].trim()

    return receipient;
}