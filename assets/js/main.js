
const INPUT_ALLERGIQUE_COLUMN_NAME = 'Êtes-vous allergique aux pollens (graminées, ambroisie, etc.) ?'
const OUTPUT_ALLERGIQUE_COLUMN_NAME = 'Allergique'

function makeSendingRow(row){
    const sendingRow = {...row};
    let allergique = row[INPUT_ALLERGIQUE_COLUMN_NAME].trim().slice(0, 3)

    delete sendingRow[INPUT_ALLERGIQUE_COLUMN_NAME]
    sendingRow[OUTPUT_ALLERGIQUE_COLUMN_NAME] = allergique

    return sendingRow
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
        const content = d3.csvParse(textContent)

        console.log('input file', file, content)

        const sendingContent = content.map(makeSendingRow)

        return d3.csvFormat(sendingContent)
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