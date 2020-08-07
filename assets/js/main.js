
const INPUT_ALLERGIQUE_COLUMN_NAME = 'Êtes-vous allergique aux pollens (graminées, ambroisie, etc.) ?'
const INPUT_VILLE_COLUMN_NAME = 'Ville'

const OUTPUT_ALLERGIQUE_COLUMN_NAME = 'Allergique'
const OUTPUT_QUALITE_AIR_COLUMN_NAME = `Qualité de l'air`

function makeSendingRow(row){
    const sendingRow = {...row};
    const TODAY_DATE_STRING = (new Date()).toISOString().slice(0, 10)

    const ville = sendingRow[INPUT_VILLE_COLUMN_NAME];
    return d3.json(`https://geo.api.gouv.fr/communes?nom=${ville}&boost=population&limit=1`)
    .then(geoResult => {
        const {code: codeINSEE} = geoResult[0];

        return d3.json(`https://app-6ccdcc10-da92-47b1-add6-59d8d3914d79.cleverapps.io/forecast?insee=${codeINSEE}`)
        .then(apiQAResult => {
            if(apiQAResult.length === 0)
                throw new Error('Pas trouvé !')

            return apiQAResult.find(res => res.date === TODAY_DATE_STRING)
        })
        .catch(err => {
            console.warn(`Pas d'information de qualité de l'air pour`, codeINSEE, ville, row, err)
        })
    })
    .catch(err => {
        console.warn('Code INSEE pour', ville, 'non trouvé', row, err)
    })
    .then(indiceATMODate => {
        //console.log('indiceATMODate', indiceATMODate, ville)

        const {qualif} = indiceATMODate || {}
        if(qualif)
            sendingRow[OUTPUT_QUALITE_AIR_COLUMN_NAME] = qualif

        let allergique = sendingRow[INPUT_ALLERGIQUE_COLUMN_NAME].trim().slice(0, 3)
        delete sendingRow[INPUT_ALLERGIQUE_COLUMN_NAME]
        sendingRow[OUTPUT_ALLERGIQUE_COLUMN_NAME] = allergique

        return sendingRow;
    })
}


function makeSendingCSV(file){
    
    return (new Promise( (resolve, reject) => {
        const reader = new FileReader();  
        reader.addEventListener("loadend", e => {
            resolve(reader.result);
        });
        reader.readAsText(file);
    }))
    .then(textContent => {
        const content = d3.csvParse(textContent)//.slice(0, 10)

        console.log('input file', file, content)

        return Promise.all(content.map(makeSendingRow))
        .then(sendingContent => d3.csvFormat(sendingContent))
    })
    
}

document.addEventListener('DOMContentLoaded', e => {
    const input = document.body.querySelector('.input input[type="file"]');
    const output = document.body.querySelector('.output');

    input.addEventListener('change', e => {
        // replace <input> with list of files
        const file = e.target.files[0];

        const sendingCSVTextP = makeSendingCSV(file)
        
        sendingCSVTextP.then(sendingCSVText => {
            console.log('output', sendingCSVText)

            const name = "fichier de sortie écosanté.csv"

            const blob = new Blob([sendingCSVText], {type: 'text/csv'});
            const blobUrl = URL.createObjectURL(blob);
            const outputFileLink = document.createElement('a');
            
            outputFileLink.setAttribute('href', blobUrl);
            outputFileLink.setAttribute('download', name);
            outputFileLink.textContent = name;

            output.append(outputFileLink)
        })
    })


}, {once: true})
